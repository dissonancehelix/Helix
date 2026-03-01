import numpy as np
from bin_b_operational.THREAT_MODEL import ThreatModel

class DCPHarness:
    """
    The 'Veto' system for the DCP Framework.
    Ensures certificates are only issued if assumptions are met.
    """
    def __init__(self, threat_model):
        self.T = threat_model
        self.log = []

    def check_assumptions(self, state_data):
        """
        Check all structural axioms. Return (Success, Veto_Reason)
        """
        # 0. Scope Exclusions (Brutal Vetoes)
        if state_data.get('full_observability', False):
            reason = "VETO: Non-DCP Domain. Full observability detected."
            self.log.append(reason)
            return False, reason

        if self.T.is_adaptive and state_data.get('env_reaction_depth', 0) == 0:
            reason = "VETO: Static environment detected for adaptive threat model."
            self.log.append(reason)
            return False, reason

        # 1. Epistemic check (r vs R)
        if not self.T.validate_axiom_1(state_data['r']):
            reason = f"VETO: Epistemic Capacity Gap (r={state_data['r']} < R={self.T.R})"
            self.log.append(reason)
            return False, reason
            
        # 2. Smoothness check (Axiom IV)
        if state_data.get('is_discontinuous', False):
            reason = "VETO: C0 Discontinuity detected."
            self.log.append(reason)
            return False, reason

        # 3. Resolution check (Axiom VI)
        if state_data['dx'] > (1.0 / self.T.Cmax):
            reason = f"VETO: Resolution Violation (dx={state_data['dx']}) > 1/Cmax"
            self.log.append(reason)
            return False, reason

        return True, "SYSTEM_READY"

def run_harness_test():
    T = ThreatModel(budget_R=3.0, curvature_Cmax=10.0)
    harness = DCPHarness(T)
    
    # Test case 1: Good sensor, high res
    case1 = {'r': 4.0, 'dx': 0.01}
    print(f"Case 1: {harness.check_assumptions(case1)}")
    
    # Test case 2: Sensing gap
    case2 = {'r': 2.0, 'dx': 0.01}
    print(f"Case 2: {harness.check_assumptions(case2)}")

    # Test case 3: Resolution gap
    case3 = {'r': 4.0, 'dx': 0.5}
    print(f"Case 3: {harness.check_assumptions(case3)}")

if __name__ == "__main__":
    run_harness_test()
