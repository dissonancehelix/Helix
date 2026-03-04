import numpy as np
import random
from sklearn.metrics import mutual_info_score, adjusted_rand_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

def permutation_null(x, y, perms=1000, block_by=None):
    """
    Computes p-value for IG via permutation testing.
    P-value = (count(permuted_IG >= observed_IG) + 1) / (perms + 1)
    """
    observed_ig = mutual_info_score(x, y)
    count = 0
    
    y_perm = y.copy()
    for _ in range(perms):
        if block_by is not None:
            # Block-stratified permutation (not implemented here for simplicity, fallback to global)
            np.random.shuffle(y_perm)
        else:
            np.random.shuffle(y_perm)
        
        perm_ig = mutual_info_score(x, y_perm)
        if perm_ig >= observed_ig:
            count += 1
            
    return observed_ig, (count + 1) / (perms + 1)

def dropout_stability(x, y, trials=20, dropout_rates=[0.1, 0.2, 0.3]):
    """
    Measures stability of IG under data dropout.
    Returns mean drift (std of IG across trials).
    """
    results = {}
    for rate in dropout_rates:
        igs = []
        n = len(y)
        k = int(n * (1 - rate))
        for _ in range(trials):
            indices = np.random.choice(n, k, replace=False)
            igs.append(mutual_info_score(x[indices], y[indices]))
        results[f"dropout_{rate}"] = {
            "mean": float(np.mean(igs)),
            "std": float(np.std(igs)),
            "drift": float(np.std(igs) / (np.mean(igs) + 1e-9))
        }
    return results

def leakage_reconstruction(x, y, axis_labels, threshold=0.85):
    """
    Tests if y can be reconstructed from x (leakage).
    Use logistic regression for classification.
    """
    if len(np.unique(y)) < 2:
        return 0.0, False
        
    # Simple classification check
    clf = LogisticRegression(max_iter=1000)
    scores = cross_val_score(clf, x.reshape(-1, 1) if x.ndim == 1 else x, y, cv=min(5, len(y)))
    mean_score = float(np.mean(scores))
    
    return mean_score, mean_score > threshold

def isotopic_invariance(x, y):
    """
    Tests invariance of IG under label reordering/encoding change.
    ARI (Adjusted Rand Index) for clustering consistency or simple IG check.
    """
    # IG is already invariant to symbol name, so we test if re-labeling changes it (should be 0)
    orig_ig = mutual_info_score(x, y)
    
    unique_x = np.unique(x)
    mapping = {val: i for i, val in enumerate(np.random.permutation(unique_x))}
    x_rot = np.array([mapping[val] for val in x])
    
    rot_ig = mutual_info_score(x_rot, y)
    drift = abs(orig_ig - rot_ig)
    
    return drift, drift < 1e-9

# Proxy Operationalization Helpers
def get_collapse_present(domain):
    return 1 if domain.get('boundary_type_primary') != 'UNKNOWN' else 0

def get_abruptness_proxy(domain):
    txt = str(domain.get('failure_mode', '')).lower()
    if any(k in txt for k in ['jump', 'discontinuity', 'snap', 'abrupt', 'sudden', 'catastrophic', 'finite-time']):
        return 1 # JUMP
    if any(k in txt for k in ['smooth', 'gradual', 'slow', 'continuous', 'diffusive']):
        return 0 # SMOOTH
    return -1 # UNKNOWN

def get_reversibility_proxy(domain):
    txt = (str(domain.get('dynamics_operator', '')) + " " + str(domain.get('failure_mode', ''))).lower()
    if any(k in txt for k in ['absorbing', 'irreversible', 'hysteresis', 'one-way', 'non-invertible', 'commitment', 'damage', 'plastic']):
        return 1 # IRREVERSIBLE
    if any(k in txt for k in ['reversible', 'elastic', 'conservative', 'invertible', 'restorable']):
        return 0 # REVERSIBLE
    return -1 # UNKNOWN

def get_basin_count_proxy(domain):
    txt = (str(domain.get('dynamics_operator', '')) + " " + str(domain.get('stability_condition', ''))).lower()
    if any(k in txt for k in ['multi-basin', 'bistable', 'multistable', 'attractors', 'metastable']):
        return 1 # MULTI
    if any(k in txt for k in ['single basin', 'monostable', 'global attractor', 'unique equilibrium']):
        return 0 # SINGLE
    return -1 # UNKNOWN

