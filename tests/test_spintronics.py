"""Tests for the spintronics MRAM MVP module."""

import pytest
import json
from repeat_spintronics import (
    encode_to_magnetization,
    decode_from_magnetization,
    create_mram_packet,
    read_mram_packet,
    verify_packet_receipt,
)
from repeat_spintronics.encoder import get_tetrahedron_state


class TestEncoder:
    """Tests for magnetization texture encoding/decoding."""
    
    def test_encode_single_byte(self):
        """Test encoding a single byte."""
        data = b"A"  # 0x41
        textures = encode_to_magnetization(data)
        # Should produce 8 textures (one per bit)
        assert len(textures) == 8
        # Each texture should be a 5-tuple
        for texture in textures:
            assert len(texture) == 5
    
    def test_encode_multiple_bytes(self):
        """Test encoding multiple bytes."""
        data = b"Test"
        textures = encode_to_magnetization(data)
        # 4 bytes * 8 bits = 32 textures
        assert len(textures) == 32
    
    def test_encode_empty_data(self):
        """Test encoding empty data."""
        data = b""
        textures = encode_to_magnetization(data)
        assert len(textures) == 0
    
    def test_decode_single_byte(self):
        """Test decoding a single byte."""
        original = b"X"
        textures = encode_to_magnetization(original)
        decoded = decode_from_magnetization(textures)
        assert decoded == original
    
    def test_decode_multiple_bytes(self):
        """Test decoding multiple bytes."""
        original = b"Hello"
        textures = encode_to_magnetization(original)
        decoded = decode_from_magnetization(textures)
        assert decoded == original
    
    def test_decode_empty_data(self):
        """Test decoding empty data."""
        textures = []
        decoded = decode_from_magnetization(textures)
        assert decoded == b""
    
    def test_decode_invalid_texture_count(self):
        """Test decoding with non-multiple of 8 textures."""
        # Create 5 textures (not a full byte)
        textures = encode_to_magnetization(b"A")[:5]
        decoded = decode_from_magnetization(textures)
        assert decoded is None
    
    def test_encode_decode_roundtrip(self):
        """Test encode-decode roundtrip for various data."""
        test_data = [
            b"A",
            b"Test",
            b"Hello, World!",
            b"\x00\x01\x02\xff",
            b"The quick brown fox",
        ]
        
        for data in test_data:
            textures = encode_to_magnetization(data)
            decoded = decode_from_magnetization(textures)
            assert decoded == data, f"Failed for data: {data}"
    
    def test_tetrahedron_state_extraction(self):
        """Test extraction of tetrahedron state from texture."""
        # Encode both binary states
        textures_0 = encode_to_magnetization(b"\x00")
        textures_1 = encode_to_magnetization(b"\xff")
        
        # Check that we can extract states
        for texture in textures_0:
            state = get_tetrahedron_state(texture)
            assert state in [0, 1]
        
        for texture in textures_1:
            state = get_tetrahedron_state(texture)
            assert state in [0, 1]


