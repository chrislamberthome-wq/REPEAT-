-include make/trtl.mk

# CRC-16/CCITT-FALSE Certification Targets

.PHONY: test vectors certify verify-manifest

# Run all tests
test:
	@echo "Running CRC-16/CCITT-FALSE tests..."
	PYTHONHASHSEED=0 LC_ALL=C TZ=UTC python -m pytest tests/test_crc16_golden.py -v

# Generate golden vectors (vectors file is frozen, this validates it)
vectors:
	@echo "Validating golden vectors..."
	@python -c "import json; f=open('audit/golden/crc16_ccitt_false.vectors.json'); json.load(f); print('✓ Vectors file is valid JSON')"

# Generate and verify manifest
certify: vectors
	@echo "Generating SHA-256 manifest..."
	@PYTHONHASHSEED=0 LC_ALL=C TZ=UTC python tools/generate_manifest.py
	@echo ""
	@echo "Verifying manifest..."
	@python tools/verify_manifest.py
	@echo ""
	@echo "Running certification tests..."
	@$(MAKE) test

# Verify manifest only (fast check)
verify-manifest:
	@python tools/verify_manifest.py
