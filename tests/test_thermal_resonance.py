"""Tests for thermal resonance pilot implementation."""

import pytest
from verifier.thermal_resonance import (
    ThermalResonanceThreshold,
    classify_resonance_thermal,
    decode_thermal,
    ThermalResonance,
)


class TestThermalResonanceThreshold:
    """Tests for ThermalResonanceThreshold class."""
    
    def test_threshold_initialization(self):
        """Test threshold initialization with valid values."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        assert threshold.min_threshold == 10.0
        assert threshold.max_threshold == 20.0
    
    def test_threshold_invalid_range(self):
        """Test threshold initialization fails with invalid range."""
        with pytest.raises(ValueError, match="min_threshold must be less than max_threshold"):
            ThermalResonanceThreshold(min_threshold=20.0, max_threshold=10.0)
    
    def test_threshold_equal_values(self):
        """Test threshold initialization fails when min equals max."""
        with pytest.raises(ValueError, match="min_threshold must be less than max_threshold"):
            ThermalResonanceThreshold(min_threshold=15.0, max_threshold=15.0)
    
    def test_threshold_negative_values(self):
        """Test threshold initialization with negative values."""
        threshold = ThermalResonanceThreshold(min_threshold=-20.0, max_threshold=-10.0)
        assert threshold.min_threshold == -20.0
        assert threshold.max_threshold == -10.0


class TestClassifyResonanceThermal:
    """Tests for classify_resonance_thermal function."""
    
    def test_classify_below_min_threshold(self):
        """Test classification returns 0 for values below min threshold."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        assert classify_resonance_thermal(5.0, threshold) == 0
        assert classify_resonance_thermal(0.0, threshold) == 0
        assert classify_resonance_thermal(9.9, threshold) == 0
    
    def test_classify_above_max_threshold(self):
        """Test classification returns 1 for values above max threshold."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        assert classify_resonance_thermal(25.0, threshold) == 1
        assert classify_resonance_thermal(20.1, threshold) == 1
        assert classify_resonance_thermal(100.0, threshold) == 1
    
    def test_classify_within_threshold_range(self):
        """Test classification returns None for values within threshold range."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        assert classify_resonance_thermal(10.0, threshold) is None
        assert classify_resonance_thermal(15.0, threshold) is None
        assert classify_resonance_thermal(20.0, threshold) is None
    
    def test_classify_boundary_conditions(self):
        """Test classification at exact boundary values."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        # At min threshold - should be indeterminate
        assert classify_resonance_thermal(10.0, threshold) is None
        
        # Just below min threshold - should be 0
        assert classify_resonance_thermal(9.999, threshold) == 0
        
        # At max threshold - should be indeterminate
        assert classify_resonance_thermal(20.0, threshold) is None
        
        # Just above max threshold - should be 1
        assert classify_resonance_thermal(20.001, threshold) == 1
    
    def test_classify_negative_values(self):
        """Test classification with negative threshold values."""
        threshold = ThermalResonanceThreshold(min_threshold=-20.0, max_threshold=-10.0)
        
        assert classify_resonance_thermal(-25.0, threshold) == 0
        assert classify_resonance_thermal(-15.0, threshold) is None
        assert classify_resonance_thermal(-5.0, threshold) == 1
    
    def test_classify_very_small_threshold_range(self):
        """Test classification with very small threshold range."""
        threshold = ThermalResonanceThreshold(min_threshold=0.001, max_threshold=0.002)
        
        assert classify_resonance_thermal(0.0005, threshold) == 0
        assert classify_resonance_thermal(0.0015, threshold) is None
        assert classify_resonance_thermal(0.0025, threshold) == 1


class TestDecodeThermal:
    """Tests for decode_thermal function."""
    
    def test_decode_below_min_threshold(self):
        """Test decode returns 0 for values below min threshold."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        assert decode_thermal(5.0, threshold) == 0
        assert decode_thermal(0.0, threshold) == 0
    
    def test_decode_above_max_threshold(self):
        """Test decode returns 1 for values above max threshold."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        assert decode_thermal(25.0, threshold) == 1
        assert decode_thermal(100.0, threshold) == 1
    
    def test_decode_within_threshold_range(self):
        """Test decode returns None for values within threshold range."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        assert decode_thermal(15.0, threshold) is None
    
    def test_decode_consistency_with_classifier(self):
        """Test that decode_thermal produces same results as classify_resonance_thermal."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        test_values = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 100.0]
        
        for value in test_values:
            decoded = decode_thermal(value, threshold)
            classified = classify_resonance_thermal(value, threshold)
            assert decoded == classified, f"Mismatch at value {value}"


class TestThermalResonance:
    """Tests for ThermalResonance class (legacy interface)."""
    
    def test_initialization(self):
        """Test ThermalResonance initialization."""
        params = {"min_threshold": 10.0, "max_threshold": 20.0}
        resonance = ThermalResonance(params)
        
        assert resonance.parameters == params
    
    def test_compute_returns_none(self):
        """Test compute method returns None (placeholder)."""
        params = {"min_threshold": 10.0, "max_threshold": 20.0}
        resonance = ThermalResonance(params)
        
        result = resonance.compute()
        assert result is None


class TestIntegration:
    """Integration tests for thermal resonance system."""
    
    def test_full_classification_pipeline(self):
        """Test complete classification pipeline with multiple values."""
        threshold = ThermalResonanceThreshold(min_threshold=100.0, max_threshold=200.0)
        
        test_cases = [
            (50.0, 0),      # Below min
            (99.9, 0),      # Just below min
            (100.0, None),  # At min
            (150.0, None),  # Middle
            (200.0, None),  # At max
            (200.1, 1),     # Just above max
            (250.0, 1),     # Above max
        ]
        
        for value, expected in test_cases:
            result = decode_thermal(value, threshold)
            assert result == expected, f"Failed for value {value}: expected {expected}, got {result}"
    
    def test_multiple_threshold_configurations(self):
        """Test with multiple different threshold configurations."""
        configurations = [
            (0.0, 1.0),
            (10.0, 20.0),
            (100.0, 200.0),
            (-50.0, 50.0),
        ]
        
        for min_t, max_t in configurations:
            threshold = ThermalResonanceThreshold(min_threshold=min_t, max_threshold=max_t)
            
            # Test below
            assert classify_resonance_thermal(min_t - 1.0, threshold) == 0
            
            # Test within
            assert classify_resonance_thermal((min_t + max_t) / 2, threshold) is None
            
            # Test above
            assert classify_resonance_thermal(max_t + 1.0, threshold) == 1
    
    def test_edge_cases(self):
        """Test edge cases and special values."""
        threshold = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        
        # Test with very large values
        assert decode_thermal(1e10, threshold) == 1
        
        # Test with very small values
        assert decode_thermal(-1e10, threshold) == 0
        
        # Test with zero
        assert decode_thermal(0.0, threshold) == 0
    
    def test_threshold_symmetry(self):
        """Test that threshold behavior is symmetric around zero."""
        threshold_pos = ThermalResonanceThreshold(min_threshold=10.0, max_threshold=20.0)
        threshold_neg = ThermalResonanceThreshold(min_threshold=-20.0, max_threshold=-10.0)
        
        # Positive side
        assert classify_resonance_thermal(5.0, threshold_pos) == 0
        assert classify_resonance_thermal(25.0, threshold_pos) == 1
        
        # Negative side (reversed due to symmetry)
        assert classify_resonance_thermal(-25.0, threshold_neg) == 0
        assert classify_resonance_thermal(-5.0, threshold_neg) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