class TestPacketizer:
    """Tests for MRAM packet creation and reading."""
    
    def test_create_packet_basic(self):
        """Test creating a basic MRAM packet."""
        data = b"Test"
        packet = create_mram_packet(data)
        
        # Verify required fields
        assert "version" in packet
        assert packet["version"] == "1.0.0"
        assert "packet_id" in packet
        assert "operation" in packet
        assert packet["operation"] == "write"
        assert "timestamp" in packet
        assert "data" in packet
        assert "checksum" in packet
    
    def test_create_packet_with_operation(self):
        """Test creating packets with different operations."""
        data = b"Data"
        
        write_packet = create_mram_packet(data, operation="write")
        assert write_packet["operation"] == "write"
        
        read_packet = create_mram_packet(data, operation="read")
        assert read_packet["operation"] == "read"
    
    def test_create_packet_invalid_operation(self):
        """Test creating packet with invalid operation."""
        with pytest.raises(ValueError):
            create_mram_packet(b"Data", operation="invalid")
    
    def test_create_packet_data_structure(self):
        """Test packet data structure."""
        data = b"ABC"
        packet = create_mram_packet(data)
        
        # Check data structure
        assert "textures" in packet["data"]
        assert "metadata" in packet["data"]
        
        # Check metadata
        metadata = packet["data"]["metadata"]
        assert metadata["byte_count"] == 3
        assert metadata["encoding_method"] == "tetrahedron_5solids"
        assert "original_hash" in metadata
        assert len(metadata["original_hash"]) == 64  # SHA-256 hex
    
    def test_create_packet_textures_count(self):
        """Test packet has correct number of textures."""
        data = b"Hi"
        packet = create_mram_packet(data)
        
        textures = packet["data"]["textures"]
        # 2 bytes * 8 bits = 16 textures
        assert len(textures) == 16
        
        # Each texture should be a 5-element list
        for texture in textures:
            assert len(texture) == 5
    
    def test_create_packet_checksum(self):
        """Test packet has valid checksum."""
        data = b"Test"
        packet = create_mram_packet(data)
        
        assert "checksum" in packet
        assert len(packet["checksum"]) == 64  # SHA-256 hex
    
    def test_create_packet_unique_ids(self):
        """Test that packet IDs are unique."""
        data = b"Same"
        packet1 = create_mram_packet(data)
        packet2 = create_mram_packet(data)
        
        assert packet1["packet_id"] != packet2["packet_id"]
    
    def test_read_packet_basic(self):
        """Test reading data from a packet."""
        original = b"Hello"
        packet = create_mram_packet(original)
        decoded = read_mram_packet(packet)
        
        assert decoded == original
    
    def test_read_packet_empty(self):
        """Test reading empty packet."""
        packet = create_mram_packet(b"")
        decoded = read_mram_packet(packet)
        assert decoded == b""
    
    def test_read_packet_various_data(self):
        """Test reading packets with various data."""
        test_data = [
            b"A",
            b"Short",
            b"A longer test string",
            b"\x00\x01\x02\x03",
        ]
        
        for data in test_data:
            packet = create_mram_packet(data)
            decoded = read_mram_packet(packet)
            assert decoded == data
    
    def test_read_packet_invalid_structure(self):
        """Test reading packet with invalid structure."""
        invalid_packet = {"invalid": "structure"}
        decoded = read_mram_packet(invalid_packet)
        assert decoded is None


class TestVerifierProofs:
    """Tests for SHA-based verifier proofs."""
    
    def test_verify_receipt_basic(self):
        """Test creating a basic receipt."""
        data = b"Test"
        packet = create_mram_packet(data)
        receipt = verify_packet_receipt(packet)
        
        # Verify required fields
        assert "version" in receipt
        assert receipt["version"] == "1.0.0"
        assert "receipt_id" in receipt
        assert "packet_id" in receipt
        assert receipt["packet_id"] == packet["packet_id"]
        assert "operation" in receipt
        assert "timestamp" in receipt
        assert "status" in receipt
        assert "verifier_proof" in receipt
        assert "result" in receipt
    
    def test_verify_receipt_success_status(self):
        """Test receipt has success status for valid packet."""
        data = b"Valid"
        packet = create_mram_packet(data)
        receipt = verify_packet_receipt(packet)
        
        assert receipt["status"] == "success"
        assert receipt["verifier_proof"]["verification_status"] == "verified"
    
    def test_verify_receipt_proof_structure(self):
        """Test verifier proof structure."""
        data = b"Data"
        packet = create_mram_packet(data)
        receipt = verify_packet_receipt(packet)
        
        proof = receipt["verifier_proof"]
        assert "packet_hash" in proof
        assert "data_hash" in proof
        assert "proof_chain" in proof
        assert "verification_status" in proof
        
        # Proof chain should have multiple hashes
        assert len(proof["proof_chain"]) >= 1
        
        # All hashes should be 64 chars (SHA-256 hex)
        assert len(proof["packet_hash"]) == 64
        assert len(proof["data_hash"]) == 64
        for hash_val in proof["proof_chain"]:
            assert len(hash_val) == 64
    
    def test_verify_receipt_with_predecoded_data(self):
        """Test creating receipt with pre-decoded data."""
        data = b"PreDecoded"
        packet = create_mram_packet(data)
        receipt = verify_packet_receipt(packet, decoded_data=data)
        
        assert receipt["status"] == "success"
        assert receipt["result"]["decoded_bytes"] == len(data)
    
    def test_verify_receipt_result_data(self):
        """Test receipt result data."""
        data = b"Result"
        packet = create_mram_packet(data)
        receipt = verify_packet_receipt(packet)
        
        result = receipt["result"]
        assert "decoded_bytes" in result
        assert result["decoded_bytes"] == len(data)
    
    def test_verify_receipt_unique_ids(self):
        """Test that receipt IDs are unique."""
        packet = create_mram_packet(b"Same")
        receipt1 = verify_packet_receipt(packet)
        receipt2 = verify_packet_receipt(packet)
        
        assert receipt1["receipt_id"] != receipt2["receipt_id"]
    
    def test_verify_receipt_hash_consistency(self):
        """Test that hashes in proof chain are consistent."""
        data = b"Consistent"
        packet = create_mram_packet(data)
        receipt = verify_packet_receipt(packet)
        
        proof = receipt["verifier_proof"]
        
        # Data hash should match packet's original hash
        original_hash = packet["data"]["metadata"]["original_hash"]
        assert proof["data_hash"] == original_hash


