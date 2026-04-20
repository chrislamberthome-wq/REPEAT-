"""
Tests for the BLE Settings module — B4IU interface and IAM_BORG collective.

Covers:
  - BLESettings defaults and serialisation round-trip
  - validate_ble_settings: valid and invalid parameter combinations
  - B4IUInterface.verify: receipt structure and hash integrity
  - IAMBorgCollective: node management, consensus computation, audit trace
"""

import json
import math
import pytest

from ble.settings import (
    BLESettings,
    validate_ble_settings,
    B4IUInterface,
    IAMBorgCollective,
    BLE_SETTINGS_SCHEMA,
    SHA256_PREFIX,
    _sha256_c14n,
    _canonical_json,
    BLE_ADVERTISING_INTERVAL_MIN_MS,
    BLE_ADVERTISING_INTERVAL_MAX_MS,
    BLE_CONNECTION_INTERVAL_MIN_MS,
    BLE_CONNECTION_INTERVAL_MAX_MS,
    BLE_TX_POWER_MIN_DBM,
    BLE_TX_POWER_MAX_DBM,
    BLE_MTU_MIN,
    BLE_MTU_MAX,
    BLE_SCAN_INTERVAL_MIN_MS,
    BLE_SCAN_INTERVAL_MAX_MS,
    BLE_SCAN_WINDOW_MIN_MS,
    BLE_SCAN_WINDOW_MAX_MS,
)


# ---------------------------------------------------------------------------
# BLESettings dataclass
# ---------------------------------------------------------------------------

class TestBLESettings:
    """Tests for BLESettings dataclass."""

    def test_default_device_id(self):
        """Default device_id is non-empty."""
        s = BLESettings()
        assert s.device_id == "ble-node-default"

    def test_default_values_are_valid(self):
        """Default BLESettings must pass validation."""
        errors = validate_ble_settings(BLESettings())
        assert errors == []

    def test_to_dict_returns_dict(self):
        """to_dict() returns a plain dict."""
        s = BLESettings(device_id="x")
        d = s.to_dict()
        assert isinstance(d, dict)
        assert d["device_id"] == "x"

    def test_from_dict_roundtrip(self):
        """from_dict(to_dict()) is identity."""
        original = BLESettings(
            device_id="node-99",
            tx_power_dbm=-10,
            mtu_bytes=100,
        )
        restored = BLESettings.from_dict(original.to_dict())
        assert restored == original

    def test_from_dict_ignores_unknown_keys(self):
        """from_dict silently drops unknown keys."""
        d = BLESettings().to_dict()
        d["future_field"] = "ignored"
        s = BLESettings.from_dict(d)
        assert s == BLESettings()

    def test_to_dict_is_json_serialisable(self):
        """to_dict() must be JSON-serialisable without error."""
        d = BLESettings().to_dict()
        serialised = json.dumps(d)
        assert isinstance(serialised, str)


# ---------------------------------------------------------------------------
# validate_ble_settings
# ---------------------------------------------------------------------------

