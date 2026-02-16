# CRC-16/CCITT-FALSE Repro (LOCK v1.1)

Golden payload:
- payload_utf8: `F0|ABC|3|1`
- expected CRC16/CCITT-FALSE: `0x34B6`

## Python mirror (newline-safe)
```bash
printf "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
python3 tools/crc16_ccitt_false.py --payload "F0|ABC|3|1" --expect 0x34B6
```

## Python tests

```bash
PYTHONPATH=. python3 -m unittest -v tests.test_crc16_golden tests.test_crc16_cli_parity
```
