"""Tests for ai_loopback_visual_binary trace_run receipt emission."""

import pytest
import json
import tempfile
from pathlib import Path
from ai_loopback_visual_binary.tools.trace_run import (
    TraceRunInputs,
    trace_run,
    emit_core_receipt_v1,
)


class TestTraceRunInputs:
    """Tests for TraceRunInputs dataclass."""
    
    def test_default_initialization(self):
        """Test TraceRunInputs with minimal required fields."""
        inputs = TraceRunInputs(run_id="run-000001")
        assert inputs.run_id == "run-000001"
        assert inputs.producer == "ai_loopback_visual_binary"
        assert inputs.receipt_dir is None
        assert inputs.artifacts is None
    
    def test_custom_initialization(self):
        """Test TraceRunInputs with custom values."""
        custom_dir = Path("/tmp/receipts")
        custom_artifacts = {"file1": "hash1"}
        
        inputs = TraceRunInputs(
            run_id="run-000002",
            producer="custom_producer",
            receipt_dir=custom_dir,
            artifacts=custom_artifacts,
        )
        
        assert inputs.run_id == "run-000002"
        assert inputs.producer == "custom_producer"
        assert inputs.receipt_dir == custom_dir
        assert inputs.artifacts == custom_artifacts
    
    def test_artifacts_not_shared(self):
        """Test that artifacts default is not a shared mutable object."""
        inputs1 = TraceRunInputs(run_id="run-001")
        inputs2 = TraceRunInputs(run_id="run-002")
        
        # Both should have None, not a shared dict
        assert inputs1.artifacts is None
        assert inputs2.artifacts is None