class TestValidateBLESettings:
    """Tests for validate_ble_settings function."""

    def test_valid_defaults(self):
        """Default settings produce no errors."""
        assert validate_ble_settings(BLESettings()) == []

    def test_valid_boundary_values(self):
        """Exact boundary values are accepted."""
        s = BLESettings(
            device_id="edge",
            advertising_interval_ms=BLE_ADVERTISING_INTERVAL_MIN_MS,
            connection_interval_min_ms=BLE_CONNECTION_INTERVAL_MIN_MS,
            connection_interval_max_ms=BLE_CONNECTION_INTERVAL_MAX_MS,
            tx_power_dbm=BLE_TX_POWER_MIN_DBM,
            mtu_bytes=BLE_MTU_MIN,
            scan_interval_ms=BLE_SCAN_INTERVAL_MIN_MS,
            scan_window_ms=BLE_SCAN_WINDOW_MIN_MS,
        )
        assert validate_ble_settings(s) == []

    def test_empty_device_id_is_invalid(self):
        """Empty device_id produces an error."""
        errors = validate_ble_settings(BLESettings(device_id=""))
        assert any("device_id" in e for e in errors)

    def test_whitespace_only_device_id_is_invalid(self):
        """Whitespace-only device_id produces an error."""
        errors = validate_ble_settings(BLESettings(device_id="   "))
        assert any("device_id" in e for e in errors)

    def test_advertising_interval_below_min(self):
        """advertising_interval_ms below min is rejected."""
        errors = validate_ble_settings(
            BLESettings(advertising_interval_ms=BLE_ADVERTISING_INTERVAL_MIN_MS - 1)
        )
        assert any("advertising_interval_ms" in e for e in errors)

    def test_advertising_interval_above_max(self):
        """advertising_interval_ms above max is rejected."""
        errors = validate_ble_settings(
            BLESettings(advertising_interval_ms=BLE_ADVERTISING_INTERVAL_MAX_MS + 1)
        )
        assert any("advertising_interval_ms" in e for e in errors)

    def test_connection_interval_min_below_bound(self):
        """connection_interval_min_ms below bound is rejected."""
        errors = validate_ble_settings(
            BLESettings(connection_interval_min_ms=BLE_CONNECTION_INTERVAL_MIN_MS - 1)
        )
        assert any("connection_interval_min_ms" in e for e in errors)

    def test_connection_interval_max_above_bound(self):
        """connection_interval_max_ms above bound is rejected."""
        errors = validate_ble_settings(
            BLESettings(connection_interval_max_ms=BLE_CONNECTION_INTERVAL_MAX_MS + 1)
        )
        assert any("connection_interval_max_ms" in e for e in errors)

    def test_connection_interval_min_exceeds_max(self):
        """connection_interval_min > max is rejected."""
        errors = validate_ble_settings(
            BLESettings(
                connection_interval_min_ms=100.0,
                connection_interval_max_ms=50.0,
            )
        )
        assert any("must not exceed" in e for e in errors)

    def test_tx_power_below_min(self):
        """tx_power_dbm below min is rejected."""
        errors = validate_ble_settings(
            BLESettings(tx_power_dbm=BLE_TX_POWER_MIN_DBM - 1)
        )
        assert any("tx_power_dbm" in e for e in errors)

    def test_tx_power_above_max(self):
        """tx_power_dbm above max is rejected."""
        errors = validate_ble_settings(
            BLESettings(tx_power_dbm=BLE_TX_POWER_MAX_DBM + 1)
        )
        assert any("tx_power_dbm" in e for e in errors)

    def test_mtu_below_min(self):
        """mtu_bytes below min is rejected."""
        errors = validate_ble_settings(BLESettings(mtu_bytes=BLE_MTU_MIN - 1))
        assert any("mtu_bytes" in e for e in errors)

    def test_mtu_above_max(self):
        """mtu_bytes above max is rejected."""
        errors = validate_ble_settings(BLESettings(mtu_bytes=BLE_MTU_MAX + 1))
        assert any("mtu_bytes" in e for e in errors)

    def test_scan_interval_below_min(self):
        """scan_interval_ms below min is rejected."""
        errors = validate_ble_settings(
            BLESettings(scan_interval_ms=BLE_SCAN_INTERVAL_MIN_MS - 1)
        )
        assert any("scan_interval_ms" in e for e in errors)

    def test_scan_window_exceeds_interval(self):
        """scan_window_ms > scan_interval_ms is rejected."""
        errors = validate_ble_settings(
            BLESettings(scan_interval_ms=50.0, scan_window_ms=100.0)
        )
        assert any("scan_window_ms" in e and "must not exceed" in e for e in errors)

    def test_multiple_violations_reported_together(self):
        """All violations are reported in a single call (not fail-fast)."""
        s = BLESettings(
            device_id="",
            advertising_interval_ms=5.0,   # below min
            tx_power_dbm=100,              # above max
        )
        errors = validate_ble_settings(s)
        assert len(errors) >= 3


