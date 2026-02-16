"""Tests for Engage receipt format validation with forward compatibility.

This module tests receipt validation in a way that's compatible with:
- Current Engage receipt format (repeat-engage-v1.receipt)
- Future Core Receipt v1 integration (repeat-core-v1.receipt)
- Other potential future schema versions

The tests validate essential receipt structure and fields without requiring
a specific schema_id, ensuring forward compatibility.
"""

import json
import os
import pytest
from pathlib import Path


# Path to golden receipt test vectors
VECTORS_PATH = Path(__file__).parent / "vectors" / "engage_golden_receipts.json"


def load_golden_receipts():
    """Load golden receipt test vectors from JSON file."""
    with open(VECTORS_PATH, 'r') as f:
        return json.load(f)


def is_valid_schema_id(schema_id: str) -> bool:
    """Validate that schema_id follows expected patterns.
    
    Accepts various schema ID formats for forward compatibility:
    - repeat-engage-v*.receipt (current format)
    - repeat-core-v*.receipt (future Core Receipt integration)
    - repeat-*-v*.receipt (other future formats)
    
    Args:
        schema_id: The schema identifier to validate
        
    Returns:
        True if schema_id matches an acceptable pattern
    """
    if not isinstance(schema_id, str):
        return False
    
    # Accept any repeat-*-v*.receipt pattern
    # This allows for evolution while maintaining structure
    parts = schema_id.split('.')
    if len(parts) != 2 or parts[1] != 'receipt':
        return False
    
    prefix = parts[0]
    # Must start with "repeat-" and contain version indicator
    if not prefix.startswith('repeat-') or '-v' not in prefix:
        return False
    
    return True


