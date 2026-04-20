"""
BLE (Bluetooth Low Energy) Settings Module — REPEAT-Bounded Autotonomy

This package implements BLE settings with deterministic behaviour and
integration with:
  - B4IU (verifiable interface) — fail-closed constraint validation
  - IAM_BORG (collective compute substrate) — deterministic node consensus

Exported surface:

  BLESettings          — dataclass holding all BLE parameters
  validate_ble_settings — validate settings against predeclared bounds
  B4IUInterface        — verifiable interface (produces auditable receipts)
  IAMBorgCollective    — collective compute substrate (consensus over nodes)
  BLE_SETTINGS_SCHEMA  — schema identifier string

Usage example::

    from ble import BLESettings, B4IUInterface, IAMBorgCollective

    settings = BLESettings(device_id="node-01", tx_power_dbm=4)
    b4iu = B4IUInterface()
    ok, errors, receipt = b4iu.verify(settings)

    borg = IAMBorgCollective()
    borg.add_node("node-01", settings)
    consensus = borg.compute_consensus()
"""

from ble.settings import (
    BLESettings,
    validate_ble_settings,
    B4IUInterface,
    IAMBorgCollective,
    BLE_SETTINGS_SCHEMA,
    # BLE parameter bounds — exposed so callers can reference without hard-coding
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

__all__ = [
    "BLESettings",
    "validate_ble_settings",
    "B4IUInterface",
    "IAMBorgCollective",
    "BLE_SETTINGS_SCHEMA",
    "BLE_ADVERTISING_INTERVAL_MIN_MS",
    "BLE_ADVERTISING_INTERVAL_MAX_MS",
    "BLE_CONNECTION_INTERVAL_MIN_MS",
    "BLE_CONNECTION_INTERVAL_MAX_MS",
    "BLE_TX_POWER_MIN_DBM",
    "BLE_TX_POWER_MAX_DBM",
    "BLE_MTU_MIN",
    "BLE_MTU_MAX",
    "BLE_SCAN_INTERVAL_MIN_MS",
    "BLE_SCAN_INTERVAL_MAX_MS",
    "BLE_SCAN_WINDOW_MIN_MS",
    "BLE_SCAN_WINDOW_MAX_MS",
]
