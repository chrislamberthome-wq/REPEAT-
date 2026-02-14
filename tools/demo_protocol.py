#!/usr/bin/env python3
"""
demo_protocol.py - AI Loopback Visual Binary Classification Demo

This is a minimal example protocol that demonstrates the REPEAT framework.
It simulates an AI-based binary classification test where the system
classifies simple visual patterns and logs the entire process as a trace.

Protocol: AI Loopback Visual Binary v1
Purpose: Demonstrate tracing, receipt generation, and verification
"""

import json
import hashlib
import sys
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List


class DemoProtocol:
    """Minimal AI loopback visual binary classification protocol."""
    
    PROTOCOL_ID = "ai_loopback_visual_binary/v1"
    PROTOCOL_VERSION = "1.0.0"
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.trace: List[Dict[str, Any]] = []
        
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log an event to the trace."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "run_id": self.run_id,
            "data": data
        }
        self.trace.append(event)
        
    def simulate_visual_pattern(self, pattern_id: int) -> Dict[str, Any]:
        """Simulate generating a visual pattern."""
        # Simple binary patterns: even = squares, odd = circles
        pattern_type = "square" if pattern_id % 2 == 0 else "circle"
        pattern = {
            "pattern_id": pattern_id,
            "type": pattern_type,
            "features": {
                "size": 10 + pattern_id,
                "color": "blue" if pattern_id % 2 == 0 else "red"
            }
        }
        return pattern
    
    def classify_pattern(self, pattern: Dict[str, Any]) -> str:
        """Simulate AI classification of a pattern."""
        # Simple deterministic classification
        if pattern["type"] == "square":
            return "CLASS_A"
        else:
            return "CLASS_B"
    
    def run(self, num_samples: int = 5) -> Dict[str, Any]:
        """Run the protocol with specified number of samples."""
        # Log protocol start
        self.log_event("protocol_start", {
            "protocol_id": self.PROTOCOL_ID,
            "protocol_version": self.PROTOCOL_VERSION,
            "num_samples": num_samples
        })
        
        results = []
        
        # Process each sample
        for i in range(num_samples):
            # Generate pattern
            pattern = self.simulate_visual_pattern(i)
            self.log_event("pattern_generated", {
                "sample_index": i,
                "pattern": pattern
            })
            
            # Classify pattern
            classification = self.classify_pattern(pattern)
            self.log_event("pattern_classified", {
                "sample_index": i,
                "pattern_id": pattern["pattern_id"],
                "classification": classification
            })
            
            # Check loopback (verify classification matches expected)
            expected = "CLASS_A" if pattern["type"] == "square" else "CLASS_B"
            match = classification == expected
            
            self.log_event("loopback_check", {
                "sample_index": i,
                "expected": expected,
                "actual": classification,
                "match": match
            })
            
            results.append({
                "sample_index": i,
                "pattern_id": pattern["pattern_id"],
                "classification": classification,
                "loopback_match": match
            })
        
        # Compute summary
        total_samples = len(results)
        successful_loopbacks = sum(1 for r in results if r["loopback_match"])
        success_rate = successful_loopbacks / total_samples if total_samples > 0 else 0
        
        verdict = "PASS" if success_rate == 1.0 else "FAIL"
        
        summary = {
            "total_samples": total_samples,
            "successful_loopbacks": successful_loopbacks,
            "success_rate": success_rate,
            "verdict": verdict
        }
        
        self.log_event("protocol_complete", {
            "summary": summary,
            "results": results
        })
        
        return summary
    
    def write_trace(self, output_path: str) -> None:
        """Write trace to JSONL file."""
        with open(output_path, 'w') as f:
            for event in self.trace:
                f.write(json.dumps(event) + '\n')
        print(f"Trace written to: {output_path}")
        
    def get_inputs_hash(self) -> str:
        """Compute hash of inputs."""
        # For this demo, inputs are the protocol params
        inputs = {
            "protocol_id": self.PROTOCOL_ID,
            "run_id": self.run_id
        }
        canonical = json.dumps(inputs, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def get_outputs_hash(self) -> str:
        """Compute hash of outputs."""
        # Find the protocol_complete event
        for event in reversed(self.trace):
            if event["event_type"] == "protocol_complete":
                outputs = event["data"]["summary"]
                canonical = json.dumps(outputs, sort_keys=True)
                return hashlib.sha256(canonical.encode()).hexdigest()
        return ""


def main():
    parser = argparse.ArgumentParser(
        description="Run the AI Loopback Visual Binary demo protocol"
    )
    parser.add_argument(
        "--output",
        default="audit/examples/demo.trace.jsonl",
        help="Output path for trace file (default: audit/examples/demo.trace.jsonl)"
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run ID (default: auto-generated)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=5,
        help="Number of samples to process (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Generate run ID if not provided
    if args.run_id is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        args.run_id = f"run_{timestamp}"
    
    # Create output directory if needed
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"=== REPEAT Demo Protocol ===")
    print(f"Protocol: ai_loopback_visual_binary/v1")
    print(f"Run ID: {args.run_id}")
    print(f"Samples: {args.samples}")
    print()
    
    # Run protocol
    protocol = DemoProtocol(args.run_id)
    summary = protocol.run(num_samples=args.samples)
    
    # Write trace
    protocol.write_trace(args.output)
    
    # Print summary
    print()
    print(f"=== Summary ===")
    print(f"Total samples: {summary['total_samples']}")
    print(f"Successful loopbacks: {summary['successful_loopbacks']}")
    print(f"Success rate: {summary['success_rate']:.1%}")
    print(f"Verdict: {summary['verdict']}")
    print()
    print(f"Next steps:")
    print(f"  1. Emit receipt: python tools/emit_receipt.py {args.output}")
    print(f"  2. Verify receipt: python tools/verify_receipt.py {args.output.replace('.trace.jsonl', '.receipt.json')}")
    
    # Exit with appropriate code
    sys.exit(0 if summary['verdict'] == 'PASS' else 1)


if __name__ == "__main__":
    main()
