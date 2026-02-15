"""Command-line interface for REPEAT-AI diff and policy evaluation."""

import argparse
import json
import sys
from typing import Dict, Any, List

from repeat_ai.policy import PolicyEngine


def load_json_file(filepath: str) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary containing the parsed JSON data
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_paths_from_diff(baseline: Dict[str, Any], current: Dict[str, Any]) -> List[str]:
    """
    Extract paths that differ between baseline and current.
    
    This is a simple implementation that compares keys at the top level.
    For a real implementation, this would do deep comparison and track
    all changed paths.
    
    Args:
        baseline: Baseline data structure
        current: Current data structure
        
    Returns:
        List of paths that have changed
    """
    changed_paths = []
    
    # Get all unique keys from both dictionaries
    all_keys = set(baseline.keys()) | set(current.keys())
    
    for key in all_keys:
        baseline_val = baseline.get(key)
        current_val = current.get(key)
        
        if baseline_val != current_val:
            changed_paths.append(key)
    
    return changed_paths


def cmd_diff(args):
    """Handle the diff command."""
    # Load baseline and current files
    try:
        baseline = load_json_file(args.baseline)
        current = load_json_file(args.current)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        return 1
    
    # Extract changed paths
    changed_paths = extract_paths_from_diff(baseline, current)
    
    # Check if there are any changes
    if not changed_paths:
        print("No differences found.")
        return 0
    
    # If --fail-on-change is set, exit with code 2 regardless of policy
    if args.fail_on_change:
        print(f"Changes detected ({len(changed_paths)} paths changed).", file=sys.stderr)
        print("Exiting with code 2 due to --fail-on-change flag.", file=sys.stderr)
        return 2
    
    # If policy is specified, evaluate paths against policy
    if args.policy:
        try:
            policy_engine = PolicyEngine.from_file(args.policy)
        except FileNotFoundError:
            print(f"Error: Policy file not found - {args.policy}", file=sys.stderr)
            return 1
        except json.JSONDecodeError as e:
            print(f"Error: Invalid policy JSON - {e}", file=sys.stderr)
            return 1
        
        # Evaluate paths
        evaluation = policy_engine.evaluate(changed_paths)
        
        # Generate and print report
        grouped = args.policy_report == 'grouped'
        report = policy_engine.format_report(evaluation, grouped=grouped)
        print(report)
        
        # Exit with appropriate code
        if evaluation['has_deny_violations']:
            print("\nPolicy violations detected. Exiting with code 3.", file=sys.stderr)
            return 3
        else:
            return 0
    else:
        # No policy specified, just print the changed paths
        print(f"Differences found in {len(changed_paths)} paths:")
        for path in sorted(changed_paths):
            print(f"  - {path}")
        return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='repeat_ai',
        description='REPEAT-AI: Policy engine for structural diff classification'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Diff command
    diff_parser = subparsers.add_parser(
        'diff',
        help='Compare two JSON files and evaluate against policy'
    )
    diff_parser.add_argument(
        'baseline',
        help='Path to baseline JSON file'
    )
    diff_parser.add_argument(
        'current',
        help='Path to current JSON file'
    )
    diff_parser.add_argument(
        '--policy',
        help='Path to policy JSON file for classification'
    )
    diff_parser.add_argument(
        '--policy-report',
        choices=['grouped', 'per-path'],
        default='grouped',
        help='Report format: grouped (default) or per-path'
    )
    diff_parser.add_argument(
        '--fail-on-change',
        action='store_true',
        help='Exit with code 2 if any changes are detected, regardless of policy'
    )
    diff_parser.set_defaults(func=cmd_diff)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
