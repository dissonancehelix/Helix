import json
import numpy as np
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from sklearn.ensemble import RandomForestClassifier
from infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
REPORT_FILE = ROOT / 'reports/bridge_decoupling_verdict.md'

class BridgeDecouplingSuite:
    def __init__(self):
        self.domains = []
        self._load_data()

    def _load_data(self):
        # Base
        for p in (ROOT / 'data/domains').glob('*.json'):
            if p.name.startswith('phase'): continue
            with open(p, 'r') as f:
                try: self.domains.append(json.load(f))
                except: continue
        # Expansion
        expansion_file = ROOT / 'data/domains_extreme_expansion.json'
        if expansion_file.exists():
            with open(expansion_file, 'r') as f:
                self.domains.extend(json.load(f))
        print(f"Bridge Decoupling Suite: Loaded {len(self.domains)} domains.")

    def run(self):
        # Data Prep
        y = np.array([d.get('boundary_type_primary', 'UNKNOWN') for d in self.domains])
        
        # Element C3
        x_c10 = np.array([utils.get_coordination_proxy(d) for d in self.domains])
        
        # Bridge B3
        ops = [utils.get_bridge_operators(d) for d in self.domains]
        x_b3 = np.array([o['B3'] for o in ops])
        
        # Phase 1: Isomorphism Test
        mi = normalized_mutual_info_score(x_b3, x_c10)
        recon_b3_to_c10 = self._reconstruction_ratio(x_b3, x_c10)
        recon_c10_to_b3 = self._reconstruction_ratio(x_c10, x_b3)
        
        # Phase 2: Predictive Difference
        # C1, C2 (Base)
        x_c1 = np.array([str(d.get('persistence_ontology', 'UNKNOWN')) for d in self.domains])
        x_c2 = np.array([1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0 for d in self.domains])
        
        u1 = np.unique(x_c1)
        m_c1 = np.array([np.where(u1 == v)[0][0] for v in x_c1])
        
        model_a_acc = self._predictive_test(m_c1, x_c2, x_c10, y)
        model_b_acc = self._predictive_test(m_c1, x_c2, x_b3, y)
        
        # Phase 4: Symmetry Break
        sym_break = self._symmetry_test(m_c1, x_c2, x_c10, x_b3, y)

        # Phase 5: Abstract Formalization
        # Re-derive B3 without "agent" or "social" keywords
        x_b3_pure = []
        for d in self.domains:
            txt = str(d).lower()
            val = 0
            # Pure B3: Competition + resources + sharing
            if any(k in txt for k in ['competition', 'resource sharing', 'sharing', 'conflict', 'nash', 'sharing strategy']):
                val = 1
            x_b3_pure.append(val)
        x_b3_pure = np.array(x_b3_pure)
        mi_pure = normalized_mutual_info_score(x_b3_pure, x_c10)

        # Generate Report
        self._generate_report(mi, recon_b3_to_c10, recon_c10_to_b3, model_a_acc, model_b_acc, sym_break, mi_pure)

    def _reconstruction_ratio(self, x, target):
        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        X = x.reshape(-1, 1)
        clf.fit(X, target)
        pred = clf.predict(X)
        mi_full = mutual_info_score(target, target)
        mi_recon = mutual_info_score(pred, target)
        return mi_recon / (mi_full + 1e-9)

    def _predictive_test(self, c1, c2, test_axis, y):
        X = np.stack([c1, c2, test_axis], axis=1)
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        # Using 5-fold cross val score for stability comparison
        from sklearn.model_selection import cross_val_score
        # Stratified if y has more than 1 class
        if len(np.unique(y)) > 1:
            scores = cross_val_score(clf, X, y, cv=3)
            return float(np.mean(scores))
        return 0.0

    def _symmetry_test(self, c1, c2, c10, b3, y):
        # Drop C3, keep B3
        x_b_only = np.stack([c1, c2, b3], axis=1)
        ig_b = mutual_info_score(np.array(["_".join([str(v) for v in row]) for row in x_b_only]), y)
        
        # Drop B3, keep C3
        x_c_only = np.stack([c1, c2, c10], axis=1)
        ig_c = mutual_info_score(np.array(["_".join([str(v) for v in row]) for row in x_c_only]), y)
        
        return {"ig_b_only": float(ig_b), "ig_c_only": float(ig_c)}

    def _generate_report(self, mi, r1, r2, acc_a, acc_b, sym, mi_pure):
        verdict = "ISOMORPHIC_RELABEL"
        if mi_pure < (mi * 0.7): verdict = "TRUE_GENERATIVE_BRIDGE"
        elif sym["ig_b_only"] != sym["ig_c_only"]: verdict = "PARTIAL_OVERLAP"
        
        report = f"# Helix Bridge-Element Decoupling Verdict\n\n"
        report += f"**Verdict:** {verdict}\n\n"
        
        report += "## 1. Isomorphism Test\n"
        report += f"- **B3 <-> C3 MI:** {mi:.4f}\n"
        report += f"- **Reconstruction B3 -> C3:** {r1:.4f}\n"
        report += f"- **Reconstruction C3 -> B3:** {r2:.4f}\n\n"
        
        report += "## 2. Predictive Comparison\n"
        report += f"- **Model A (with C3): Accuracy:** {acc_a:.4f}\n"
        report += f"- **Model B (with B3): Accuracy:** {acc_b:.4f}\n"
        report += f"- **Predictive Difference:** {abs(acc_a - acc_b):.4f}\n\n"
        
        report += "## 3. Symmetry Break Results\n"
        report += f"- **IG (C1+C2+B3):** {sym['ig_b_only']:.4f}\n"
        report += f"- **IG (C1+C2+C3):** {sym['ig_c_only']:.4f}\n\n"
        
        report += "## 4. Formalization & Leakage\n"
        report += f"- **B3 Original MI with C3:** {mi:.4f}\n"
        report += f"- **B3 Pure (Semantic isolation) MI with C3:** {mi_pure:.4f}\n"
        report += f"  - Ratio: {mi_pure / (mi + 1e-9):.4f}\n\n"
        
        report += "---"
        report += f"\nDerived From: Bridge-Element Decoupling Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Decoupling report generated for verdict: {verdict}")

if __name__ == "__main__":
    suite = BridgeDecouplingSuite()
    suite.run()
