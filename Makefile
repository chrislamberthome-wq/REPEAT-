-include make/trtl.mk

# CRC-16/CCITT-FALSE Python Implementation Targets
.PHONY: crc16-py-run crc16-py-test

crc16-py-run:
	echo -n "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py

crc16-py-test:
	PYTHONPATH=. python3 -m unittest -v tests.test_crc16_golden