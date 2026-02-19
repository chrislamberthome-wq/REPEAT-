"""Thermal Resonance Implementation - Threshold-based Classification."""

from typing import Optional


class ThermalResonanceThreshold:
    """
    Threshold-based thermal resonance classifier.
    
    Classifies thermal resonance values based on configurable thresholds.
    """
    
    def __init__(self, low_threshold: float = 0.3, high_threshold: float = 0.7):
        """
        Initialize the thermal resonance classifier with thresholds.
        
        Args:
            low_threshold: Lower threshold for classification (default: 0.3)
            high_threshold: Upper threshold for classification (default: 0.7)
        """
        if low_threshold >= high_threshold:
            raise ValueError("low_threshold must be less than high_threshold")
        
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
    
    def classify(self, value: float) -> str:
        """
        Classify a thermal resonance value based on thresholds.
        
        Args:
            value: Thermal resonance value to classify
            
        Returns:
            Classification string: "low", "medium", or "high"
        """
        if value < self.low_threshold:
            return "low"
        elif value < self.high_threshold:
            return "medium"
        else:
            return "high"


def classify_resonance_thermal(value: float, 
                               low_threshold: float = 0.3, 
                               high_threshold: float = 0.7) -> str:
    """
    Classify thermal resonance value using threshold-based classification.
    
    This is a convenience function that creates a classifier and classifies
    the value in one step.
    
    Args:
        value: Thermal resonance value to classify
        low_threshold: Lower threshold for classification (default: 0.3)
        high_threshold: Upper threshold for classification (default: 0.7)
        
    Returns:
        Classification string: "low", "medium", or "high"
    """
    classifier = ThermalResonanceThreshold(low_threshold, high_threshold)
    return classifier.classify(value)


def decode_thermal(value: float, 
                   threshold: float = 0.5) -> bool:
    """
    Decode a thermal value to a boolean (truthy/falsy) based on a threshold.
    
    Values greater than or equal to the threshold are decoded as True,
    values less than the threshold are decoded as False.
    
    Args:
        value: Thermal value to decode
        threshold: Threshold for binary classification (default: 0.5)
        
    Returns:
        Boolean value: True if value >= threshold, False otherwise
    """
    return value >= threshold
