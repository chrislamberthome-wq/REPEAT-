# Include trtl.mk if it exists
-include make/trtl.mk

# Holo-ID v0 Test Targets
.PHONY: smoke golden verify holo-all

# Smoke test - Quick sanity check
smoke:
	@echo "Running Holo-ID v0 smoke tests..."
	@echo -n "Test 1: Encode empty data... "
	@echo -n "" | python src/verify_holo_id.py encode > /tmp/smoke_empty.json && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Test 2: Verify empty packet... "
	@python src/verify_holo_id.py verify --input /tmp/smoke_empty.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Test 3: Encode and verify 'Hello'... "
	@echo -n "Hello" | python src/verify_holo_id.py encode | python src/verify_holo_id.py verify > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Test 4: Strict verification test... "
	@echo -n "Test data" | python src/verify_holo_id.py encode | python src/verify_holo_id.py verify --strict > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo "All smoke tests passed!"

# Golden packet verification
golden:
	@echo "Verifying golden packets..."
	@echo -n "Verifying empty.json (basic)... "
	@python src/verify_holo_id.py verify --input golden/empty.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Verifying empty.json (strict)... "
	@python src/verify_holo_id.py verify --strict --input golden/empty.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Verifying single_byte.json (basic)... "
	@python src/verify_holo_id.py verify --input golden/single_byte.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Verifying single_byte.json (strict)... "
	@python src/verify_holo_id.py verify --strict --input golden/single_byte.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Verifying hello.json (basic)... "
	@python src/verify_holo_id.py verify --input golden/hello.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Verifying hello.json (strict)... "
	@python src/verify_holo_id.py verify --strict --input golden/hello.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Verifying all_bytes.json (basic)... "
	@python src/verify_holo_id.py verify --input golden/all_bytes.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo -n "Verifying all_bytes.json (strict)... "
	@python src/verify_holo_id.py verify --strict --input golden/all_bytes.json > /dev/null && echo "OK" || (echo "FAIL" && exit 1)
	@echo "All golden packets verified!"

# Full verification suite
verify: smoke golden
	@echo "Running full Holo-ID v0 verification suite..."
	@echo -n "Testing corruption detection (bitflip)... "
	@python src/verify_holo_id.py corrupt --input golden/hello.json --type bitflip --output /tmp/corrupted_bitflip.json > /dev/null
	@python src/verify_holo_id.py verify --input /tmp/corrupted_bitflip.json > /dev/null 2>&1 && (echo "FAIL - should have detected corruption" && exit 1) || echo "OK"
	@echo -n "Testing corruption detection (checksum)... "
	@python src/verify_holo_id.py corrupt --input golden/hello.json --type checksum --output /tmp/corrupted_checksum.json > /dev/null
	@python src/verify_holo_id.py verify --input /tmp/corrupted_checksum.json > /dev/null 2>&1 && (echo "FAIL - should have detected corruption" && exit 1) || echo "OK"
	@echo -n "Testing corruption detection (coordinate)... "
	@python src/verify_holo_id.py corrupt --input golden/hello.json --type coordinate --output /tmp/corrupted_coordinate.json > /dev/null
	@python src/verify_holo_id.py verify --strict --input /tmp/corrupted_coordinate.json > /dev/null 2>&1 && (echo "FAIL - should have detected corruption" && exit 1) || echo "OK"
	@echo "Full verification suite passed!"

# Run all Holo-ID v0 tests
holo-all: verify
	@echo "All Holo-ID v0 tests completed successfully!"

# Existing test target (if any)
test:
	python -m pytest tests/ -v
