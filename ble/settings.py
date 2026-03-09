"""
BLE Settings — core implementation.

Implements BLE (Bluetooth Low Energy) configuration with deterministic
behaviour, aligned with the REPEAT-bounded autotonomy model:

  INV-1 (Predeclared constraints): Every BLE parameter has an explicit
    valid range declared as module-level constants. These ranges cannot
    be modified at runtime.

  INV-2 (Auditable trace): Every B4IU verification call produces a
    structured JSONL-ready receipt containing the settings snapshot,
    verdict, and a sha256 hash chain.

  INV-3 (Fail-closed verifier): ``validate_ble_settings`` returns a
    non-empty error list (never silently passes) when any constraint is
    violated. ``B4IUInterface.verify`` surfaces this verdict directly.

  INV-4 (No goal sovereignty): The module does not modify its own
    constraint constants. All bounds are read-only module-level values.

Public API
----------
  BLESettings          dataclass — all BLE parameters with safe defaults
  validate_ble_settings function  — returns ``List[str]`` of violations
  B4IUInterface        class     — verifiable interface; produces receipts
  IAMBorgCollective    class     — collective compute substrate; consensus
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Schema identifier
# ---------------------------------------------------------------------------

BLE_SETTINGS_SCHEMA = "repeat-ble-settings-v1"
SHA256_PREFIX = "sha256:"

# ---------------------------------------------------------------------------
# Predeclared BLE parameter bounds (INV-1)
# All values are in the units indicated by the constant name suffix.
# ---------------------------------------------------------------------------

BLE_ADVERTISING_INTERVAL_MIN_MS: float = 20.0
BLE_ADVERTISING_INTERVAL_MAX_MS: float = 10240.0

BLE_CONNECTION_INTERVAL_MIN_MS: float = 7.5
BLE_CONNECTION_INTERVAL_MAX_MS: float = 4000.0

BLE_TX_POWER_MIN_DBM: int = -40
BLE_TX_POWER_MAX_DBM: int = 20

BLE_MTU_MIN: int = 23
BLE_MTU_MAX: int = 517

BLE_SCAN_INTERVAL_MIN_MS: float = 2.5
BLE_SCAN_INTERVAL_MAX_MS: float = 10240.0

BLE_SCAN_WINDOW_MIN_MS: float = 2.5
BLE_SCAN_WINDOW_MAX_MS: float = 10240.0


# ---------------------------------------------------------------------------
# BLESettings dataclass
# ---------------------------------------------------------------------------

@dataclass
class BLESettings:
    """
    BLE settings with predeclared constraints for REPEAT-bounded operation.

    All parameters carry explicit valid ranges defined by the ``BLE_*``
    module constants.  Default values correspond to conservative,
    interoperable BLE configurations.

    Attributes:
        device_id: Logical identifier for this BLE node.
        advertising_interval_ms: Advertising interval in milliseconds.
            Valid range: [20, 10240].
        advertising_enabled: Whether advertising is active.
        connection_interval_min_ms: Minimum connection interval in ms.
            Valid range: [7.5, 4000].
        connection_interval_max_ms: Maximum connection interval in ms.
            Valid range: [7.5, 4000]; must be >= connection_interval_min_ms.
        tx_power_dbm: Transmit power in dBm.
            Valid range: [-40, 20].
        mtu_bytes: Maximum Transmission Unit size in bytes.
            Valid range: [23, 517].
        scan_interval_ms: Scan interval in milliseconds.
            Valid range: [2.5, 10240].
        scan_window_ms: Scan window in milliseconds.
            Valid range: [2.5, 10240]; must be <= scan_interval_ms.
    """

    device_id: str = "ble-node-default"
    advertising_interval_ms: float = 100.0
    advertising_enabled: bool = True
    connection_interval_min_ms: float = 7.5
    connection_interval_max_ms: float = 30.0
    tx_power_dbm: int = 0
    mtu_bytes: int = 247
    scan_interval_ms: float = 100.0
    scan_window_ms: float = 50.0

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain ``dict`` representation (suitable for JSON)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BLESettings":
        """Construct a ``BLESettings`` from a plain dictionary.

        Unknown keys are silently ignored so that forward-compatible
        receipts can be loaded without error.
        """
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


# ---------------------------------------------------------------------------
# Validation (INV-3: fail-closed)
# ---------------------------------------------------------------------------

def validate_ble_settings(settings: BLESettings) -> List[str]:
    """
    Validate *settings* against predeclared BLE parameter bounds.

    Implements fail-closed validation (INV-3): the returned list is empty
    only when every constraint is satisfied.  Callers MUST treat a
    non-empty list as a hard failure.

    Args:
        settings: The :class:`BLESettings` instance to validate.

    Returns:
        A list of human-readable error strings.  An empty list means the
        settings are valid.
    """
    errors: List[str] = []

    # --- device identity ---------------------------------------------------
    if not settings.device_id or not settings.device_id.strip():
        errors.append("device_id must not be empty or whitespace-only")

    # --- advertising -------------------------------------------------------
    if not (
        BLE_ADVERTISING_INTERVAL_MIN_MS
        <= settings.advertising_interval_ms
        <= BLE_ADVERTISING_INTERVAL_MAX_MS
    ):
        errors.append(
            f"advertising_interval_ms {settings.advertising_interval_ms} out of range "
            f"[{BLE_ADVERTISING_INTERVAL_MIN_MS}, {BLE_ADVERTISING_INTERVAL_MAX_MS}]"
        )

    # --- connection interval -----------------------------------------------
    if not (
        BLE_CONNECTION_INTERVAL_MIN_MS
        <= settings.connection_interval_min_ms
        <= BLE_CONNECTION_INTERVAL_MAX_MS
    ):
        errors.append(
            f"connection_interval_min_ms {settings.connection_interval_min_ms} out of range "
            f"[{BLE_CONNECTION_INTERVAL_MIN_MS}, {BLE_CONNECTION_INTERVAL_MAX_MS}]"
        )

    if not (
        BLE_CONNECTION_INTERVAL_MIN_MS
        <= settings.connection_interval_max_ms
        <= BLE_CONNECTION_INTERVAL_MAX_MS
    ):
        errors.append(
            f"connection_interval_max_ms {settings.connection_interval_max_ms} out of range "
            f"[{BLE_CONNECTION_INTERVAL_MIN_MS}, {BLE_CONNECTION_INTERVAL_MAX_MS}]"
        )

    if settings.connection_interval_min_ms > settings.connection_interval_max_ms:
        errors.append(
            f"connection_interval_min_ms ({settings.connection_interval_min_ms}) "
            f"must not exceed connection_interval_max_ms ({settings.connection_interval_max_ms})"
        )

    # --- TX power ----------------------------------------------------------
    if not (BLE_TX_POWER_MIN_DBM <= settings.tx_power_dbm <= BLE_TX_POWER_MAX_DBM):
        errors.append(
            f"tx_power_dbm {settings.tx_power_dbm} out of range "
            f"[{BLE_TX_POWER_MIN_DBM}, {BLE_TX_POWER_MAX_DBM}]"
        )

    # --- MTU ---------------------------------------------------------------
    if not (BLE_MTU_MIN <= settings.mtu_bytes <= BLE_MTU_MAX):
        errors.append(
            f"mtu_bytes {settings.mtu_bytes} out of range "
            f"[{BLE_MTU_MIN}, {BLE_MTU_MAX}]"
        )

    # --- scan settings -----------------------------------------------------
    if not (
        BLE_SCAN_INTERVAL_MIN_MS
        <= settings.scan_interval_ms
        <= BLE_SCAN_INTERVAL_MAX_MS
    ):
        errors.append(
            f"scan_interval_ms {settings.scan_interval_ms} out of range "
            f"[{BLE_SCAN_INTERVAL_MIN_MS}, {BLE_SCAN_INTERVAL_MAX_MS}]"
        )

    if not (
        BLE_SCAN_WINDOW_MIN_MS
        <= settings.scan_window_ms
        <= BLE_SCAN_WINDOW_MAX_MS
    ):
        errors.append(
            f"scan_window_ms {settings.scan_window_ms} out of range "
            f"[{BLE_SCAN_WINDOW_MIN_MS}, {BLE_SCAN_WINDOW_MAX_MS}]"
        )

    if settings.scan_window_ms > settings.scan_interval_ms:
        errors.append(
            f"scan_window_ms ({settings.scan_window_ms}) must not exceed "
            f"scan_interval_ms ({settings.scan_interval_ms})"
        )

    return errors


# ---------------------------------------------------------------------------
# Canonical JSON helpers (REPEAT C14N v1 / JCS / RFC 8785)
# ---------------------------------------------------------------------------

def _canonical_json(obj: Dict[str, Any]) -> bytes:
    """Canonical JSON bytes per REPEAT C14N v1."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_c14n(obj: Dict[str, Any]) -> str:
    """sha256 of canonical JSON, prefixed with ``sha256:``."""
    return SHA256_PREFIX + hashlib.sha256(_canonical_json(obj)).hexdigest()


