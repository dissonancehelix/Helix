
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CCSSignal:
    name: str
    value: float  # [0.0, 1.0]
    axis: str
    weight: float = 1.0

class CCSCalculator:
    """
    Core engine for mapping signals to 6D Cognitive Coordinates.
    Signals are mapped to axes according to core/models/ccs/SPEC.md definitions.
    """
    
    AXES = [
        "attractor_stability",
        "generative_constraint",
        "recurrence_depth",
        "structural_density",
        "control_entropy",
        "basin_permeability"
    ]
    
    def __init__(self, baseline_ref: Optional[Dict[str, float]] = None):
        # Baseline can be used for normalization (e.g., operator's mean energy)
        self.baseline = baseline_ref or {axis: 0.5 for axis in self.AXES}

    def calculate(self, signals: List[CCSSignal]) -> Dict[str, float]:
        """
        Groups signals by axis and computes the mean weighted value for each.
        """
        embedding = {axis: 0.0 for axis in self.AXES}
        counts = {o: 0 for o in self.AXES}
        
        for s in signals:
            if s.axis in embedding:
                embedding[s.axis] += s.value * s.weight
                counts[s.axis] += s.weight
                
        # Normalize and finalize each axis
        for axis in self.AXES:
            if counts[axis] > 0:
                embedding[axis] = embedding[axis] / counts[axis]
            else:
                embedding[axis] = self.baseline[axis] # Fallback to baseline
                
        return embedding

    def normalize_signal(self, raw_value: float, domain_min: float, domain_max: float) -> float:
        """
        Maps raw domain values to the [0, 1] unit hypercube.
        """
        return (raw_value - domain_min) / (domain_max - domain_min + 1e-9)
