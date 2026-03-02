# Helix Ring 0: Irreducibility Protocol
# SACRED: No non-stdlib imports.

class IrreducibilityTest:
    """
    Verifies that a proposed basis or primitive is not redundant.
    Threshold for rejection: Reconstruction Ratio >= 0.75
    """
    @staticmethod
    def check_independence(mi_score, reconstruction_ratio):
        if reconstruction_ratio >= 0.75:
            return "DERIVATIVE_REJECTED"
        if mi_score > 0.5:
            return "HIGH_COUPLING_WARNING"
        return "ORTHOGONAL_CONFIRMED"

    @staticmethod
    def validate_overlay(agreement_pct):
        return agreement_pct >= 0.90