# ---------------------------------------------------------------------------
# B4IUInterface
# ---------------------------------------------------------------------------

class TestB4IUInterface:
    """Tests for B4IUInterface.verify."""

    def setup_method(self):
        self.b4iu = B4IUInterface()

    def test_valid_settings_returns_true(self):
        """Valid settings produce is_valid == True."""
        ok, errors, _ = self.b4iu.verify(BLESettings())
        assert ok is True
        assert errors == []

    def test_invalid_settings_returns_false(self):
        """Invalid settings produce is_valid == False with non-empty errors."""
        ok, errors, _ = self.b4iu.verify(BLESettings(tx_power_dbm=999))
        assert ok is False
        assert errors

    def test_receipt_has_required_fields(self):
        """Receipt contains all required schema fields."""
        _, _, receipt = self.b4iu.verify(BLESettings())
        assert "schema" in receipt
        assert "settings_hash_sha256" in receipt
        assert "verdict" in receipt
        assert "receipt_hash_sha256" in receipt

    def test_receipt_schema_identifier(self):
        """Receipt schema identifier matches BLE_SETTINGS_SCHEMA."""
        _, _, receipt = self.b4iu.verify(BLESettings())
        assert receipt["schema"] == BLE_SETTINGS_SCHEMA

    def test_receipt_verdict_pass_true_for_valid(self):
        """Verdict pass is True for valid settings."""
        _, _, receipt = self.b4iu.verify(BLESettings())
        assert receipt["verdict"]["pass"] is True
        assert receipt["verdict"]["errors"] == []

    def test_receipt_verdict_pass_false_for_invalid(self):
        """Verdict pass is False for invalid settings."""
        _, _, receipt = self.b4iu.verify(BLESettings(tx_power_dbm=999))
        assert receipt["verdict"]["pass"] is False
        assert receipt["verdict"]["errors"]

    def test_settings_hash_format(self):
        """settings_hash_sha256 has correct sha256: prefix and length."""
        _, _, receipt = self.b4iu.verify(BLESettings())
        h = receipt["settings_hash_sha256"]
        assert h.startswith(SHA256_PREFIX)
        assert len(h) == len(SHA256_PREFIX) + 64

    def test_receipt_hash_format(self):
        """receipt_hash_sha256 has correct sha256: prefix and length."""
        _, _, receipt = self.b4iu.verify(BLESettings())
        h = receipt["receipt_hash_sha256"]
        assert h.startswith(SHA256_PREFIX)
        assert len(h) == len(SHA256_PREFIX) + 64

    def test_receipt_hash_integrity(self):
        """receipt_hash_sha256 is verifiable by recomputing it."""
        _, _, receipt = self.b4iu.verify(BLESettings())
        stored_hash = receipt["receipt_hash_sha256"]
        # Recompute over receipt minus receipt_hash_sha256 field
        body_without_hash = {k: v for k, v in receipt.items() if k != "receipt_hash_sha256"}
        recomputed = _sha256_c14n(body_without_hash)
        assert stored_hash == recomputed

    def test_settings_hash_is_deterministic(self):
        """Same settings always produce the same settings_hash."""
        s = BLESettings(device_id="test-node", tx_power_dbm=4)
        _, _, r1 = self.b4iu.verify(s)
        _, _, r2 = self.b4iu.verify(s)
        assert r1["settings_hash_sha256"] == r2["settings_hash_sha256"]

    def test_different_settings_produce_different_hash(self):
        """Different settings produce different settings_hash."""
        _, _, r1 = self.b4iu.verify(BLESettings(tx_power_dbm=0))
        _, _, r2 = self.b4iu.verify(BLESettings(tx_power_dbm=4))
        assert r1["settings_hash_sha256"] != r2["settings_hash_sha256"]

    def test_receipt_is_json_serialisable(self):
        """Receipt must be JSON-serialisable."""
        _, _, receipt = self.b4iu.verify(BLESettings())
        serialised = json.dumps(receipt)
        assert isinstance(serialised, str)


