"""Tests for spintronics hash module."""

import pytest
from spintronics.hash import (
    hash_packet,
    hash_trace,
    compute_receipt_hash,
    verify_checksum
)


class TestHashPacket:
    """Tests for hash_packet function."""
    
    def test_deterministic_hash(self):
        """Test that hashing is deterministic."""
        packet = {"id": "test", "data": [1, 2, 3]}
        hash1 = hash_packet(packet)
        hash2 = hash_packet(packet)
        assert hash1 == hash2
    
    def test_sha256_default(self):
        """Test SHA-256 as default algorithm."""
        packet = {"value": 42}
        result = hash_packet(packet)
        assert len(result) == 64  # SHA-256 produces 64 hex chars
    
    def test_md5_algorithm(self):
        """Test MD5 algorithm."""
        packet = {"value": 42}
        result = hash_packet(packet, algorithm='md5')
        assert len(result) == 32  # MD5 produces 32 hex chars
    
    def test_key_order_independence(self):
        """Test that key order doesn't affect hash."""
        packet1 = {"a": 1, "b": 2}
        packet2 = {"b": 2, "a": 1}
        assert hash_packet(packet1) == hash_packet(packet2)
    
    def test_invalid_algorithm(self):
        """Test handling of invalid algorithm."""
        packet = {"value": 42}
        with pytest.raises(ValueError):
            hash_packet(packet, algorithm='invalid')


class TestHashTrace:
    """Tests for hash_trace function."""
    
    def test_pulse_sequence_hash(self):
        """Test hashing of pulse sequence."""
        pulses = [
            {"index": 0, "amplitude": 1.0},
            {"index": 1, "amplitude": 2.0}
        ]
        result = hash_trace(pulses)
        assert len(result) == 64
    
    def test_empty_sequence(self):
        """Test hashing empty pulse sequence."""
        result = hash_trace([])
        assert len(result) == 64


class TestComputeReceiptHash:
    """Tests for compute_receipt_hash function."""
    
    def test_receipt_hash(self):
        """Test computing receipt hash."""
        write_op = {"address": "0x100", "data_bit": 1}
        read_op = {"resistance_state": 1000.0, "decoded_bit": 1}
        result = compute_receipt_hash(write_op, read_op)
        assert len(result) == 64
    
    def test_deterministic(self):
        """Test receipt hash is deterministic."""
        write_op = {"address": "0x100", "data_bit": 1}
        read_op = {"resistance_state": 1000.0, "decoded_bit": 1}
        hash1 = compute_receipt_hash(write_op, read_op)
        hash2 = compute_receipt_hash(write_op, read_op)
        assert hash1 == hash2


class TestVerifyChecksum:
    """Tests for verify_checksum function."""
    
    def test_valid_checksum(self):
        """Test verification of valid checksum."""
        data = {"value": 42}
        checksum = hash_packet(data)
        assert verify_checksum(data, checksum) is True
    
    def test_invalid_checksum(self):
        """Test rejection of invalid checksum."""
        data = {"value": 42}
        assert verify_checksum(data, "invalid") is False
    
    def test_modified_data(self):
        """Test detection of modified data."""
        data1 = {"value": 42}
        checksum = hash_packet(data1)
        data2 = {"value": 43}
        assert verify_checksum(data2, checksum) is False
