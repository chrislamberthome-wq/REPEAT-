"""Policy engine for classifying structural diffs by path using glob patterns."""

import json
import fnmatch
from typing import Dict, List, Tuple, Any
from enum import Enum


class Classification(Enum):
    """Policy classification levels with precedence order."""
    DENY = 3
    WARN = 2
    ALLOW = 1
    UNMATCHED = 0


class PolicyEngine:
    """Glob-based classifier and evaluator for structural diffs."""
    
    def __init__(self, policy_data: Dict[str, Any]):
        """
        Initialize the policy engine.
        
        Args:
            policy_data: Dictionary containing policy rules with keys:
                - deny: List of glob patterns for DENY classification
                - warn: List of glob patterns for WARN classification
                - allow: List of glob patterns for ALLOW classification
        """
        self.deny_patterns = policy_data.get('deny', [])
        self.warn_patterns = policy_data.get('warn', [])
        self.allow_patterns = policy_data.get('allow', [])
    
    @classmethod
    def from_file(cls, policy_path: str) -> 'PolicyEngine':
        """
        Load policy from a JSON file.
        
        Args:
            policy_path: Path to the policy JSON file
            
        Returns:
            PolicyEngine instance
        """
        with open(policy_path, 'r') as f:
            policy_data = json.load(f)
        return cls(policy_data)
    
    def classify_path(self, path: str) -> Classification:
        """
        Classify a path according to policy rules.
        
        Precedence order: DENY > WARN > ALLOW > UNMATCHED
        
        Args:
            path: The path to classify
            
        Returns:
            Classification enum value
        """
        # Check DENY patterns first (highest precedence)
        for pattern in self.deny_patterns:
            if fnmatch.fnmatch(path, pattern):
                return Classification.DENY
        
        # Check WARN patterns
        for pattern in self.warn_patterns:
            if fnmatch.fnmatch(path, pattern):
                return Classification.WARN
        
        # Check ALLOW patterns
        for pattern in self.allow_patterns:
            if fnmatch.fnmatch(path, pattern):
                return Classification.ALLOW
        
        # Default to UNMATCHED
        return Classification.UNMATCHED
    
    def evaluate(self, paths: List[str]) -> Dict[str, Any]:
        """
        Evaluate a list of paths and generate a classification report.
        
        Args:
            paths: List of paths to evaluate
            
        Returns:
            Dictionary containing:
                - classifications: Dict mapping paths to Classification
                - summary: Dict with counts per classification
                - has_deny_violations: Boolean indicating if any DENY violations exist
        """
        classifications = {}
        summary = {
            'deny': 0,
            'warn': 0,
            'allow': 0,
            'unmatched': 0
        }
        
        for path in paths:
            classification = self.classify_path(path)
            classifications[path] = classification
            
            if classification == Classification.DENY:
                summary['deny'] += 1
            elif classification == Classification.WARN:
                summary['warn'] += 1
            elif classification == Classification.ALLOW:
                summary['allow'] += 1
            else:
                summary['unmatched'] += 1
        
        has_deny_violations = summary['deny'] > 0
        
        return {
            'classifications': classifications,
            'summary': summary,
            'has_deny_violations': has_deny_violations
        }
    
    def format_report(self, evaluation: Dict[str, Any], grouped: bool = True) -> str:
        """
        Format evaluation results as a human-readable report.
        
        Args:
            evaluation: Result from evaluate()
            grouped: If True, group by classification; if False, show per-path
            
        Returns:
            Formatted report string
        """
        lines = []
        
        # Summary header
        lines.append("=== Policy Evaluation Summary ===")
        summary = evaluation['summary']
        lines.append(f"DENY:      {summary['deny']}")
        lines.append(f"WARN:      {summary['warn']}")
        lines.append(f"ALLOW:     {summary['allow']}")
        lines.append(f"UNMATCHED: {summary['unmatched']}")
        lines.append("")
        
        classifications = evaluation['classifications']
        
        if grouped:
            # Group by classification
            lines.append("=== Paths by Classification ===")
            
            for class_type in [Classification.DENY, Classification.WARN, 
                              Classification.ALLOW, Classification.UNMATCHED]:
                paths = [p for p, c in classifications.items() if c == class_type]
                if paths:
                    lines.append(f"\n{class_type.name}:")
                    for path in sorted(paths):
                        lines.append(f"  - {path}")
        else:
            # Show per-path
            lines.append("=== Per-Path Classification ===")
            for path in sorted(classifications.keys()):
                classification = classifications[path]
                lines.append(f"{classification.name:10} {path}")
        
        return "\n".join(lines)