def get_recovery_proxy(domain):
    txt = (str(domain.get('stability_condition', '')) + " " + str(domain.get('notes', ''))).lower()
    if any(k in txt for k in ['recoverable', 'repair', 'healing', 'resilient', 'restoration']):
        return 1
    if any(k in txt for k in ['fatal', 'irrecoverable', 'terminal', 'unrecoverable']):
        return 0
    return -1

def get_feedback_proxy(domain):
    txt = (str(domain.get('dynamics_operator', '')) + " " + str(domain.get('stability_condition', ''))).lower()
    return 1 if any(k in txt for k in ['feedback', 'recurrent', 'loop', 'circular', 'self-reinforcing', 'autocatalytic']) else 0

def get_modularity_proxy(domain):
    txt = (str(domain.get('substrate_formalism', '')) + " " + str(domain.get('notes', ''))).lower()
    return 1 if any(k in txt for k in ['modular', 'network', 'component', 'subsystem', 'distributed', 'array', 'agent-based']) else 0

def get_invariant_jump_proxy(domain):
    txt = (str(domain.get('dynamics_operator', '')) + " " + str(domain.get('failure_mode', ''))).lower()
    return 1 if any(k in txt for k in ['integer', 'topology change', 'invariant change', 'quantized', 'discrete update']) else 0

def get_compression_proxy(domain):
    txt = (str(domain.get('stability_condition', '')) + " " + str(domain.get('notes', ''))).lower()
    return 1 if any(k in txt for k in ['tightening', 'repair', 'enforcement', 'regulation', 'constraint', 'error correction']) else 0

def get_expression_proxy(domain):
    txt = (str(domain.get('dynamics_operator', '')) + " " + str(domain.get('notes', ''))).lower()
    return 1 if any(k in txt for k in ['branching', 'slack', 'recombination', 'exploration', 'diversity', 'redundancy']) else 0

def get_asymmetry_proxy(domain):
    txt = (str(domain.get('dynamics_operator', '')) + " " + str(domain.get('stability_condition', ''))).lower()
    # Check for asymmetry cues (arrow of time, one-way, non-commutative, gradient, flow)
    if any(k in txt for k in ['asymmetric', 'non-reversible', 'one-way', 'gradient', 'flow', 'directional', 'unilateral', 'irreversible']):
        return 1
    # Explicitly symmetrical cues
    if any(k in txt for k in ['symmetric', 'bi-directional', 'reversible', 'equilibrium', 'conservative']):
        return 0
    return -1

def get_dissipation_proxy(domain):
    txt = str(domain).lower()
    # Cues for entropy dumping/exhaust
    if any(k in txt for k in ['exhaust', 'waste', 'dump', 'dissipation', 'excretion', 'garbage collection', 'heat sink', 'evaporation', 'radiation']):
        return 1
    return 0

def get_coordination_proxy(domain):
    txt = str(domain).lower()
    # Coordination cues: synchronization, consensus, agents, collective, agreement
    score = 0
    if any(k in txt for k in ['synchronization', 'sync', 'consensus', 'agreement', 'protocol', 'agents', 'collective', 'cooperation', 'interaction']):
        score += 1
    if domain.get('regime') == 'Social / institutional collapse':
        score += 2
    return score

def get_symbolic_depth_proxy(domain):
    txt = str(domain).lower()
    # Depth cues: nesting, recursion, constraints, boolean, logic paths
    score = 0
    if any(k in txt for k in ['nesting', 'depth', 'recursion', 'constraint', 'boolean', 'compiler', 'sat', 'logic']):
        score += 1
    if domain.get('regime', '') == 'Purely symbolic / combinatorial systems':
        score += 2
    return score

def get_bridge_operators(domain):
    txt = str(domain).lower()
    ops = {}
    # B1: Selection / Optimization
    ops['B1'] = 1 if any(k in txt for k in ['fitness', 'optimization', 'minimization', 'selection', 'survival', 'least action']) else 0
    # B2: Adaptive Update
    ops['B2'] = 1 if any(k in txt for k in ['learning', 'adaptation', 'update rule', 'plasticity', 'evolutionary']) else 0
    # B3: Competitive Multi-Agent
    ops['B3'] = 1 if any(k in txt for k in ['multi-agent', 'competition', 'nash', 'game theory', 'social', 'collective']) else 0
    # B4: Computability
    ops['B4'] = 1 if any(k in txt for k in ['turing', 'algorithm', 'complexity class', 'computable', 'recursive function']) else 0
    # B5: Feedback Amplification
    ops['B5'] = 1 if any(k in txt for k in ['positive feedback', 'amplification', 'runaway', 're-entry', 'resonance']) else 0
    return ops
