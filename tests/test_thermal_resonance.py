"""Tests for thermal resonance implementation."""

import pytest
from verifier.thermal_resonance import (
    ThermalResonanceThreshold,
    classify_resonance_thermal,
    decode_thermal,
)


class TestClassifyResonanceThermal:
    """Tests for classify_resonance_thermal function with default thresholds."""
    
    def test_classify_resonance_thermal_default_thresholds(self):
        """Test classify_resonance_thermal with default thresholds (0.3, 0.7)."""
        # Test low range (< 0.3)
        assert classify_resonance_thermal(0.0) == "low"
        assert classify_resonance_thermal(0.1) == "low"
        assert classify_resonance_thermal(0.29) == "low"
        
        # Test medium range (>= 0.3 and < 0.7)
        assert classify_resonance_thermal(0.3) == "medium"
        assert classify_resonance_thermal(0.5) == "medium"
        assert classify_resonance_thermal(0.69) == "medium"
        
        # Test high range (>= 0.7)
        assert classify_resonance_thermal(0.7) == "high"
        assert classify_resonance_thermal(0.9) == "high"
        assert classify_resonance_thermal(1.0) == "high"
    
    def test_classify_resonance_thermal_custom_thresholds(self):
        """Test classify_resonance_thermal with custom thresholds."""
        # Custom thresholds: low=0.2, high=0.8
        assert classify_resonance_thermal(0.1, 0.2, 0.8) == "low"
        assert classify_resonance_thermal(0.5, 0.2, 0.8) == "medium"
        assert classify_resonance_thermal(0.9, 0.2, 0.8) == "high"
    
    def test_classify_resonance_thermal_boundary_cases(self):
        """Test boundary values with default thresholds."""
        # Exact boundary values
        assert classify_resonance_thermal(0.3) == "medium"
        assert classify_resonance_thermal(0.7) == "high"
        
        # Just below boundaries
        assert classify_resonance_thermal(0.2999999) == "low"
        assert classify_resonance_thermal(0.6999999) == "medium"


class TestDecodeThermal:
    """Tests for decode_thermal function."""
    
    def test_decode_thermal_truthiness(self):
        """Test decode_thermal for truthiness with default threshold (0.5)."""
        # Test False cases (< 0.5)
        assert decode_thermal(0.0) == False
        assert decode_thermal(0.1) == False
        assert decode_thermal(0.3) == False
        assert decode_thermal(0.49) == False
        
        # Test True cases (>= 0.5)
        assert decode_thermal(0.5) == True
        assert decode_thermal(0.6) == True
        assert decode_thermal(0.9) == True
        assert decode_thermal(1.0) == True
    
    def test_decode_thermal_custom_threshold(self):
        """Test decode_thermal with custom threshold."""
        # Custom threshold 0.7
        assert decode_thermal(0.6, threshold=0.7) == False
        assert decode_thermal(0.7, threshold=0.7) == True
        assert decode_thermal(0.8, threshold=0.7) == True
    
    def test_decode_thermal_boundary_cases(self):
        """Test boundary values with default threshold."""
        # Exact threshold value should be True
        assert decode_thermal(0.5) == True
        # Just below should be False
        assert decode_thermal(0.4999999) == False


class TestThermalResonanceThreshold:
    """Tests for ThermalResonanceThreshold class."""
    
    def test_init_default_thresholds(self):
        """Test initialization with default thresholds."""
        classifier = ThermalResonanceThreshold()
        assert classifier.low_threshold == 0.3
        assert classifier.high_threshold == 0.7
    
    def test_init_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        classifier = ThermalResonanceThreshold(0.2, 0.8)
        assert classifier.low_threshold == 0.2
        assert classifier.high_threshold == 0.8
    
    def test_init_invalid_thresholds(self):
        """Test that invalid thresholds raise ValueError."""
        with pytest.raises(ValueError):
            ThermalResonanceThreshold(0.7, 0.3)  # low >= high
        
        with pytest.raises(ValueError):
            ThermalResonanceThreshold(0.5, 0.5)  # low == high
    
    def test_classify_low(self):
        """Test classification of low values."""
        classifier = ThermalResonanceThreshold()
        assert classifier.classify(0.0) == "low"
        assert classifier.classify(0.2) == "low"
        assert classifier.classify(0.29) == "low"
    
    def test_classify_medium(self):
        """Test classification of medium values."""
        classifier = ThermalResonanceThreshold()
        assert classifier.classify(0.3) == "medium"
        assert classifier.classify(0.5) == "medium"
        assert classifier.classify(0.69) == "medium"
    
    def test_classify_high(self):
        """Test classification of high values."""
        classifier = ThermalResonanceThreshold()
        assert classifier.classify(0.7) == "high"
        assert classifier.classify(0.9) == "high"
        assert classifier.classify(1.0) == "high"
