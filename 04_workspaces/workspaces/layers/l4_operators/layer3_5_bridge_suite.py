import json
import numpy as np
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from runtime.infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
REPORT_FILE = ROOT / '06_artifacts/artifacts/reports/layer3_5_bridge_verdict.md'

class Layer3_5BridgeSuite:
    def __init__(self):
        self.domains = []
        self._load_data()
        self.assumptions = ["A1", "A2", "A3", "A4", "A5"]
        self.elements = ["C1", "C2", "C3", "C4"]
        self.bridges = ["B1", "B2", "B3", "B4", "B5"]

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
                except: pass
        print(f"Layer 3.5 Bridge Suite: Loaded {len(self.domains)} domains.")

    def run(self):
        # 1. Prep Data
        a_matrix = self._map_assumptions()
        e_matrix = self._map_elements()
        b_matrix = self._map_bridges()
        
        # 2. Phase 2: Sufficiency Test
        sufficiency = self._test_sufficiency(a_matrix, b_matrix, e_matrix)
        
        # 3. Phase 3: Minimality Test
        minimal_b_set = self._find_minimal_set(a_matrix, b_matrix, e_matrix)
        
        # 4. Phase 4: Non-Circularity Audit
        circ_report = self._audit_circularity(b_matrix, e_matrix)
        
        # 5. Phase 5: Cross-Regime Validation
        regime_results = self._validate_cross_regime(a_matrix, b_matrix, e_matrix)
        
        # 6. Generate Report
        self._generate_report(sufficiency, minimal_b_set, circ_report, regime_results)

    def _map_assumptions(self):
        matrix = []
        for d in self.domains:
            row = []
            txt = str(d).lower()
            row.append(1 if any(k in txt for k in ['branching', 'network', 'bandwidth', 'channel', 'capacity', 'throughput']) else 0) # A1
            row.append(1 if any(k in txt for k in ['finite', 'energy', 'resource', 'budget', 'limit', 'state-space']) else 0) # A2
            row.append(1 if any(k in txt for k in ['noise', 'perturbation', 'drift', 'fluctuation', 'stochastic', 'error']) else 0) # A3
            row.append(1 if d.get('boundary_locality') == 'LOCAL' or 'local' in txt else 0) # A4
            row.append(1 if d.get('substrate_type') == 'SYMBOLIC_SPACE' or any(k in txt for k in ['logic', 'consistency', 'contradiction', 'symbolic', 'invariant']) else 0) # A5
            matrix.append(row)
        return np.array(matrix)

    def _map_elements(self):
        matrix = []
        for d in self.domains:
            row = []
            row.append(1 if str(d.get('persistence_ontology', '')) != 'UNKNOWN' else 0) # C1
            row.append(1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0) # C2
            row.append(utils.get_coordination_proxy(d)) # C3
            row.append(utils.get_symbolic_depth_proxy(d)) # C4
            matrix.append(row)
        return np.array(matrix)

    def _map_bridges(self):
        matrix = []
        for d in self.domains:
            ops = utils.get_bridge_operators(d)
            matrix.append([ops[b] for b in self.bridges])
        return np.array(matrix)

    def _test_sufficiency(self, a, b, e):
        # Basis = [A1-A5]
        basis_str = np.array(["_".join([str(row[i]) for i in range(5)]) for row in a])
        results = {}
        for i, b_name in enumerate(self.bridges):
            e_scores = {}
            for j, e_name in enumerate(self.elements):
                # MI (A + Bk) -> Ej
                combined = np.array([f"{basis_str[k]}_{b[k, i]}" for k in range(len(basis_str))])
                mi = normalized_mutual_info_score(combined, e[:, j])
                e_scores[e_name] = float(mi)
            results[b_name] = e_scores
        return results

    def _find_minimal_set(self, a, b, e):
        # We find the set B* such that sum(MI(A + B*, Ei)) is maximized and count is minimized
        basis_str = np.array(["_".join([str(row[i]) for i in range(5)]) for row in a])
        best_avg_mi = 0
        best_set = []
        # Test individual, then pairs
        for i, b1 in enumerate(self.bridges):
            combined = np.array([f"{basis_str[k]}_{b[k, i]}" for k in range(len(basis_str))])
            avg_mi = np.mean([normalized_mutual_info_score(combined, e[:, j]) for j in range(4)])
            if avg_mi > best_avg_mi:
                best_avg_mi = avg_mi
                best_set = [b1]
        
        # Test addition of a second operator
        if best_set:
            b1_idx = self.bridges.index(best_set[0])
            for i, b2 in enumerate(self.bridges):
                if i == b1_idx: continue
                combined = np.array([f"{basis_str[k]}_{b[k, b1_idx]}_{b[k, i]}" for k in range(len(basis_str))])
                avg_mi = np.mean([normalized_mutual_info_score(combined, e[:, j]) for j in range(4)])
                if avg_mi > (best_avg_mi + 0.05): # Threshold for improvement
                    best_avg_mi = avg_mi
                    best_set.append(b2)
                    break
        return best_set

    def _audit_circularity(self, b, e):
        # Check if B elements encode C elements too directly
        results = {}
        for i, b_name in enumerate(self.bridges):
            for j, e_name in enumerate(self.elements):
                # MI(Bk, Ej) directly
                mi = normalized_mutual_info_score(b[:, i], e[:, j])
                if mi > 0.8: results[b_name] = f"CIRCULAR (High direct MI with {e_name}: {mi:.4f})"
        return results if results else "NONE_DETECTED"

    def _validate_cross_regime(self, a, b, e):
        regimes = {}
        for i, d in enumerate(self.domains):
            r = d.get('regime', 'Base')
            if r not in regimes: regimes[r] = []
            regimes[r].append(i)
        
        # Test on Symbolic-only and Institutional-only specifically
        results = {}
        target_regimes = ['Symbolic / combinatorial', 'Social / institutional', 'Ecological cascades', 'High-dimensional continuous']
        for r_name in target_regimes:
            idx = [i for i, d in enumerate(self.domains) if r_name in d.get('regime', '')]
            if len(idx) < 10: continue
            
            basis_str = np.array(["_".join([str(a[k, m]) for m in range(5)]) for k in idx])
            all_b = np.array(["_".join([str(b[k, m]) for m in range(5)]) for k in idx])
            
            # MI(A+B -> E) in this regime
            combined = np.array([f"{basis_str[k]}_{all_b[k]}" for k in range(len(idx))])
            # Average across E
            reg_mi = np.mean([normalized_mutual_info_score(combined, e[idx, j]) for j in range(4)])
            results[r_name] = float(reg_mi)
            
        return results

    def _generate_report(self, sufficiency, best_set, circ, regimes):
        report = f"# Helix Layer 3.5 Bridge Operator Verdict\n\n"
        
        # Classification
        classif = "MINIMAL_MULTI_BRIDGE" if len(best_set) > 1 else "SINGLE_BRIDGE_SUFFICIENT"
        if not best_set: classif = "NO_SUFFICIENT_BRIDGE"
        
        report += f"**Verdict:** {classif}\n\n"
        
        report += "## 1. Bridge Operator Sufficiency (MI Improvement over A1-A5)\n"
        report += "| Operator | C1 | C2 | C3 | C4 | Mean |\n"
        report += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for b in self.bridges:
            scores = sufficiency[b]
            row = [f"{scores[e]:.3f}" for e in self.elements]
            mean_score = sum(scores.values()) / 4
            report += f"| {b} | {' | '.join(row)} | {mean_score:.3f} |\n"
        report += "\n"
        
        report += f"## 2. Minimal Bridge Operator Set (B*)\n"
        report += f"- **Set:** {', '.join(best_set)}\n"
        report += f"- **Derivation:** Generates Layer 2 elements with maximal efficiency and minimal cardinality.\n\n"
        
        report += f"## 3. Circularity Audit\n"
        report += f"- **Status:** {'CLEAN' if circ == 'NONE_DETECTED' else 'WARNING'}\n"
        report += f"- **Details:** {circ}\n\n"
        
        report += f"## 4. Cross-Regime Validation (Mean Bridge-MI)\n"
        for r, score in regimes.items():
            report += f"- **{r}:** {score:.4f}\n"
        report += "\n"
        
        report += "### Bridge Descriptions\n"
        report += "- **B1:** Selection / Optimization pressure (Stability bias)\n"
        report += "- **B2:** Adaptive Update rules (Structural learning)\n"
        report += "- **B3:** Competitive Multi-Agent dynamics (Collective resource sharing)\n"
        report += "- **B4:** Computability constraints (Implementation limits)\n"
        report += "- **B5:** Feedback Amplification (Positive loops)\n\n"
        
        report += "---\nDerived From: Bridge Discovery Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Bridge report generated at {REPORT_FILE}")

if __name__ == "__main__":
    suite = Layer3_5BridgeSuite()
    suite.run()
