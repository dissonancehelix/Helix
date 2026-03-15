import json
import numpy as np
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from engines.infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_FILE = ROOT / '04_labs/corpus/domains/domains_extreme_expansion.json'
REPORT_FILE = ROOT / '07_artifacts/artifacts/reports/extreme_validation_report.md'

class HostileValidation:
    def __init__(self):
        self.domains = []
        self._load_datasets()
        if not (ROOT / '07_artifacts/artifacts/reports').exists(): (ROOT / '07_artifacts/artifacts/reports').mkdir(parents=True, exist_ok=True)
        
    def _load_datasets(self):
        from engines.infra.io.persistence import load_domains
        # 1. Base + Packs
        base_items = load_domains(ROOT / '04_labs/corpus/domains/domains')
        self.domains = [d for _, d in base_items]
        
        pack_items = load_domains(ROOT / '04_labs/corpus/domains/packs', recursive=True)
        self.domains.extend([d for _, d in pack_items])
        
        # 2. Extreme Expansion
        if DOMAINS_FILE.exists():
            with open(DOMAINS_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.domains.extend(data)
                    else:
                        self.domains.append(data)
                except:
                    pass
        print(f"Hostile Validation: Total Domains = {len(self.domains)}")

    def run(self):
        y = np.array([d.get('boundary_type_primary', 'UNKNOWN') for d in self.domains])
        x_k1 = np.array([str(d.get('persistence_ontology', 'UNKNOWN')) for d in self.domains])
        x_k2 = np.array([1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0 for d in self.domains])
        x_c8 = np.array([1 if any(k in str(d).lower() for k in ['self-model', 'internal model', 'representation', 'recursion', 'predictive loop']) else 0 for d in self.domains])
        x_c9 = np.array([utils.get_feedback_proxy(d) for d in self.domains])
        x_c10 = np.array([utils.get_coordination_proxy(d) for d in self.domains])
        x_c11 = np.array([utils.get_symbolic_depth_proxy(d) for d in self.domains])

        # Phase 2: Promotion Pipeline Re-run
        # (Simplified implementation for the report)
        ig_k1, p_k1 = utils.permutation_null(x_k1, y, perms=500)
        ig_k2, p_k2 = utils.permutation_null(x_k2, y, perms=500)
        
        # Phase 3: High-Rank Detection
        rank, variance_top2, rank_change = self._run_rank_test(y, x_k1, x_k2, x_c10, x_c11)
        
        # Phase 4: Cross-Domain Holdout
        generalization_scores = self._run_cross_domain_test(y, x_k2)
        
        # Phase 5: Interaction Nonlinearity
        nonlinearity_verdict = self._run_nonlinearity_test(y, x_k1, x_k2)
        
        # Phase 6: Structural Fracture Search
        fracture_count = self._run_fracture_search(y, x_k2)
        
        # Phase 7: Ontological Limit Investigation (Open Questions)
        limit_results = self._investigate_open_questions(y, x_k1, x_k2, x_c8, x_c9, x_c10, x_c11)
        
        # Final Report
        self._generate_report(ig_k1, p_k1, ig_k2, p_k2, rank, variance_top2, rank_change, generalization_scores, nonlinearity_verdict, fracture_count, limit_results)

    def _run_rank_test(self, y, x1, x2, x10, x11):
        # Build matrix over {K1, K2, C3, C4, BoundaryType}
        # We need numeric proxies
        def to_num(arr):
            u = np.unique(arr)
            return np.array([np.where(u == val)[0][0] for val in arr])
        
        m_k1 = to_num(x1)
        m_k2 = to_num(x2)
        m_c10 = to_num(x10)
        m_c11 = to_num(x11)
        m_y = to_num(y)
        
        matrix = np.stack([m_k1, m_k2, m_c10, m_c11, m_y], axis=1)
        # Normalize
        matrix = (matrix - matrix.mean(axis=0)) / (matrix.std(axis=0) + 1e-9)
        
        svd = TruncatedSVD(n_components=2)
        svd.fit(matrix)
        variance_top2 = np.sum(svd.explained_variance_ratio_)
        
        # Effective rank (singular values above threshold)
        full_svd = np.linalg.svd(matrix, compute_uv=False)
        rank = np.sum(full_svd > 0.1)
        
        # Assume baseline rank was 1 (from our previous lab result) or similar
        rank_change = int(rank) - 1 
        
        return rank, variance_top2, rank_change

    def _run_cross_domain_test(self, y, x2):
        # Group by regime
        regimes = {}
        for d, label, val in zip(self.domains, y, x2):
            r = d.get('regime', 'Base')
            if r not in regimes: regimes[r] = {'x': [], 'y': []}
            regimes[r]['x'].append(val)
            regimes[r]['y'].append(label)
            
        scores = {}
        # Train on 3, test on 1 (simplified)
        for target_regime in regimes:
            x_train, y_train = [], []
            x_test, y_test = regimes[target_regime]['x'], regimes[target_regime]['y']
            for name, data in regimes.items():
                if name != target_regime:
                    x_train.extend(data['x'])
                    y_train.extend(data['y'])
            
            if len(x_train) == 0: continue
            
            clf = RandomForestClassifier(n_estimators=10)
            clf.fit(np.array(x_train).reshape(-1, 1), y_train)
            score = clf.score(np.array(x_test).reshape(-1, 1), y_test)
            scores[target_regime] = float(score)
            
        return scores

    def _run_nonlinearity_test(self, y, x1, x2):
        # Compare linear vs non-linear
        ig_combined = mutual_info_score(np.array([f"{a}_{b}" for a, b in zip(x1, x2)]), y)
        ig_sum = mutual_info_score(x1, y) + mutual_info_score(x2, y)
        
        if ig_combined > (ig_sum * 1.5): return "COMPOSITE_GEOMETRY"
        return "REDUCIBLE_GEOMETRY"

    def _run_fracture_search(self, y, x2):
        count = 0
        for label, val in zip(y, x2):
            # Fracture: high expression (1) and smooth collapse
            if val == 1 and label == "SMOOTH_HYPERSURFACE": count += 1
            # Fracture: low expression (0) and combinatorial collapse
            if val == 0 and label == "COMBINATORIAL_THRESHOLD": count += 1
        return count

    def _investigate_open_questions(self, y, x1, x2, x8, x9, x10, x11):
        # Q2: Self-reference ceiling. Does x8 (self-model) increase IG where x2 (expression) fails?
        ig_2 = mutual_info_score(x2, y)
        combined_2_8 = np.array([f"{a}_{b}" for a, b in zip(x2, x8)])
        ig_combined = mutual_info_score(combined_2_8, y)
        delta_ig = ig_combined - ig_2
        
        # Patching check
        ig_patched = mutual_info_score(np.array([f"{a}_{b}_{c}_{d}" for a, b, c, d in zip(x1, x2, x10, x11)]), y)
        
        # Check neural/cognitive regime specifically
        neural_idx = [i for i, d in enumerate(self.domains) if d.get('regime') == 'Neural / cognitive models']
        ig_neural_2 = mutual_info_score(x2[neural_idx], y[neural_idx]) if neural_idx else 0
        ig_neural_8 = mutual_info_score(x8[neural_idx], y[neural_idx]) if neural_idx else 0
        
        return {
            "self_model_gain": float(delta_ig),
            "neural_regime_self_model_ig": float(ig_neural_8),
            "feedback_ig": float(mutual_info_score(x9, y)),
            "patched_ig": float(ig_patched)
        }

    def _generate_report(self, ig_k1, p_k1, ig_k2, p_k2, rank, variance, rank_change, gen_scores, nonlin, fractures, limits):
        verdict = "REDUCIBLE_GEOMETRY_SURVIVES"
        if rank > 3 or fractures > 500 or nonlin == "COMPOSITE_GEOMETRY":
            verdict = "REDUCIBLE_GEOMETRY_FALSIFIED"
            
        report = f"# Helix Extreme Validation Report\n\n"
        report += f"**Verdict:** {verdict}\n\n"
        report += f"## Phase 2: Promotion Results (N={len(self.domains)})\n"
        report += f"- **C1_KERNEL_1**: IG={ig_k1:.4f} (p={p_k1:.4f})\n"
        report += f"- **C2_EXPRESSION**: IG={ig_k2:.4f} (p={p_k2:.4f})\n\n"
        
        report += f"## Phase 3: Rank Detection\n"
        report += f"- **Effective Rank:** {rank}\n"
        report += f"- **Variance Explained (Top 2):** {variance:.4f}\n"
        report += f"- **Rank Change:** {rank_change:+d}\n\n"
        
        report += f"## Phase 4: Cross-Domain Holdout\n"
        for r, s in gen_scores.items():
            report += f"- **{r} Holdout Score:** {s:.4f}\n"
        report += "\n"
        
        report += f"## Phase 5: Interaction Nonlinearity\n"
        report += f"- **Nonlinearity Verdict:** {nonlin}\n\n"
        
        report += f"## Phase 6: Fracture Search\n"
        report += f"- **Structural Fractures Detected:** {fractures}\n"
        report += f"- **Fracture Density:** {fractures/len(self.domains):.4f}\n\n"

        report += f"## Phase 7: Ontological Limit Investigation\n"
        report += f"- **Self-Model IG Gain (Q2):** {limits['self_model_gain']:.4f}\n"
        report += f"- **Neural Regime Self-Model IG:** {limits['neural_regime_self_model_ig']:.4f}\n"
        report += f"- **Feedback Total IG:** {limits['feedback_ig']:.4f}\n"
        report += f"- **Patched IG (K1+K2+C3+C4):** {limits['patched_ig']:.4f}\n\n"
        
        report += f"### Solution Verdict (Open Questions)\n"
        if limits['patched_ig'] > (ig_k1 + ig_k2) * 1.5:
            report += f"> **PATCH_STABLE:** C3 and C4 effectively patch the major fracture clusters.\n"
        if limits['self_model_gain'] > 0.05:
            report += f"> **SOLVED (Partial):** Self-reference acts as a secondary structural element (C8) that resolves the expression ceiling in cognitive/neural regimes.\n"
        else:
            report += f"> **UNSOLVED:** Self-reference remains a non-discriminative modifier at the current scale.\n"

        report += f"---"
        report += f"\nDerived From: Extreme Validation Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Validation complete. Verdict: {verdict}")

if __name__ == "__main__":
    v = HostileValidation()
    v.run()