# ---------------------------------------------------------------------------
# IAMBorgCollective
# ---------------------------------------------------------------------------

class TestIAMBorgCollective:
    """Tests for IAMBorgCollective."""

    def setup_method(self):
        self.borg = IAMBorgCollective()

    def test_initial_node_count_is_zero(self):
        """Fresh collective has zero nodes."""
        assert self.borg.node_count == 0

    def test_add_valid_node(self):
        """Valid node is accepted without error."""
        self.borg.add_node("node-a", BLESettings())
        assert self.borg.node_count == 1

    def test_add_invalid_node_raises(self):
        """Invalid settings are rejected by B4IU; ValueError raised."""
        with pytest.raises(ValueError, match="B4IU"):
            self.borg.add_node("bad", BLESettings(tx_power_dbm=999))
        assert self.borg.node_count == 0

    def test_remove_existing_node(self):
        """Removing a registered node decrements count."""
        self.borg.add_node("node-a", BLESettings())
        self.borg.remove_node("node-a")
        assert self.borg.node_count == 0

    def test_remove_unknown_node_raises(self):
        """Removing a non-existent node raises KeyError."""
        with pytest.raises(KeyError):
            self.borg.remove_node("ghost")

    def test_compute_consensus_no_nodes_raises(self):
        """compute_consensus with no nodes raises ValueError."""
        with pytest.raises(ValueError, match="no registered nodes"):
            self.borg.compute_consensus()

    def test_compute_consensus_single_node(self):
        """Consensus of one node equals that node's settings (except device_id)."""
        s = BLESettings(device_id="solo", tx_power_dbm=4, mtu_bytes=100)
        self.borg.add_node("solo", s)
        consensus = self.borg.compute_consensus()
        assert consensus.tx_power_dbm == 4
        assert consensus.mtu_bytes == 100

    def test_compute_consensus_mean_of_two(self):
        """Consensus of two nodes averages numeric fields."""
        self.borg.add_node("a", BLESettings(tx_power_dbm=0))
        self.borg.add_node("b", BLESettings(tx_power_dbm=4))
        consensus = self.borg.compute_consensus()
        assert consensus.tx_power_dbm == 2  # round((0+4)/2) == 2

    def test_compute_consensus_mtu_mean(self):
        """Consensus MTU is the rounded mean of all nodes."""
        self.borg.add_node("x", BLESettings(mtu_bytes=100))
        self.borg.add_node("y", BLESettings(mtu_bytes=200))
        self.borg.add_node("z", BLESettings(mtu_bytes=300))
        consensus = self.borg.compute_consensus()
        assert consensus.mtu_bytes == 200  # round(600/3)

    def test_compute_consensus_is_deterministic(self):
        """Calling compute_consensus twice returns identical settings."""
        self.borg.add_node("a", BLESettings(tx_power_dbm=-4))
        self.borg.add_node("b", BLESettings(tx_power_dbm=4))
        c1 = self.borg.compute_consensus()
        c2 = self.borg.compute_consensus()
        assert c1 == c2

    def test_consensus_device_id_is_lexicographic_min(self):
        """Consensus device_id is the lexicographic minimum."""
        self.borg.add_node("alpha", BLESettings(device_id="zebra"))
        self.borg.add_node("beta", BLESettings(device_id="alpha"))
        consensus = self.borg.compute_consensus()
        assert consensus.device_id == "alpha"

    def test_consensus_advertising_enabled_majority_true(self):
        """Majority True → advertising_enabled is True."""
        self.borg.add_node("a", BLESettings(advertising_enabled=True))
        self.borg.add_node("b", BLESettings(advertising_enabled=True))
        self.borg.add_node("c", BLESettings(advertising_enabled=False))
        consensus = self.borg.compute_consensus()
        assert consensus.advertising_enabled is True

    def test_consensus_advertising_enabled_majority_false(self):
        """Majority False → advertising_enabled is False."""
        self.borg.add_node("a", BLESettings(advertising_enabled=False))
        self.borg.add_node("b", BLESettings(advertising_enabled=False))
        self.borg.add_node("c", BLESettings(advertising_enabled=True))
        consensus = self.borg.compute_consensus()
        assert consensus.advertising_enabled is False

    def test_add_node_appends_to_audit_trace(self):
        """add_node appends an entry to the audit trace."""
        self.borg.add_node("n1", BLESettings())
        trace = self.borg.get_audit_trace()
        assert any(e.get("event") == "add_node" for e in trace)

    def test_remove_node_appends_to_audit_trace(self):
        """remove_node appends an entry to the audit trace."""
        self.borg.add_node("n1", BLESettings())
        self.borg.remove_node("n1")
        trace = self.borg.get_audit_trace()
        assert any(e.get("event") == "remove_node" for e in trace)

    def test_compute_consensus_appends_to_audit_trace(self):
        """compute_consensus appends an entry to the audit trace."""
        self.borg.add_node("n1", BLESettings())
        self.borg.compute_consensus()
        trace = self.borg.get_audit_trace()
        assert any(e.get("event") == "compute_consensus" for e in trace)

    def test_audit_trace_entries_contain_receipt(self):
        """add_node audit trace entries include a B4IU receipt."""
        self.borg.add_node("n1", BLESettings())
        trace = self.borg.get_audit_trace()
        add_events = [e for e in trace if e.get("event") == "add_node"]
        assert add_events
        for evt in add_events:
            assert "receipt" in evt
            assert "schema" in evt["receipt"]

    def test_get_audit_trace_returns_copy(self):
        """get_audit_trace() returns a copy; mutations do not affect state."""
        self.borg.add_node("n1", BLESettings())
        trace = self.borg.get_audit_trace()
        trace.clear()
        assert self.borg.get_audit_trace()  # internal trace unchanged

    def test_add_same_node_id_updates_settings(self):
        """Re-adding a node id with new settings updates its entry."""
        self.borg.add_node("node", BLESettings(tx_power_dbm=0))
        self.borg.add_node("node", BLESettings(tx_power_dbm=4))
        assert self.borg.node_count == 1
        consensus = self.borg.compute_consensus()
        assert consensus.tx_power_dbm == 4