def validate_receipt_structure(receipt: dict) -> tuple[bool, list[str]]:
    """Validate essential receipt structure and required fields.
    
    This function validates the core structure that should be present
    in all receipt formats, regardless of specific schema version.
    
    Args:
        receipt: The receipt object to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check that receipt is a dictionary
    if not isinstance(receipt, dict):
        errors.append("Receipt must be a dictionary")
        return False, errors
    
    # Required top-level fields
    required_fields = [
        "schema_id",
        "receipt_id",
        "timestamp",
        "engagement_type",
        "participant_id",
        "data",
        "receipt"
    ]
    
    for field in required_fields:
        if field not in receipt:
            errors.append(f"Missing required field: {field}")
    
    # Validate schema_id if present
    if "schema_id" in receipt:
        if not is_valid_schema_id(receipt["schema_id"]):
            errors.append(
                f"Invalid schema_id format: {receipt['schema_id']}. "
                "Expected pattern: repeat-*-v*.receipt"
            )
    
    # Validate receipt_id format if present
    if "receipt_id" in receipt:
        if not isinstance(receipt["receipt_id"], str) or not receipt["receipt_id"]:
            errors.append("receipt_id must be a non-empty string")
    
    # Validate timestamp format if present
    if "timestamp" in receipt:
        if not isinstance(receipt["timestamp"], str):
            errors.append("timestamp must be a string")
        # Basic ISO 8601 format check (YYYY-MM-DDTHH:MM:SSZ)
        elif len(receipt["timestamp"]) < 20 or 'T' not in receipt["timestamp"]:
            errors.append("timestamp must be in ISO 8601 format")
    
    # Validate engagement_type if present
    if "engagement_type" in receipt:
        if not isinstance(receipt["engagement_type"], str) or not receipt["engagement_type"]:
            errors.append("engagement_type must be a non-empty string")
    
    # Validate participant_id if present
    if "participant_id" in receipt:
        if not isinstance(receipt["participant_id"], str) or not receipt["participant_id"]:
            errors.append("participant_id must be a non-empty string")
    
    # Validate data field if present
    if "data" in receipt:
        if not isinstance(receipt["data"], dict):
            errors.append("data must be a dictionary")
    
    # Validate nested receipt object if present
    if "receipt" in receipt:
        if not isinstance(receipt["receipt"], dict):
            errors.append("receipt must contain a nested receipt object")
        elif "sha256_c14n" in receipt["receipt"]:
            sha256_c14n = receipt["receipt"]["sha256_c14n"]
            if not isinstance(sha256_c14n, str):
                errors.append("receipt.sha256_c14n must be a string")
            elif not sha256_c14n.startswith("sha256:"):
                errors.append("receipt.sha256_c14n must start with 'sha256:'")
            elif len(sha256_c14n) != 71:  # "sha256:" + 64 hex chars
                errors.append("receipt.sha256_c14n must be 'sha256:' followed by 64 hex characters")
    
    return len(errors) == 0, errors


class TestEngageGoldenReceipts:
    """Test suite for Engage receipt validation with forward compatibility."""
    
    def test_golden_receipts_exist(self):
        """Verify that golden receipt test vectors exist and are loadable."""
        assert VECTORS_PATH.exists(), f"Golden receipts file not found: {VECTORS_PATH}"
        receipts = load_golden_receipts()
        assert isinstance(receipts, list), "Golden receipts must be a list"
        assert len(receipts) > 0, "Golden receipts must not be empty"
    
    def test_schema_id_validation_patterns(self):
        """Test that schema_id validator accepts expected patterns."""
        # Current format should be accepted
        assert is_valid_schema_id("repeat-engage-v1.receipt")
        assert is_valid_schema_id("repeat-engage-v2.receipt")
        
        # Future Core Receipt format should be accepted
        assert is_valid_schema_id("repeat-core-v1.receipt")
        
        # Other potential future formats should be accepted
        assert is_valid_schema_id("repeat-analytics-v1.receipt")
        assert is_valid_schema_id("repeat-survey-v3.receipt")
        
        # Invalid formats should be rejected
        assert not is_valid_schema_id("invalid-format")
        assert not is_valid_schema_id("repeat-engage.receipt")  # Missing version
        assert not is_valid_schema_id("repeat-engage-v1")  # Missing .receipt
        assert not is_valid_schema_id("engage-v1.receipt")  # Missing repeat- prefix
        assert not is_valid_schema_id("")
        assert not is_valid_schema_id(None)
        assert not is_valid_schema_id(123)
    
    @pytest.mark.parametrize("vector", load_golden_receipts())
    def test_golden_receipt_validation(self, vector):
        """Test that each golden receipt passes validation.
        
        This test validates essential structure and fields without requiring
        a specific schema_id value, ensuring compatibility with current and
        future receipt formats.
        """
        receipt = vector["receipt"]
        is_valid, errors = validate_receipt_structure(receipt)
        
        # Build detailed error message if validation fails
        if not is_valid:
            error_msg = f"\nReceipt validation failed for: {vector['id']}"
            error_msg += f"\nDescription: {vector.get('description', 'N/A')}"
            error_msg += f"\nSchema ID: {receipt.get('schema_id', 'missing')}"
            error_msg += f"\nErrors:\n  - " + "\n  - ".join(errors)
            pytest.fail(error_msg)
    
    def test_current_engage_format_compatible(self):
        """Ensure current repeat-engage-v1.receipt format is accepted."""
        receipt = {
            "schema_id": "repeat-engage-v1.receipt",
            "receipt_id": "TEST-001",
            "timestamp": "2026-02-16T12:00:00Z",
            "engagement_type": "test",
            "participant_id": "P00001",
            "data": {},
            "receipt": {
                "sha256_c14n": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
        is_valid, errors = validate_receipt_structure(receipt)
        assert is_valid, f"Current format should be valid. Errors: {errors}"
    
    def test_future_core_receipt_format_compatible(self):
        """Ensure future repeat-core-v1.receipt format is accepted."""
        receipt = {
            "schema_id": "repeat-core-v1.receipt",
            "receipt_id": "CORE-001",
            "timestamp": "2026-02-16T12:00:00Z",
            "engagement_type": "test",
            "participant_id": "P00002",
            "data": {},
            "receipt": {
                "sha256_c14n": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
            }
        }
        is_valid, errors = validate_receipt_structure(receipt)
        assert is_valid, f"Future Core Receipt format should be valid. Errors: {errors}"
    
    def test_missing_required_fields_rejected(self):
        """Verify that receipts missing required fields are rejected."""
        # Missing schema_id
        receipt = {
            "receipt_id": "TEST-001",
            "timestamp": "2026-02-16T12:00:00Z",
            "engagement_type": "test",
            "participant_id": "P00001",
            "data": {},
            "receipt": {
                "sha256_c14n": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
        is_valid, errors = validate_receipt_structure(receipt)
        assert not is_valid
        assert any("schema_id" in error for error in errors)
    
    def test_invalid_schema_id_rejected(self):
        """Verify that receipts with invalid schema_id format are rejected."""
        receipt = {
            "schema_id": "invalid-schema-format",
            "receipt_id": "TEST-001",
            "timestamp": "2026-02-16T12:00:00Z",
            "engagement_type": "test",
            "participant_id": "P00001",
            "data": {},
            "receipt": {
                "sha256_c14n": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
        is_valid, errors = validate_receipt_structure(receipt)
        assert not is_valid
        assert any("schema_id" in error for error in errors)
    
    def test_invalid_sha256_format_rejected(self):
        """Verify that receipts with invalid sha256_c14n format are rejected."""
        # Missing sha256: prefix
        receipt = {
            "schema_id": "repeat-engage-v1.receipt",
            "receipt_id": "TEST-001",
            "timestamp": "2026-02-16T12:00:00Z",
            "engagement_type": "test",
            "participant_id": "P00001",
            "data": {},
            "receipt": {
                "sha256_c14n": "0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
        is_valid, errors = validate_receipt_structure(receipt)
        assert not is_valid
        assert any("sha256:" in error for error in errors)
        
        # Wrong length
        receipt["receipt"]["sha256_c14n"] = "sha256:abc"
        is_valid, errors = validate_receipt_structure(receipt)
        assert not is_valid
        assert any("64 hex" in error for error in errors)
