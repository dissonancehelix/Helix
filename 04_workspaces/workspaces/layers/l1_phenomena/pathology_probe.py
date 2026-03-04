from pathlib import Path
import json
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score

from collections import defaultdict
from runtime.infra.io.persistence import save_wrapped

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ART_DIR = ROOT / '06_artifacts/artifacts'

def build_risk(domains):
    hybrids = [d for _, d in domains if d.get('substrate_S1c') == 'HYBRID']
    ranked = []
    for d in hybrids:
        score = 0
        obs = d.get('measurement_layer', {}).get('obstruction_type', '')
        if obs == 'UNITS_NOT_PROJECTABLE': score += 3
        if obs == 'NO_ORDER_PARAMETER': score += 2
        o = d.get('persistence_ontology', '')
        if o in ['P2_GLOBAL_INVARIANT', 'P3_ALGORITHMIC_SYNDROME']: score += 5
        elif o == 'P4_DISTRIBUTIONAL_EQUILIBRIUM': score += 3
        else: score += 1
        t = d.get('T1', '')
        t_mult = 1.5 if t in ['T1_FAST_PERTURB', 'T1_COMPARABLE'] else 1.0
        
        final = score * t_mult
        ranked.append({"domain": d.get("id"), "risk_score": final})
        
    ranked.sort(key=lambda x: x["risk_score"], reverse=True)
    save_wrapped(ART_DIR / 'risk/risk_scores.json', ranked)
    return ranked

def build_structural_debt(domains):
    report_items = []
    for _, d in domains:
        stats = {"TODO": 0, "UNDEFINED": 0, "SCHEMA_INSUFFICIENT": 0, "NO_THRESHOLD_DEFINED": 0, "numeric_coverage": 0.0}
        flat_values = str(d).upper()
        stats["TODO"] = flat_values.count("TODO")
        stats["UNDEFINED"] = flat_values.count("UNDEFINED")
        stats["SCHEMA_INSUFFICIENT"] = flat_values.count("SCHEMA_INSUFFICIENT")
        stats["NO_THRESHOLD_DEFINED"] = flat_values.count("NO_THRESHOLD_DEFINED")
        nums = [1 for w in flat_values.split() if w.replace('.', '', 1).isdigit()]
        words = len(flat_values.split())
        if words > 0: stats["numeric_coverage"] = len(nums) / words
        report_items.append({"domain_id": d.get("id"), "debt": stats})
    save_wrapped(ART_DIR / 'structural_debt_report.json', report_items)
    return report_items
REPORT_FILE = ROOT / '06_artifacts/artifacts/reports/pathology_deep_scan.md'

import pandas as pd
from runtime.infra.platform import claims_suite_utils as utils