# ---------------------------------------------------------------------------
# Canonical JSON / hash helpers
# ---------------------------------------------------------------------------

class TestCanonicalJSON:
    """Tests for _canonical_json and _sha256_c14n helpers."""

    def test_canonical_json_sorts_keys(self):
        """Keys are sorted lexicographically."""
        obj = {"z": 1, "a": 2}
        result = _canonical_json(obj).decode()
        assert result.index('"a"') < result.index('"z"')

    def test_canonical_json_no_whitespace(self):
        """Canonical JSON has no insignificant whitespace."""
        result = _canonical_json({"k": "v"}).decode()
        assert " " not in result

    def test_sha256_c14n_has_prefix(self):
        """sha256 hash has the sha256: prefix."""
        h = _sha256_c14n({"k": "v"})
        assert h.startswith(SHA256_PREFIX)

    def test_sha256_c14n_length(self):
        """sha256 hash has 64 hex chars after the prefix."""
        h = _sha256_c14n({"k": "v"})
        assert len(h) == len(SHA256_PREFIX) + 64

    def test_sha256_c14n_is_deterministic(self):
        """Same input always produces the same hash."""
        obj = {"x": 1, "y": 2}
        assert _sha256_c14n(obj) == _sha256_c14n(obj)

    def test_sha256_c14n_different_inputs(self):
        """Different inputs produce different hashes."""
        assert _sha256_c14n({"a": 1}) != _sha256_c14n({"a": 2})