class TestEmitCoreReceiptV1:
    """Tests for emit_core_receipt_v1 function."""
    
    def test_emit_creates_directory(self):
        """Test that emit_core_receipt_v1 creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_path = Path(tmpdir) / "nested" / "dir" / "receipt.json"
            
            emit_core_receipt_v1(
                receipt_path=receipt_path,
                receipt_id="TEST-001",
                run_id="run-001",
                producer="test_producer",
                verify_pass=True,
                checks={"test_check": {"status": "pass"}},
            )
            
            assert receipt_path.exists()
            assert receipt_path.is_file()
    
    def test_emit_writes_valid_json(self):
        """Test that emit_core_receipt_v1 writes valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_path = Path(tmpdir) / "receipt.json"
            
            emit_core_receipt_v1(
                receipt_path=receipt_path,
                receipt_id="TEST-001",
                run_id="run-001",
                producer="test_producer",
                verify_pass=True,
                checks={"test_check": {"status": "pass"}},
            )
            
            with open(receipt_path) as f:
                data = json.load(f)
            
            assert isinstance(data, dict)
            assert "schema" in data
            assert "receipt" in data
            assert "verify" in data
            assert "checks" in data
            assert "artifacts" in data
    
    def test_emit_with_artifacts(self):
        """Test that emit_core_receipt_v1 includes artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_path = Path(tmpdir) / "receipt.json"
            artifacts = {"file1.txt": "sha256:abc123"}
            
            emit_core_receipt_v1(
                receipt_path=receipt_path,
                receipt_id="TEST-001",
                run_id="run-001",
                producer="test_producer",
                verify_pass=True,
                checks={"test_check": {"status": "pass"}},
                artifacts=artifacts,
            )
            
            with open(receipt_path) as f:
                data = json.load(f)
            
            assert data["artifacts"] == artifacts


class TestTraceRun:
    """Tests for trace_run function."""
    
    def test_trace_run_with_temp_directory(self):
        """Test that trace_run produces receipt files in the correct location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_dir = Path(tmpdir)
            inputs = TraceRunInputs(
                run_id="run-000001",
                receipt_dir=receipt_dir,
            )
            
            result_path = trace_run(inputs)
            
            assert result_path.exists()
            assert result_path.is_file()
            assert result_path.name == "run-000001.receipt.json"
            assert result_path.parent == receipt_dir
    
    def test_trace_run_generates_valid_core_receipt_v1(self):
        """Test that trace_run generates a valid Core Receipt v1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_dir = Path(tmpdir)
            inputs = TraceRunInputs(
                run_id="run-000002",
                receipt_dir=receipt_dir,
            )
            
            result_path = trace_run(inputs)
            
            with open(result_path) as f:
                data = json.load(f)
            
            # Validate schema structure
            assert data["schema"] == "v1.0"
            
            # Validate receipt section
            assert "receipt" in data
            assert "receipt_id" in data["receipt"]
            assert "created_utc" in data["receipt"]
            assert "producer" in data["receipt"]
            assert "run_id" in data["receipt"]
            assert data["receipt"]["run_id"] == "run-000002"
            assert data["receipt"]["producer"] == "ai_loopback_visual_binary"
            
            # Validate verify section
            assert "verify" in data
            assert "pass" in data["verify"]
            assert isinstance(data["verify"]["pass"], bool)
            
            # Validate checks section
            assert "checks" in data
            assert isinstance(data["checks"], dict)
            
            # Validate artifacts section
            assert "artifacts" in data
            assert isinstance(data["artifacts"], dict)
    
    def test_trace_run_includes_required_checks(self):
        """Test that trace_run includes CRC16_CCITT_FALSE and BER_THRESHOLD checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_dir = Path(tmpdir)
            inputs = TraceRunInputs(
                run_id="run-000003",
                receipt_dir=receipt_dir,
            )
            
            result_path = trace_run(inputs)
            
            with open(result_path) as f:
                data = json.load(f)
            
            checks = data["checks"]
            
            # Verify CRC16_CCITT_FALSE check
            assert "CRC16_CCITT_FALSE" in checks
            assert "status" in checks["CRC16_CCITT_FALSE"]
            assert checks["CRC16_CCITT_FALSE"]["status"] == "pass"
            
            # Verify BER_THRESHOLD check
            assert "BER_THRESHOLD" in checks
            assert "status" in checks["BER_THRESHOLD"]
            assert checks["BER_THRESHOLD"]["status"] == "pass"
            assert "threshold" in checks["BER_THRESHOLD"]
            assert "actual" in checks["BER_THRESHOLD"]
    
    def test_trace_run_verify_pass_field(self):
        """Test that trace_run generates verify.pass field correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_dir = Path(tmpdir)
            inputs = TraceRunInputs(
                run_id="run-000004",
                receipt_dir=receipt_dir,
            )
            
            result_path = trace_run(inputs)
            
            with open(result_path) as f:
                data = json.load(f)
            
            # All checks pass, so verify.pass should be True
            assert data["verify"]["pass"] is True
    
    def test_trace_run_with_artifacts(self):
        """Test that trace_run includes artifacts when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_dir = Path(tmpdir)
            artifacts = {
                "image1.jpg": "sha256:deadbeef",
                "video1.mp4": "sha256:cafebabe",
            }
            inputs = TraceRunInputs(
                run_id="run-000005",
                receipt_dir=receipt_dir,
                artifacts=artifacts,
            )
            
            result_path = trace_run(inputs)
            
            with open(result_path) as f:
                data = json.load(f)
            
            assert data["artifacts"] == artifacts
    
    def test_trace_run_default_inputs(self):
        """Test that trace_run works with default inputs (None)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # We can't easily test the default path, so we'll create a custom one
            # This test verifies the function handles None gracefully
            result_path = trace_run()
            
            # Should create receipt in default location
            assert result_path.exists()
            assert result_path.is_file()
            assert result_path.name == "run-000001.receipt.json"
    
    def test_trace_run_receipt_id_format(self):
        """Test that trace_run generates receipt_id in correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_dir = Path(tmpdir)
            inputs = TraceRunInputs(
                run_id="run-000123",
                receipt_dir=receipt_dir,
            )
            
            result_path = trace_run(inputs)
            
            with open(result_path) as f:
                data = json.load(f)
            
            # Receipt ID should be formatted as PRODUCER-RUNID
            assert data["receipt"]["receipt_id"] == "AI-LOOPBACK-VISUAL-BINARY-000123"


class TestIntegration:
    """Integration tests for trace_run workflow."""
    
    def test_full_workflow(self):
        """Test complete trace_run workflow from inputs to receipt validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_dir = Path(tmpdir)
            
            # Create inputs
            inputs = TraceRunInputs(
                run_id="run-integration-001",
                producer="ai_loopback_visual_binary",
                receipt_dir=receipt_dir,
                artifacts={"test.dat": "sha256:test123"},
            )
            
            # Execute trace_run
            result_path = trace_run(inputs)
            
            # Verify file exists
            assert result_path.exists()
            
            # Load and validate receipt
            with open(result_path) as f:
                data = json.load(f)
            
            # Comprehensive validation
            assert data["schema"] == "v1.0"
            assert data["receipt"]["run_id"] == "run-integration-001"
            assert data["receipt"]["producer"] == "ai_loopback_visual_binary"
            assert data["verify"]["pass"] is True
            assert "CRC16_CCITT_FALSE" in data["checks"]
            assert "BER_THRESHOLD" in data["checks"]
            assert data["artifacts"] == {"test.dat": "sha256:test123"}