class PathologyProbe:
    def __init__(self):
        self.domains = []
        self._load_data()

    def _load_data(self):
        from runtime.infra.io.persistence import load_domains
        # Base
        domain_items = load_domains(ROOT / '04_workspaces/workspaces/domain_data/domains')
        self.domains = [d for _, d in domain_items]
        
        # Expansion
        expansion_file = ROOT / '04_workspaces/workspaces/domain_data/domains_extreme_expansion.json'
        if expansion_file.exists():
            with open(expansion_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.domains.extend(data)
                    else:
                        self.domains.append(data)
                except:
                    pass
        print(f"Pathology Probe: Loaded {len(self.domains)} total domains.")

    def run(self):
        pathological = [d for d in self.domains if "Pathological" in d.get('regime', '') or "adversarial" in d.get('regime', '').lower()]
        stable = [d for d in self.domains if d not in pathological]
        
        print(f"Pathological: {len(pathological)}, Stable: {len(stable)}")
        
        # 1. Local Rank Analysis
        rank_p = self._calculate_rank(pathological)
        rank_s = self._calculate_rank(stable)
        
        # 2. Information Persistence Bias
        bias_p = self._calculate_persistence_bias(pathological)
        bias_s = self._calculate_persistence_bias(stable)
        
        # 3. Substrate Volatility
        vol_p = self._calculate_substrate_volatility(pathological)
        vol_s = self._calculate_substrate_volatility(stable)
        
        # 4. Identity Collapse Search (Collision between K1 and K2)
        collision = self._check_kernel_collision(pathological)

        # 5. Generate Report
        self._generate_report(len(pathological), rank_p, rank_s, bias_p, bias_s, vol_p, vol_s, collision)

    def _calculate_rank(self, subset):
        if len(subset) < 10: return 0
        vectors = []
        for d in subset:
            row = []
            # Encoding features
            row.append(utils.get_coordination_proxy(d))
            row.append(utils.get_symbolic_depth_proxy(d))
            row.append(1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0)
            p_map = {"P0_STATE_LOCAL": 0, "P1_STRUCTURAL_INVARIANT": 1, "P2_TOPOLOGICAL_BASIN": 2, "P3_INFORMATION_TRACE": 3}
            row.append(p_map.get(d.get('persistence_ontology', 'P1_STRUCTURAL_INVARIANT'), 1))
            vectors.append(row)
        
        vectors = np.array(vectors)
        svd = TruncatedSVD(n_components=min(vectors.shape) - 1 if vectors.shape[1] > 1 else 1)
        svd.fit(vectors)
        # Effective rank = count of components that explain > 5% of variance
        expl = svd.explained_variance_ratio_
        return int(np.sum(expl > 0.05))

    def _calculate_persistence_bias(self, subset):
        # Distribution of Persistence Ontology
        dist = [d.get('persistence_ontology', 'UNKNOWN') for d in subset]
        val_counts = pd.Series(dist).value_counts(normalize=True).to_dict()
        return val_counts

    def _calculate_substrate_volatility(self, subset):
        # Entropy of substrate types
        dist = [d.get('substrate_type', 'UNKNOWN') for d in subset]
        counts = pd.Series(dist).value_counts(normalize=True)
        entropy = -np.sum(counts * np.log2(counts + 1e-9))
        return entropy

    def _check_kernel_collision(self, subset):
        # Do K1 and K2 become identical in pathological zones?
        k1 = np.array([str(d.get('persistence_ontology', '')) for d in subset])
        k2 = np.array([1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0 for d in subset])
        mi = normalized_mutual_info_score(k1, k2)
        return float(mi)

    def _generate_report(self, count, rp, rs, bp, bs, vp, vs, coll):
        report = f"# Helix Pathology Deep Scan Report\n\n"
        report += f"**Staring Duration:** Extended (Focus on Pathological Adversarial Zones)\n"
        report += f"**Target Samples:** {count} domains\n\n"
        
        report += f"### 1. Structural Phase Transition\n"
        report += f"| Regime | Effective Rank | Substrate Volatility (Entropy) |\n"
        report += f"| :--- | :--- | :--- |\n"
        report += f"| **Stable** | {rs} | {vs:.4f} |\n"
        report += f"| **Pathological** | {rp} | {vp:.4f} |\n\n"
        
        report += f"**Observation:** Pathological zones exhibit a **{'CLEAN RANK LOSS' if rp < rs else 'RANK INFLATION'}**. "
        if rp < rs:
            report += "This suggests a structural collapse where the system loses its internal degrees of freedom."
        else:
            report += "This suggests an irreducible complexity spike requiring a new element (C13?)"
        
        report += f"\n\n### 2. Kernel Collision Analysis\n"
        report += f"- **K1 <-> K2 Correlation (MI):** {coll:.4f}\n"
        if coll > 0.5:
            report += "**WARNING:** Kernel-1 (Ontology) and Kernel-2 (Expression) are colliding in pathological regimes. "
            report += "The boundary between 'what a system is' and 'what it does' is dissolving.\n"
        else:
            report += "**STATUS:** Base Kernels remain orthogonal even in fracture zones.\n"
            
        report += f"\n### 3. Persistence Shadow\n"
        report += "**Stable Distribution:**\n"
        for k, v in bs.items(): report += f"- {k}: {v*100:.1f}%\n"
        report += "\n**Pathological Distribution:**\n"
        for k, v in bp.items(): report += f"- {k}: {v*100:.1f}%\n"
        
        report += "\n### 4. The 'Stare' Outcome\n"
        if vp > vs * 1.5:
            report += "The substrate volatility in pathological domains is critically high. "
            report += "We are looking at systems where the type of substrate (HYBRID vs SYMBOLIC) changes faster than the state itself."
        
        report += "\n---\nDerived From: Pathology Deep Scan v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Deep scan report generated at {REPORT_FILE}")

if __name__ == "__main__":
    probe = PathologyProbe()
    probe.run()
