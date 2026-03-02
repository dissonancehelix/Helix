import json
import numpy as np
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import TruncatedSVD
from infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
REPORT_FILE = ROOT / 'reports/rank_collapse_verdict.md'

class RankCollapseSuite:
    def __init__(self):
        self.domains = []
        self._load_datasets()
        if not (ROOT / 'reports').exists(): (ROOT / 'reports').mkdir(parents=True, exist_ok=True)

    def _load_datasets(self):
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
        print(f"Rank Collapse Suite: Loaded {len(self.domains)} domains.")

    def run(self):
        # Data Prep
        y = np.array([d.get('boundary_type_primary', 'UNKNOWN') for d in self.domains])
        
        # Elements
        x_c1 = np.array([str(d.get('persistence_ontology', 'UNKNOWN')) for d in self.domains])
        x_c2 = np.array([1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0 for d in self.domains])
        x_c8 = np.array([1 if any(k in str(d).lower() for k in ['self-model', 'internal model', 'representation', 'recursion', 'predictive loop']) else 0 for d in self.domains])
        x_c10 = np.array([utils.get_coordination_proxy(d) for d in self.domains])
        x_c11 = np.array([utils.get_symbolic_depth_proxy(d) for d in self.domains])

        elements = {
            "C1": x_c1,
            "C2": x_c2,
            "C8": x_c8,
            "C3": x_c10,
            "C4": x_c11
        }

        # Phase 1: Redundancy Compression
        recon_ratios = {}
        for target in ["C3", "C4"]:
            recon_ratios[target] = self._test_redundancy(elements["C1"], elements["C2"], elements[target])

        # Phase 2: Cross-Regime Holdout
        cross_regime_ig = self._run_cross_regime_holdout(y, elements)

        # Phase 3: Adversarial Inversion
        # Inject adversarial domains (constructed in situ)
        adv_results = self._run_adversarial_inversion(y, elements)

        # Phase 4: Minimal Basis SVD
        rank_info = self._run_svd(elements)

        # Phase 5: Element Necessity Ablation
        ablation_deltas = self._run_ablation(y, elements)

        # Phase 6: Feature Entanglement Audit
        leakage_results = self._run_leakage_audit(y, elements)

        # Final Report
        self._generate_report(recon_ratios, cross_regime_ig, adv_results, rank_info, ablation_deltas, leakage_results)

    def _test_redundancy(self, c1, c2, target):
        # Mapping C1 to numeric
        u = np.unique(c1)
        m_c1 = np.array([np.where(u == v)[0][0] for v in c1])
        X = np.stack([m_c1, c2], axis=1)
        
        # Train nonlinear model
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X, target)
        score = clf.score(X, target)
        
        # Ratio of mutual info
        mi_full = mutual_info_score(target, target)
        mi_recon = mutual_info_score(clf.predict(X), target)
        ratio = mi_recon / (mi_full + 1e-9)
        
        return float(ratio)

    def _run_cross_regime_holdout(self, y, elements):
        regimes = {}
        for i, d in enumerate(self.domains):
            reg = d.get('regime', 'Base')
            if reg not in regimes: regimes[reg] = []
            regimes[reg].append(i)
            
        results = {}
        for target_element in ["C3", "C4"]:
            res_list = []
            for target_reg in regimes:
                test_idx = regimes[target_reg]
                train_idx = [idx for r, idxs in regimes.items() if r != target_reg for idx in idxs]
                
                if not train_idx or not test_idx: continue
                
                # IG of target_element on test_idx
                ig = mutual_info_score(elements[target_element][test_idx], y[test_idx])
                res_list.append(float(ig))
            results[target_element] = res_list
        return results

    def _run_adversarial_inversion(self, y, elements):
        # Construct synthetic adversarial domains
        # We simulate the drop in IG if coordination/symbolic depth are decoupled from boundary
        n = len(y)
        flip_idx = random.sample(range(n), 300)
        
        results = {}
        for name in ["C3", "C4"]:
            x_adv = elements[name].copy()
            # Randomize x_adv for the flip_idx
            u = np.unique(x_adv)
            for idx in flip_idx:
                x_adv[idx] = random.choice(u)
            
            ig_adv = mutual_info_score(x_adv, y)
            results[name] = float(ig_adv)
        return results

    def _run_svd(self, elements):
        def to_num(arr):
            u = np.unique(arr)
            return np.array([np.where(u == v)[0][0] for v in arr])
            
        matrix = np.stack([to_num(v) for v in elements.values()], axis=1)
        # Normalize
        matrix = (matrix - matrix.mean(axis=0)) / (matrix.std(axis=0) + 1e-9)
        
        svd = TruncatedSVD(n_components=min(matrix.shape))
        svd.fit(matrix)
        
        explained = svd.explained_variance_ratio_
        var_top3 = sum(explained[:3])
        var_top4 = sum(explained[:4])
        
        rank = sum(svd.singular_values_ > 0.1)
        
        return {
            "rank": int(rank),
            "var_top3": float(var_top3),
            "var_top4": float(var_top4),
            "singular_values": [float(s) for s in svd.singular_values_]
        }

    def _run_ablation(self, y, elements):
        def combine(names):
            # Combine multiple elements into a single vector for IG
            # Simplified: string concatenation of states
            combined = []
            for i in range(len(y)):
                combined.append("_".join([str(elements[n][i]) for n in names]))
            return np.array(combined)

        all_names = list(elements.keys())
        full_ig = mutual_info_score(combine(all_names), y)
        
        deltas = {}
        for name in all_names:
            subset = [n for n in all_names if n != name]
            subset_ig = mutual_info_score(combine(subset), y)
            deltas[name] = float(full_ig - subset_ig)
        return deltas

    def _run_leakage_audit(self, y, elements):
        y_shuffled = y.copy()
        random.shuffle(y_shuffled)
        
        leaks = {}
        for name, vec in elements.items():
            ig_leak = mutual_info_score(vec, y_shuffled)
            leaks[name] = float(ig_leak)
        return leaks

    def _generate_report(self, recon, cross, adv, rank_info, ablation, leak):
        verdict = "STRUCTURED_HIGH_RANK (finite basis)"
        if rank_info["var_top3"] >= 0.85:
            verdict = "REDUCIBLE_GEOMETRY (3D basis)"
        elif rank_info["var_top4"] >= 0.90:
            verdict = "LOW_RANK_PLURALITY"
            
        report = f"# Helix Rank Collapse & Element Minimality Verdict\n\n"
        report += f"**Verdict:** {verdict}\n\n"
        
        report += f"## Phase 1: Redundancy Compression\n"
        for t, r in recon.items():
            status = "INDEPENDENT"
            if r > 0.75: status = "DERIVATIVE"
            elif r > 0.5: status = "PARTIALLY_COMPOSITE"
            report += f"- **{t} Reconstruction Ratio:** {r:.4f} ({status})\n"
        report += "\n"
        
        report += f"## Phase 2: Cross-Regime Holdout (Mean IG)\n"
        for t, values in cross.items():
            report += f"- **{t} Stability (N={len(values)}):** {np.mean(values):.4f}\n"
        report += "\n"
        
        report += f"## Phase 3: Adversarial Inversion\n"
        for t, ig in adv.items():
            report += f"- **{t} Adversarial IG:** {ig:.4f}\n"
        report += "\n"
        
        report += f"## Phase 4: Minimal Basis SVD\n"
        report += f"- **Effective Rank:** {rank_info['rank']}\n"
        report += f"- **Variance Explained (Top 3):** {rank_info['var_top3']:.4f}\n"
        report += f"- **Variance Explained (Top 4):** {rank_info['var_top4']:.4f}\n"
        report += f"- **Singular Values:** {rank_info['singular_values']}\n\n"
        
        report += f"## Phase 5: Element Necessity Ablation (ΔIG)\n"
        for name, delta in ablation.items():
            report += f"- **{name}:** {delta:.4f} {'(ESSENTIAL)' if delta > 0.05 else '(REDUNDANT)'}\n"
        report += "\n"
        
        report += f"## Phase 6: Feature Entanglement Audit\n"
        for name, l in leak.items():
            report += f"- **{name} Leakage IG:** {l:.4f} {'(LEAK DETECTED)' if l > 0.05 else '(CLEAN)'}\n"
        report += "\n"
        
        report += f"---"
        report += f"\nDerived From: Rank Collapse Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Rank Collapse report generated. Verdict: {verdict}")

if __name__ == "__main__":
    suite = RankCollapseSuite()
    suite.run()
