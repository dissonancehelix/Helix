# SUBSTRATE RESOLUTION CONSTRAINTS (RING 1)
# Inherited from Structural Basis B1_BASIN

import json

class SubstrateResolution:
    """
    Evaluates the 'Mantle' of a B1 Basin.
    Definition: The minimum numeric resolution required to prevent 
    spontaneous basin state transition due to rounding-depth.
    """
    
    BIT_DEPTH_MAP = {
        "float32": 24, # Significand bits
        "bfloat16": 7,
        "float16": 10,
        "int8": 8,
        "int4": 4
    }

    @staticmethod
    def get_resolution_error(substrate_type):
        """Returns the epsilon-drift based on substrate precision."""
        bits = SubstrateResolution.BIT_DEPTH_MAP.get(substrate_type, 0)
        if bits == 0: return 1.0 # Maximum uncertainty
        return 2 ** (-bits)

    @staticmethod
    def validate_b1_depth(b1_value, substrate_type):
        """
        Validates if a B1 Basin is actually stable given the substrate mantle.
        If B1_depth < resolution_error, the basin is 'virtual' and non-persistent.
        """
        error = SubstrateResolution.get_resolution_error(substrate_type)
        if b1_value < error:
            return {
                "status": "UNSTABLE",
                "reason": "BASIN_FLOOR_COLLAPSE",
                "mantle_error": error
            }
        return {"status": "STABLE", "mantle_error": error}
