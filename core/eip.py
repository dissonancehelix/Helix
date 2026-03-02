# Helix Ring 0: Epistemic Irreversibility Principle (EIP)
# SACRED: No non-stdlib imports.

class EpistemicIrreversibility:
    """
    EIP Principle: For any agent with finite epistemic capacity (r),
    in an environment with irreversible sinks (C), uncertainty scales
    as binary terminal failure.
    """
    @staticmethod
    def is_irreversible(failure_mode, stability_condition):
        terms = ['hysteresis', 'irreversible', 'latch', 'absorbing', 'path-depend', 'lock-in']
        combined = (failure_mode + " " + stability_condition).lower()
        return any(term in combined for term in terms)

    @staticmethod
    def classify_commitment(is_irreversible):
        return "IRREVERSIBLE_SINK" if is_irreversible else "REVERSIBLE_STATE"
