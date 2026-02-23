#!/usr/bin/env python3
"""
Golden Vector Tests for MRAM Drift Detection

These tests validate:
1. All runs pass in stable mode
2. Deterministic failure when drift tolerance exceeded
3. Receipt hashes are stable across repeated runs
4. Packet hashes remain invariant
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import pytest


class TestMRAMDriftDetection:
    """Test suite for MRAM drift detection with REPEAT verification."""
    
    # Golden hash constants
    EXPECTED_PACKET_HASH = "sha256:e79de2a174f42f074d36fc450a8389fe16d804996535d2a462f4c815ba4b3353"
    EXPECTED_RUN_23_RECEIPT_HASH = "sha256:24957fd9ea82a4197f8afac0fe11c0002453b2f6942129f1d683c08fa452c127"
    
    def run_simulation(self, mode: str, seed: int) -> tuple[str, str]:
        """
        Run the simulation and return (output_text, receipt_file_path).
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            output_file = f.name
        
        try:
            result = subprocess.run(
                [
                    'python3',
                    'simulate_mram_runs.py',
                    '--mode', mode,
                    '--seed', str(seed),
                    '--output', output_file
                ],
                capture_output=True,
                text=True,
                check=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            return result.stdout, output_file
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Simulation failed: {e.stderr}")
    
    def load_receipts(self, receipt_file: str) -> list[dict]:
        """Load receipts from JSONL file."""
        receipts = []
        with open(receipt_file, 'r') as f:
            for line in f:
                receipts.append(json.loads(line))
        return receipts
    
    def test_stable_mode_all_pass(self):
        """Test that all runs pass in stable mode (no drift)."""
        output, receipt_file = self.run_simulation('pass', seed=42)
        
        try:
            # Verify output contains expected pass count
            assert 'PASS: 100' in output
            assert 'FAIL: 0' in output
            
            # Load and verify receipts
            receipts = self.load_receipts(receipt_file)
            assert len(receipts) == 100
            
            # All receipts should pass
            for receipt in receipts:
                assert receipt['verdict']['pass'] is True
                assert 'fail_reason' not in receipt['verdict']
        finally:
            os.unlink(receipt_file)
    
    def test_drift_fail_mode_detects_drift(self):
        """Test that drift mode deterministically fails due to drift tolerance."""
        output, receipt_file = self.run_simulation('drift_fail', seed=42)
        
        try:
            # Verify output shows failures
            assert 'FAIL:' in output
            assert int(output.split('FAIL: ')[1].split('\n')[0]) > 0
            
            # Verify first failure is reported
            assert 'First failure: run_id=23' in output
            assert 'reason=drift_detected' in output
            
            # Load and verify receipts
            receipts = self.load_receipts(receipt_file)
            assert len(receipts) == 100
            
            # Find first failure
            first_failure_idx = None
            for i, receipt in enumerate(receipts):
                if not receipt['verdict']['pass']:
                    first_failure_idx = i
                    break
            
            assert first_failure_idx is not None, "Should have at least one failure"
            
            # Verify first failure is at run 23
            assert receipts[first_failure_idx]['run_id'] == 23
            assert receipts[first_failure_idx]['verdict']['fail_reason'] == 'drift_detected'
            
            # Verify drift percentage exceeded tolerance
            assert receipts[first_failure_idx]['metrics']['drift_pct'] > 5.0
            
            # Verify threshold was NOT exceeded (this is the key difference)
            # Resistance should be below 1250 ohms (the threshold)
            assert receipts[first_failure_idx]['measured_resistance_ohms'] < 1250.0
        finally:
            os.unlink(receipt_file)
    
    def test_receipt_hashes_deterministic(self):
        """Test that receipt hashes are stable across repeated runs with same seed."""
        # Run simulation twice with same seed
        output1, file1 = self.run_simulation('drift_fail', seed=123)
        output2, file2 = self.run_simulation('drift_fail', seed=123)
        
        try:
            receipts1 = self.load_receipts(file1)
            receipts2 = self.load_receipts(file2)
            
            assert len(receipts1) == len(receipts2)
            
            # Compare each receipt
            for i, (r1, r2) in enumerate(zip(receipts1, receipts2)):
                assert r1 == r2, f"Receipt {i+1} differs between runs"
                
                # Specifically check hash fields
                assert r1['packet_hash_sha256'] == r2['packet_hash_sha256']
                assert r1['evidence_hash_sha256'] == r2['evidence_hash_sha256']
                assert r1['receipt_hash_sha256'] == r2['receipt_hash_sha256']
        finally:
            os.unlink(file1)
            os.unlink(file2)
    
    def test_packet_hash_invariant(self):
        """Test that packet hash remains constant across different modes."""
        # Run in both modes
        output_pass, file_pass = self.run_simulation('pass', seed=42)
        output_drift, file_drift = self.run_simulation('drift_fail', seed=42)
        
        try:
            receipts_pass = self.load_receipts(file_pass)
            receipts_drift = self.load_receipts(file_drift)
            
            # Extract packet hashes
            packet_hash_pass = receipts_pass[0]['packet_hash_sha256']
            packet_hash_drift = receipts_drift[0]['packet_hash_sha256']
            
            # Packet hash should be identical (same configuration)
            assert packet_hash_pass == packet_hash_drift
            
            # Verify against expected golden hash
            assert packet_hash_pass == self.EXPECTED_PACKET_HASH
        finally:
            os.unlink(file_pass)
            os.unlink(file_drift)
    
    def test_receipt_schema_compliance(self):
        """Test that receipts comply with the schema structure."""
        output, receipt_file = self.run_simulation('drift_fail', seed=42)
        
        try:
            receipts = self.load_receipts(receipt_file)
            
            # Check first receipt (passing)
            passing_receipt = receipts[0]
            assert passing_receipt['schema'] == 'repeat-spintronics-receipt-v1'
            assert 'packet_hash_sha256' in passing_receipt
            assert 'evidence_hash_sha256' in passing_receipt
            assert 'receipt_hash_sha256' in passing_receipt
            assert 'run_id' in passing_receipt
            assert 'measured_resistance_ohms' in passing_receipt
            assert 'verdict' in passing_receipt
            assert 'pass' in passing_receipt['verdict']
            assert 'metrics' in passing_receipt
            assert 'mean_resistance_ohms' in passing_receipt['metrics']
            assert 'drift_pct' in passing_receipt['metrics']
            
            # Check failing receipt (should have fail_reason)
            failing_receipt = receipts[22]  # run_id=23, index=22
            assert failing_receipt['verdict']['pass'] is False
            assert 'fail_reason' in failing_receipt['verdict']
            assert failing_receipt['verdict']['fail_reason'] == 'drift_detected'
        finally:
            os.unlink(receipt_file)
    
    def test_drift_progression(self):
        """Test that drift increases progressively in drift_fail mode."""
        output, receipt_file = self.run_simulation('drift_fail', seed=42)
        
        try:
            receipts = self.load_receipts(receipt_file)
            
            # After baseline window (run 10), drift should generally increase
            # (with some noise)
            drift_values = []
            for receipt in receipts[10:]:  # Skip baseline window
                drift_values.append(receipt['metrics']['drift_pct'])
            
            # Check that drift generally trends upward
            # By end of run, drift should be significantly higher than at start
            early_drift_avg = sum(drift_values[:10]) / 10
            late_drift_avg = sum(drift_values[-10:]) / 10
            
            assert late_drift_avg > early_drift_avg, \
                f"Drift should increase over time: early={early_drift_avg:.2f}%, late={late_drift_avg:.2f}%"
            
            # Verify final drift is substantial (showing clear drift)
            assert late_drift_avg > 15.0, \
                f"Final drift should be >15%: got {late_drift_avg:.2f}%"
        finally:
            os.unlink(receipt_file)
    
    def test_golden_hash_run_23(self):
        """Test golden hash value for the critical run 23 (first failure)."""
        output, receipt_file = self.run_simulation('drift_fail', seed=42)
        
        try:
            receipts = self.load_receipts(receipt_file)
            run_23_receipt = receipts[22]  # run_id=23, index=22
            
            # Verify this is run 23 and it fails
            assert run_23_receipt['run_id'] == 23
            assert run_23_receipt['verdict']['pass'] is False
            
            # Golden hash for run 23 with seed 42
            assert run_23_receipt['receipt_hash_sha256'] == self.EXPECTED_RUN_23_RECEIPT_HASH, \
                "Golden hash mismatch - indicates non-deterministic behavior or schema change"
        finally:
            os.unlink(receipt_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
