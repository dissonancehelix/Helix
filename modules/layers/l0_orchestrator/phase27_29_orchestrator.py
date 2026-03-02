import json
import math
import random
import statistics
from pathlib import Path
from collections import Counter

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / 'domains'

domains = []
for p in DOMAINS_DIR.glob('*.json'):
    with open(p, 'r') as f:
        domains.append(json.load(f))

PHI = (1 + math.sqrt(5)) / 2
N = len(domains)
boundaries = [d.get('boundary_type_primary', 'UNKNOWN') for d in domains]

# Observed
b_counts = Counter(boundaries)
# Sort descending
b_freqs = sorted(b_counts.values(), reverse=True)
obs_r = b_freqs[2] / b_freqs[3] if len(b_freqs) > 3 and b_freqs[3] > 0 else 0

# --- PHASE 27: BOOTSTRAP ---
random.seed(42)
bootstrap_r = []
for _ in range(10000):
    sample = random.choices(boundaries, k=N)
    counts = sorted(Counter(sample).values(), reverse=True)
    if len(counts) > 3 and counts[3] > 0:
        bootstrap_r.append(counts[2] / counts[3])
    else:
        bootstrap_r.append(0)

mean_r = statistics.mean(bootstrap_r)
std_r = statistics.stdev(bootstrap_r)
prob_phi = sum(1 for r in bootstrap_r if abs(r - PHI) <= 0.01) / len(bootstrap_r)

# Null Model
null_r = []
blist = list(set(boundaries))
for _ in range(10000):
    sample = [random.choice(blist) for _ in range(N)]
    counts = sorted(Counter(sample).values(), reverse=True)
    if len(counts) > 3 and counts[3] > 0:
        null_r.append(counts[2] / counts[3])
    else:
        null_r.append(0)

mean_null = statistics.mean(null_r)
std_null = statistics.stdev(null_r)
z_score = (obs_r - mean_null) / std_null if std_null > 0 else 0

verdict_27 = "COINCIDENCE" if z_score < 2 else ("WEAK_SIGNAL" if z_score < 3 else "STRUCTURAL_ANOMALY")

# --- PHASE 28: STRATIFIED ---
s1c_groups = {}
for d in domains:
    s = d.get('substrate_S1c', 'HYBRID')
    s1c_groups.setdefault(s, []).append(d.get('boundary_type_primary', 'UNKNOWN'))

group_rs = []
for s, b_list in s1c_groups.items():
    counts = sorted(Counter(b_list).values(), reverse=True)
    if len(counts) > 3 and counts[3] > 0:
        group_rs.append(counts[2] / counts[3])

var_group = statistics.variance(group_rs) if len(group_rs) > 1 else 0

# Random removal 
removal_stability = []
for k in range(1, 11):
    k_rs = []
    for _ in range(100):
        sample = random.sample(boundaries, N - k)
        counts = sorted(Counter(sample).values(), reverse=True)
        if len(counts) > 3 and counts[3] > 0:
            k_rs.append(counts[2] / counts[3])
    removal_stability.append(statistics.mean(k_rs))

stratified_verdict = "COLLAPSED"
# If removing domains makes r jump wildly away from phi
if all(abs(r - PHI) < 0.2 for r in removal_stability):
    stratified_verdict = "STABLE"

# --- PHASE 29: OPERATOR-LEVEL KAM ---
# Since our json schemas do not enforce numeric epsilons (they just contain text descriptions),
# we cannot find actual numeric spectral gaps clustering around PHI. 
operator_phi_verdict = "FAILED_NO_NUMERIC_OPERATOR_RATIOS"

# Final Verdict
if prob_phi > 0.05 and stratified_verdict == "STABLE":
    final_verdict = "WEAK_INVARIANT"
else:
    final_verdict = "NUMERICAL_ARTIFACT"

output = f"""- Bootstrap P(|r \u2212 \u03c6| \u2264 0.01): {prob_phi:.4f}
- Null z-score: {z_score:.4f}
- Stratified stability verdict: {stratified_verdict}
- Operator-level \u03c6 detection verdict: {operator_phi_verdict}
- Final classification: {final_verdict}"""

print(output)
