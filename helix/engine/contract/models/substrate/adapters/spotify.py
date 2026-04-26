
from typing import Dict, List
import pandas as pd
from core.models.substrate.engine.calculator import domainsignal, SubstrateCalculator

class SpotifyAdapter:
    """
    Maps Spotify audio features to Substrate Capability Vector Signals.
    Derived from structural deep dive on operator data (~200k scrobbles).
    """
    
    def map_track(self, features: Dict[str, float]) -> List[domainsignal]:
        signals = []
        
        # 1. Structural Density (Stiffness: Energy / Danceability)
        # Higher Ratio = 'Stiff' density (Metal/VGM). Lower = 'Loose' density (Pop/Swing).
        stiffness = features.get("Energy", 0.5) / (features.get("Danceability", 0.5) + 0.01)
        
        signals.append(domainsignal(
            name="structural_stiffness",
            value=min(1.0, stiffness / 5.0), # Normalize 5.0 ratio to 1.0
            axis="structural_density"
        ))
        
        # 2. Generative Constraint (Proxy: Instrumentalness * (1-Acousticness))
        # Includes 'Substrate Saturation' proxy via Instrumentalness
        signals.append(CCSSignal(
            name="hardware_constraint_proxy",
            value=features.get("Instrumentalness", 0.1) * (1.0 - features.get("Acousticness", 0.1)),
            axis="generative_constraint"
        ))
        
        # 3. Control Entropy (Proxy: 1 - Valence)
        # Minor keys/tense music = higher perceived structural entropy
        signals.append(CCSSignal(
            name="tension_entropy",
            value=1.0 - features.get("Valence", 0.5),
            axis="control_entropy"
        ))
        
        # 4. Attractor Stability (Proxy: Danceability * Acousticness)
        # Higher organic predictability = stable attractor
        signals.append(CCSSignal(
            name="organic_stability",
            value=features.get("Danceability", 0.5) * features.get("Acousticness", 0.1),
            axis="attractor_stability"
        ))
        
        return signals
