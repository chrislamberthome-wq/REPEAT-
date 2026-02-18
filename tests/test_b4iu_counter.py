"""Tests for the B4IU (Before-In-Use) locked counter and spec rule."""

import pytest
from repeat_hd.cli import B4IULockedCounter


class TestB4IULockedCounter:
    """Tests for B4IULockedCounter class."""
    
    def test_counter_initial_state(self):
        """Test counter starts at zero and unlocked."""
        counter = B4IULockedCounter()
        assert counter.get_count() == 0
        assert not counter.is_locked()
        assert len(counter.get_violations()) == 0
    
    def test_counter_increment(self):
        """Test counter can be incremented."""
        counter = B4IULockedCounter()
        result = counter.increment()
        assert result is True
        assert counter.get_count() == 1
    
    def test_counter_multiple_increments(self):
        """Test counter can be incremented multiple times."""
        counter = B4IULockedCounter()
        for i in range(5):
            result = counter.increment()
            assert result is True
            assert counter.get_count() == i + 1
    
    def test_counter_lock(self):
        """Test counter can be locked."""
        counter = B4IULockedCounter()
        counter.lock()
        assert counter.is_locked()
    
    def test_counter_locked_prevents_increment(self):
        """Test locked counter cannot be incremented."""
        counter = B4IULockedCounter()
        counter.increment()
        counter.lock()
        
        result = counter.increment()
        assert result is False
        assert counter.get_count() == 1
        assert counter.is_locked()
    
    def test_counter_locked_records_violation(self):
        """Test attempting to increment locked counter records violation."""
        counter = B4IULockedCounter()
        counter.lock()
        counter.increment()
        
        violations = counter.get_violations()
        assert len(violations) == 1
        assert "locked counter" in violations[0].lower()
    
    def test_counter_multiple_violations(self):
        """Test multiple violation attempts are recorded."""
        counter = B4IULockedCounter()
        counter.lock()
        
        for _ in range(3):
            counter.increment()
        
        violations = counter.get_violations()
        assert len(violations) == 3


class TestSpecRule:
    """Tests for spec rule compliance checking."""
    
    def test_spec_rule_unlocked_counter_valid(self):
        """Test unlocked counter passes spec rule."""
        counter = B4IULockedCounter()
        counter.increment()
        
        is_valid, error = counter.check_spec_rule(min_required=1)
        assert is_valid
        assert error is None
    
    def test_spec_rule_locked_with_sufficient_count(self):
        """Test locked counter with sufficient count passes spec rule."""
        counter = B4IULockedCounter()
        counter.increment()
        counter.lock()
        
        is_valid, error = counter.check_spec_rule(min_required=1)
        assert is_valid
        assert error is None
    
    def test_spec_rule_locked_with_insufficient_count(self):
        """Test locked counter with insufficient count fails spec rule."""
        counter = B4IULockedCounter()
        counter.lock()  # Lock without incrementing
        
        is_valid, error = counter.check_spec_rule(min_required=1)
        assert not is_valid
        assert error is not None
        assert "spec rule violation" in error.lower()
        assert "count=0" in error
        assert "required>=1" in error
    
    def test_spec_rule_custom_minimum(self):
        """Test spec rule with custom minimum requirement."""
        counter = B4IULockedCounter()
        counter.increment()
        counter.increment()
        counter.lock()
        
        # Should pass with min_required=2
        is_valid, error = counter.check_spec_rule(min_required=2)
        assert is_valid
        assert error is None
        
        # Create another counter with only 1 increment
        counter2 = B4IULockedCounter()
        counter2.increment()
        counter2.lock()
        
        # Should fail with min_required=2
        is_valid, error = counter2.check_spec_rule(min_required=2)
        assert not is_valid
        assert error is not None
    
    def test_spec_rule_zero_minimum(self):
        """Test spec rule with zero minimum (always passes when locked)."""
        counter = B4IULockedCounter()
        counter.lock()  # Lock without incrementing
        
        is_valid, error = counter.check_spec_rule(min_required=0)
        assert is_valid
        assert error is None
    
    def test_spec_rule_high_minimum(self):
        """Test spec rule with high minimum requirement."""
        counter = B4IULockedCounter()
        for _ in range(10):
            counter.increment()
        counter.lock()
        
        is_valid, error = counter.check_spec_rule(min_required=10)
        assert is_valid
        assert error is None
        
        is_valid, error = counter.check_spec_rule(min_required=11)
        assert not is_valid
        assert "count=10" in error
        assert "required>=11" in error


class TestB4IUIntegration:
    """Integration tests for B4IU counter usage patterns."""
    
    def test_typical_verification_workflow(self):
        """Test typical verification workflow with counter."""
        counter = B4IULockedCounter()
        
        # Start verification
        counter.increment()
        assert counter.get_count() == 1
        
        # Perform checks
        counter.increment()
        assert counter.get_count() == 2
        
        # Complete verification
        counter.lock()
        assert counter.is_locked()
        
        # Verify spec rule compliance
        is_valid, error = counter.check_spec_rule(min_required=2)
        assert is_valid
        assert error is None
    
    def test_failed_verification_workflow(self):
        """Test verification workflow that fails early."""
        counter = B4IULockedCounter()
        
        # Start verification
        counter.increment()
        
        # Verification fails, lock immediately
        counter.lock()
        
        # Should still meet minimum spec rule (at least 1 operation)
        is_valid, error = counter.check_spec_rule(min_required=1)
        assert is_valid
    
    def test_strict_mode_workflow(self):
        """Test verification workflow with strict mode enabled."""
        counter = B4IULockedCounter()
        
        # Basic verification
        counter.increment()
        
        # Strict mode additional checks
        counter.increment()
        
        # Lock after all checks
        counter.lock()
        
        # Verify higher spec rule requirement for strict mode
        is_valid, error = counter.check_spec_rule(min_required=2)
        assert is_valid
    
    def test_counter_immutability_after_lock(self):
        """Test that locked counter state is immutable."""
        counter = B4IULockedCounter()
        counter.increment()
        counter.increment()
        counter.lock()
        
        initial_count = counter.get_count()
        initial_locked = counter.is_locked()
        
        # Try to modify
        counter.increment()
        counter.increment()
        
        # State should not change
        assert counter.get_count() == initial_count
        assert counter.is_locked() == initial_locked
        
        # But violations should be recorded
        assert len(counter.get_violations()) == 2
    
    def test_violations_isolation(self):
        """Test that violations list is isolated per counter."""
        counter1 = B4IULockedCounter()
        counter2 = B4IULockedCounter()
        
        counter1.lock()
        counter1.increment()
        
        # counter1 should have violation, counter2 should not
        assert len(counter1.get_violations()) == 1
        assert len(counter2.get_violations()) == 0
    
    def test_get_violations_returns_copy(self):
        """Test that get_violations returns a copy, not the original list."""
        counter = B4IULockedCounter()
        counter.lock()
        counter.increment()
        
        violations1 = counter.get_violations()
        violations2 = counter.get_violations()
        
        # Should be equal but not the same object
        assert violations1 == violations2
        assert violations1 is not violations2
        
        # Modifying returned list shouldn't affect counter
        violations1.append("external modification")
        violations3 = counter.get_violations()
        assert len(violations3) == 1
        assert "external modification" not in violations3
