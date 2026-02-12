"""
Test suite for validating REPEAT Receipt v1 contract compliance.

This test discovers all *.receipt.json files in the repository and validates
them against the core receipt schema (schemas/repeat_receipt.v1.schema.json).
"""

import json
import pathlib
from typing import List

import pytest

# Import jsonschema if available, otherwise skip tests
try:
    import jsonschema
    from jsonschema import Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


# Repository root is assumed to be parent of tests/ directory
REPO_ROOT = pathlib.Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "repeat_receipt.v1.schema.json"


def find_receipt_files() -> List[pathlib.Path]:
    """
    Discover all *.receipt.json files in the repository.
    
    Returns:
        List of Path objects pointing to receipt files.
    """
    receipt_files = list(REPO_ROOT.glob("**/*.receipt.json"))
    return sorted(receipt_files)


def load_json_file(file_path: pathlib.Path) -> dict:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Parsed JSON as a dictionary.
        
    Raises:
        ValueError: If the file cannot be parsed as valid JSON.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def load_schema() -> dict:
    """
    Load the REPEAT Receipt v1 schema.
    
    Returns:
        The schema as a dictionary.
        
    Raises:
        FileNotFoundError: If schema file does not exist.
        ValueError: If schema is not valid JSON.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}\n"
            "Expected schemas/repeat_receipt.v1.schema.json to exist."
        )
    return load_json_file(SCHEMA_PATH)


@pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema library not installed")
class TestRepeatReceiptContract:
    """Test suite for REPEAT Receipt v1 contract validation."""
    
    def test_schema_exists(self):
        """Verify that the receipt schema file exists."""
        assert SCHEMA_PATH.exists(), (
            f"Schema file not found at {SCHEMA_PATH}. "
            "Expected schemas/repeat_receipt.v1.schema.json to exist."
        )
    
    def test_schema_is_valid_json(self):
        """Verify that the schema file is valid JSON."""
        try:
            load_schema()
        except ValueError as e:
            pytest.fail(f"Schema is not valid JSON: {e}")
    
    def test_schema_is_valid_json_schema(self):
        """Verify that the schema is a valid JSON Schema (Draft 7)."""
        schema = load_schema()
        try:
            Draft7Validator.check_schema(schema)
        except jsonschema.SchemaError as e:
            pytest.fail(f"Schema is not a valid JSON Schema: {e}")
    
    def test_discover_receipt_files(self):
        """
        Discover all receipt files in the repository.
        
        This test passes if no receipt files are found (allowing repos
        to adopt the schema before creating receipts) but logs a warning.
        """
        receipt_files = find_receipt_files()
        
        if not receipt_files:
            pytest.skip(
                "No *.receipt.json files found in repository. "
                "This is acceptable for initial schema adoption."
            )
        
        # If we found files, log them for visibility
        print(f"\nFound {len(receipt_files)} receipt file(s):")
        for receipt_file in receipt_files:
            rel_path = receipt_file.relative_to(REPO_ROOT)
            print(f"  - {rel_path}")
    
    def test_validate_all_receipts(self):
        """
        Validate all *.receipt.json files against the core schema.
        
        This test will:
        - Skip if no receipt files exist (valid for initial adoption)
        - Fail with clear error messages for each invalid receipt
        - Pass if all receipts are valid
        """
        receipt_files = find_receipt_files()
        
        if not receipt_files:
            pytest.skip(
                "No *.receipt.json files found. "
                "Schema validation will run when receipts are added."
            )
        
        schema = load_schema()
        validator = Draft7Validator(schema)
        
        validation_errors = []
        
        for receipt_file in receipt_files:
            rel_path = receipt_file.relative_to(REPO_ROOT)
            
            try:
                receipt_data = load_json_file(receipt_file)
            except ValueError as e:
                validation_errors.append(
                    f"\n  File: {rel_path}\n"
                    f"  Error: {e}\n"
                )
                continue
            
            # Validate against schema
            errors = list(validator.iter_errors(receipt_data))
            
            if errors:
                error_messages = []
                for error in errors:
                    # Build a clear path to the problematic field
                    field_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
                    error_messages.append(
                        f"    - Field: {field_path}\n"
                        f"      Message: {error.message}\n"
                        f"      Schema path: {'.'.join(str(p) for p in error.absolute_schema_path)}"
                    )
                
                validation_errors.append(
                    f"\n  File: {rel_path}\n"
                    f"  Validation errors:\n" + "\n".join(error_messages)
                )
        
        if validation_errors:
            error_summary = (
                f"\n{'='*70}\n"
                f"REPEAT Receipt v1 Contract Validation Failed\n"
                f"{'='*70}\n"
                f"\nSchema: {SCHEMA_PATH.relative_to(REPO_ROOT)}\n"
                f"Failed {len(validation_errors)} of {len(receipt_files)} receipt file(s):\n"
                + "".join(validation_errors) +
                f"\n{'='*70}\n"
            )
            pytest.fail(error_summary)


# Convenience test that can run even without jsonschema
def test_schema_file_exists_without_jsonschema():
    """
    Basic test to ensure schema file exists.
    
    This test runs even if jsonschema is not installed,
    ensuring the schema file is at least present.
    """
    assert SCHEMA_PATH.exists(), (
        f"Schema file not found at {SCHEMA_PATH}. "
        "Expected schemas/repeat_receipt.v1.schema.json to exist."
    )
