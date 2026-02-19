"""Tests for the thermal resonance module."""

import pytest
from verifier.thermal_resonance import ThermalResonance


class TestThermalResonanceInit:
    """Tests for ThermalResonance initialization."""
    
    def test_init_with_dict_parameters(self):
        """Test initialization with dictionary parameters."""
        params = {"temp": 300, "frequency": 1000}
        tr = ThermalResonance(params)
        assert tr.parameters == params
    
    def test_init_with_empty_parameters(self):
        """Test initialization with empty parameters."""
        tr = ThermalResonance({})
        assert tr.parameters == {}
    
    def test_init_with_none_parameters(self):
        """Test initialization with None parameters."""
        tr = ThermalResonance(None)
        assert tr.parameters is None
    
    def test_init_with_string_parameters(self):
        """Test initialization with string parameters."""
        params = "test_params"
        tr = ThermalResonance(params)
        assert tr.parameters == params
    
    def test_init_with_numeric_parameters(self):
        """Test initialization with numeric parameters."""
        tr = ThermalResonance(42)
        assert tr.parameters == 42


class TestThermalResonanceCompute:
    """Tests for ThermalResonance compute method."""
    
    def test_compute_returns_none(self):
        """Test that compute method returns None."""
        tr = ThermalResonance({"temp": 300})
        result = tr.compute()
        assert result is None
    
    def test_compute_callable(self):
        """Test that compute method is callable."""
        tr = ThermalResonance({})
        assert callable(tr.compute)
    
    def test_compute_multiple_calls(self):
        """Test multiple calls to compute method."""
        tr = ThermalResonance({"value": 100})
        result1 = tr.compute()
        result2 = tr.compute()
        # Both should return None
        assert result1 is None
        assert result2 is None


class TestThermalResonanceIntegration:
    """Integration tests for ThermalResonance."""
    
    def test_create_and_compute_workflow(self):
        """Test typical workflow of creating instance and computing."""
        params = {"temperature": 298.15, "pressure": 101325}
        tr = ThermalResonance(params)
        
        # Verify parameters are stored
        assert tr.parameters["temperature"] == 298.15
        assert tr.parameters["pressure"] == 101325
        
        # Call compute
        result = tr.compute()
        assert result is None
    
    def test_multiple_instances(self):
        """Test creating multiple ThermalResonance instances."""
        tr1 = ThermalResonance({"id": 1})
        tr2 = ThermalResonance({"id": 2})
        
        # Instances should be independent
        assert tr1.parameters["id"] == 1
        assert tr2.parameters["id"] == 2
        assert tr1 is not tr2
    
    def test_parameters_share_reference(self):
        """Test that parameters share reference with original dict."""
        params = {"value": 10}
        tr = ThermalResonance(params)
        
        # Modify original params
        params["value"] = 20
        
        # The instance should reflect the change (same object reference)
        assert tr.parameters["value"] == 20