class TestIntegration:
    """Integration tests for the full spintronics system."""
    
    def test_full_workflow(self):
        """Test complete workflow: encode -> packet -> read -> verify."""
        original_data = b"Complete workflow test"
        
        # Create packet
        packet = create_mram_packet(original_data)
        
        # Read packet
        decoded_data = read_mram_packet(packet)
        assert decoded_data == original_data
        
        # Verify receipt
        receipt = verify_packet_receipt(packet)
        assert receipt["status"] == "success"
        assert receipt["verifier_proof"]["verification_status"] == "verified"
    
    def test_multiple_packets(self):
        """Test creating and processing multiple packets."""
        test_data = [
            b"First",
            b"Second",
            b"Third",
        ]
        
        packets = []
        for data in test_data:
            packet = create_mram_packet(data)
            packets.append(packet)
        
        # Read all packets
        for i, packet in enumerate(packets):
            decoded = read_mram_packet(packet)
            assert decoded == test_data[i]
    
    def test_packet_serialization(self):
        """Test that packets can be serialized to JSON."""
        data = b"Serialize me"
        packet = create_mram_packet(data)
        
        # Serialize to JSON
        json_str = json.dumps(packet)
        assert json_str is not None
        
        # Deserialize from JSON
        packet_restored = json.loads(json_str)
        
        # Read restored packet
        decoded = read_mram_packet(packet_restored)
        assert decoded == data
    
    def test_receipt_serialization(self):
        """Test that receipts can be serialized to JSON."""
        data = b"Receipt test"
        packet = create_mram_packet(data)
        receipt = verify_packet_receipt(packet)
        
        # Serialize to JSON
        json_str = json.dumps(receipt)
        assert json_str is not None
        
        # Deserialize from JSON
        receipt_restored = json.loads(json_str)
        
        # Verify structure
        assert receipt_restored["status"] == "success"
        assert receipt_restored["verifier_proof"]["verification_status"] == "verified"
    
    def test_deterministic_encoding(self):
        """Test that encoding is deterministic for same input."""
        data = b"Deterministic"
        
        # Encode multiple times
        textures1 = encode_to_magnetization(data)
        textures2 = encode_to_magnetization(data)
        
        # Should produce identical results
        assert len(textures1) == len(textures2)
        for t1, t2 in zip(textures1, textures2):
            assert t1 == t2
    
    def test_various_byte_patterns(self):
        """Test with various byte patterns."""
        patterns = [
            b"\x00",  # All zeros
            b"\xff",  # All ones
            b"\xaa",  # Alternating 10101010
            b"\x55",  # Alternating 01010101
            b"\x00\xff",  # Mixed
        ]
        
        for pattern in patterns:
            packet = create_mram_packet(pattern)
            decoded = read_mram_packet(packet)
            assert decoded == pattern
            
            receipt = verify_packet_receipt(packet)
            assert receipt["status"] == "success"