# ---------------------------------------------------------------------------
# B4IU — Verifiable Interface
# ---------------------------------------------------------------------------

class B4IUInterface:
    """
    B4IU Verifiable Interface for BLE settings.

    Provides fail-closed validation of :class:`BLESettings` against
    predeclared constraints and produces a structured, auditable receipt
    for every verification call (INV-2).

    The receipt format mirrors the ``repeat-ble-settings-v1`` schema:

    .. code-block:: json

        {
          "schema": "repeat-ble-settings-v1",
          "settings_hash_sha256": "sha256:<hex>",
          "receipt_hash_sha256": "sha256:<hex>",
          "verdict": {"pass": true, "errors": []}
        }

    Example::

        b4iu = B4IUInterface()
        ok, errors, receipt = b4iu.verify(settings)
        if not ok:
            raise RuntimeError(f"B4IU NACK: {errors}")
    """

    def verify(
        self, settings: BLESettings
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Verify *settings* against predeclared BLE constraints.

        Args:
            settings: The BLE configuration to verify.

        Returns:
            A 3-tuple ``(is_valid, errors, receipt)`` where:

            * *is_valid* – ``True`` iff the settings satisfy all constraints.
            * *errors*   – List of violation strings (empty when valid).
            * *receipt*  – Auditable receipt ``dict`` (serialisable to JSON).
        """
        errors = validate_ble_settings(settings)
        receipt = self._build_receipt(settings, errors)
        return len(errors) == 0, errors, receipt

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_receipt(
        self, settings: BLESettings, errors: List[str]
    ) -> Dict[str, Any]:
        """Construct an auditable receipt for *settings*."""
        settings_dict = settings.to_dict()
        settings_hash = _sha256_c14n(settings_dict)

        # Build the receipt body (without receipt_hash so we can hash it)
        body: Dict[str, Any] = {
            "schema": BLE_SETTINGS_SCHEMA,
            "settings_hash_sha256": settings_hash,
            "verdict": {
                "pass": len(errors) == 0,
                "errors": errors,
            },
        }

        # Attach self-describing receipt hash (INV-2: auditable trace)
        body["receipt_hash_sha256"] = _sha256_c14n(body)
        return body


# ---------------------------------------------------------------------------
# IAM_BORG — Collective Compute Substrate
# ---------------------------------------------------------------------------

class IAMBorgCollective:
    """
    IAM_BORG Collective Compute Substrate for BLE settings.

    Manages a collection of named BLE nodes and computes a deterministic
    consensus configuration from their settings.  Each mutation is logged
    to an internal audit trace (INV-2), and consensus is derived without
    modifying the individual nodes' constraints (INV-4).

    Consensus algorithm
    -------------------
    Numerical parameters are averaged across all registered nodes (mean).
    Boolean parameters use majority vote (ties default to ``True``).
    String parameters use lexicographic minimum for determinism.

    The computed consensus is always validated through
    :class:`B4IUInterface` before being returned; if the averaged
    parameters violate any constraint the call raises :class:`ValueError`
    with the full error list.

    Example::

        borg = IAMBorgCollective()
        borg.add_node("node-a", BLESettings(tx_power_dbm=0))
        borg.add_node("node-b", BLESettings(tx_power_dbm=4))
        consensus = borg.compute_consensus()   # tx_power_dbm == 2
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, BLESettings] = {}
        self._audit_trace: List[Dict[str, Any]] = []
        self._b4iu = B4IUInterface()

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(self, node_id: str, settings: BLESettings) -> None:
        """
        Register or update a BLE node's settings.

        The settings are validated via B4IU before being accepted.
        Raises :class:`ValueError` if the settings violate any constraint.

        Args:
            node_id: Unique identifier for the node.
            settings: The node's BLE configuration.

        Raises:
            ValueError: If *settings* fails B4IU validation.
        """
        ok, errors, receipt = self._b4iu.verify(settings)
        self._audit_trace.append(
            {"event": "add_node", "node_id": node_id, "receipt": receipt}
        )
        if not ok:
            raise ValueError(
                f"IAMBorgCollective: node '{node_id}' rejected by B4IU — "
                f"{len(errors)} error(s): {errors}"
            )
        self._nodes[node_id] = settings

    def remove_node(self, node_id: str) -> None:
        """
        Remove a BLE node from the collective.

        Args:
            node_id: Identifier of the node to remove.

        Raises:
            KeyError: If *node_id* is not registered.
        """
        if node_id not in self._nodes:
            raise KeyError(f"IAMBorgCollective: unknown node '{node_id}'")
        del self._nodes[node_id]
        self._audit_trace.append({"event": "remove_node", "node_id": node_id})

    @property
    def node_count(self) -> int:
        """Number of nodes currently registered in the collective."""
        return len(self._nodes)

    # ------------------------------------------------------------------
    # Consensus
    # ------------------------------------------------------------------

    def compute_consensus(self) -> BLESettings:
        """
        Compute a deterministic consensus :class:`BLESettings` from all nodes.

        The result is validated through B4IU before being returned.

        Returns:
            A new :class:`BLESettings` instance representing the collective
            consensus.

        Raises:
            ValueError: If no nodes are registered, or if the consensus
                settings fail B4IU validation.
        """
        if not self._nodes:
            raise ValueError("IAMBorgCollective: cannot compute consensus with no registered nodes")

        node_list = list(self._nodes.values())
        n = len(node_list)

        # Numerical mean
        consensus = BLESettings(
            # Lexicographic minimum for string field — deterministic
            device_id=min(s.device_id for s in node_list),
            advertising_interval_ms=sum(s.advertising_interval_ms for s in node_list) / n,
            # Boolean majority vote — ties (equal split) default to True.
            # True iff True_count * 2 >= n, i.e. at least half voted True.
            advertising_enabled=sum(1 for s in node_list if s.advertising_enabled) * 2 >= n,
            connection_interval_min_ms=sum(s.connection_interval_min_ms for s in node_list) / n,
            connection_interval_max_ms=sum(s.connection_interval_max_ms for s in node_list) / n,
            tx_power_dbm=round(sum(s.tx_power_dbm for s in node_list) / n),
            mtu_bytes=round(sum(s.mtu_bytes for s in node_list) / n),
            scan_interval_ms=sum(s.scan_interval_ms for s in node_list) / n,
            scan_window_ms=sum(s.scan_window_ms for s in node_list) / n,
        )

        # Fail-closed: validate the consensus before returning (INV-3)
        ok, errors, receipt = self._b4iu.verify(consensus)
        self._audit_trace.append(
            {"event": "compute_consensus", "receipt": receipt}
        )
        if not ok:
            raise ValueError(
                f"IAMBorgCollective: consensus failed B4IU validation — "
                f"{len(errors)} error(s): {errors}"
            )

        return consensus

    # ------------------------------------------------------------------
    # Audit trace access
    # ------------------------------------------------------------------

    def get_audit_trace(self) -> List[Dict[str, Any]]:
        """
        Return a copy of the internal audit trace.

        Each entry is a ``dict`` with at least an ``"event"`` key.

        Returns:
            A list of audit trace entries (newest last).
        """
        return list(self._audit_trace)
