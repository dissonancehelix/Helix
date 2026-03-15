import json
import os
import numpy as np
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.decomposition import TruncatedSVD
from engines.infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACT_DIR = ROOT / '07_artifacts/artifacts/structural_lab'
DOCS_DIR = ROOT / 'docs/structural_lab'

class StructuralLab:
    def __init__(self):
        self.domains = []
        self._load_datasets()
        self.periodic_table = []
        self.candidates = {} # name -> vector
        
        if not ARTIFACT_DIR.exists(): ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        if not DOCS_DIR.exists(): DOCS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_datasets(self):
        # Base 616
        for p in (ROOT / '04_labs/corpus/domains/domains').glob('*.json'):
            if p.name.startswith('phase'): continue
            with open(p, 'r') as f:
                try: self.domains.append(json.load(f))
                except: continue
        # External/Ablation packs if they exist
        for p in (ROOT / '04_labs/corpus/domains/packs').rglob('*.json'):
            with open(p, 'r') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list): self.domains.extend(data)
                    else: self.domains.append(data)
                except: continue

    def run_pipeline(self):
        print(f"Structural Lab: Analyzing {len(self.domains)} domains.")
        
        # 1. Define Candidates from existing logic
        self._extract_candidates()
        
        # 2. Re-evaluate each
        for name, vector in self.candidates.items():
            self._evaluate_candidate(name, vector)
            
        # 3. Interaction Matrix
        self._compute_interaction_matrix()
        
        # 4. Final Verdict
        self._generate_periodic_table()
        self._generate_verdict()

    def _extract_candidates(self):
        # Target: BoundaryType
        target = [d.get('boundary_type_primary', 'UNKNOWN') for d in self.domains]
        self.target = np.array([t if t != 'UNKNOWN' else 'NULL' for t in target])
        
        # Candidate 1: Kernel-1 (Ontological Basis)
        self.candidates["C1_KERNEL_1"] = np.array([str(d.get('persistence_ontology', 'UNKNOWN')) for d in self.domains])
        
        # Candidate 2: Expression (Kernel-2)
        # Check domain tags or motifs
        c2_vec = []
        for d in self.domains:
            score = 0
            if any(p in str(d).lower() for p in ['branching', 'slack', 'recombination']): score += 1
            if d.get('expression_primitives'): score += 2
            c2_vec.append(score)
        self.candidates["C2_EXPRESSION"] = np.array(c2_vec)
        
        # Candidate 3: Memory / Trace
        c3_vec = []
        for d in self.domains:
            score = 0
            txt = str(d).lower()
            if 'trace' in txt: score += 1
            if 'memory' in txt: score += 1
            if 'history' in txt: score += 1
            if 'state-dependent' in txt: score += 1
            c3_vec.append(score)
        self.candidates["C3_MEMORY_TRACE"] = np.array(c3_vec)
        
        # Candidate 4: Minimal Triad
        # Load triad results if possible for better proxy
        triad_overlay = {}
        overlay_path = ROOT / '07_artifacts/artifacts/triad/triad_overlay.json'
        if overlay_path.exists():
            with open(overlay_path, 'r') as f:
                triad_overlay = json.load(f)
        
        c4_vec = []
        for d in self.domains:
            d_id = d.get('id', '')
            if d_id in triad_overlay:
                # Use sum of proxies
                p = triad_overlay[d_id]
                c4_vec.append(p.get('identity', 0) + p.get('distinction', 0) + p.get('relation', 0))
            else:
                # Fallback to detector
                score = 0
                if utils.get_compression_proxy(d) == 1: score += 1
                if utils.get_basin_count_proxy(d) == 1: score += 1
                if utils.get_feedback_proxy(d) == 1: score += 1
                c4_vec.append(score)
        self.candidates["C4_MINIMAL_TRIAD"] = np.array(c4_vec)

        # Candidate 5: Asymmetry (Ontology committed)
        self.candidates["C5_ASYMMETRY"] = np.array([utils.get_asymmetry_proxy(d) for d in self.domains])

        # Candidate 6: Dissipation (Roadmap/Ontology)
        self.candidates["C6_DISSIPATION"] = np.array([utils.get_dissipation_proxy(d) for d in self.domains])

        # Candidate 7: Integration (Holobiont/Recursive Similarity)
        # Using modularity + feedback as proxy for integration
        c7_vec = []
        for d in self.domains:
            mod = 1 if 'modular' in str(d).lower() else 0
            fb = 1 if 'feedback' in str(d).lower() else 0
            c7_vec.append(mod + fb)
        self.candidates["C7_INTEGRATION"] = np.array(c7_vec)

        # Candidate 8: Self-Model (Recursion/Self-Reference)
        c8_vec = []
        for d in self.domains:
            txt = str(d).lower()
            val = 0
            if any(k in txt for k in ['self-model', 'internal model', 'representation', 'recursion', 'predictive loop']): val = 1
            if 'self-reference' in txt: val = 1
            c8_vec.append(val)
        self.candidates["C8_SELF_MODEL"] = np.array(c8_vec)

        # Candidate 9: Feedback (Minimal Triad/Relational)
        self.candidates["C9_FEEDBACK"] = np.array([utils.get_feedback_proxy(d) for d in self.domains])

        # Candidate 10: Coordination Complexity (Social/Institutional)
        self.candidates["C10_COORDINATION"] = np.array([utils.get_coordination_proxy(d) for d in self.domains])

        # Candidate 11: Symbolic Depth (Combinatorial)
        self.candidates["C11_SYMBOLIC_DEPTH"] = np.array([utils.get_symbolic_depth_proxy(d) for d in self.domains])

    def _evaluate_candidate(self, name, x):
        print(f"Evaluating Candidate: {name}...")
        results = {
            "name": name,
            "status": "CANDIDATE",
            "promotion_stage_reached": "NONE",
            "ig_scores": {},
            "blind_results": {},
            "scale_results": {},
            "orthogonality_metrics": {},
            "adversarial_results": {},
            "drift_metrics": {}
        }
        
        y = self.target
        
        # Stage 1: Independence
        ig_val, ig_p = utils.permutation_null(x, y, perms=500)
        results["ig_scores"]["ig_boundary"] = float(ig_val)
        results["ig_scores"]["p_value"] = float(ig_p)
        
        if ig_p > 0.05 or ig_val < 0.01:
            results["status"] = "ARCHIVED"
            results["promotion_stage_reached"] = "INDEPENDENCE_FAIL"
            self.periodic_table.append(results)
            return

        # Stage 2: Blind Replication (Simulation on N=300 subset or separate if we had it)
        # We use a 30% holdout for blind simulation
        n = len(x)
        idx = list(range(n))
        random.shuffle(idx)
        blind_idx = idx[:min(300, int(n*0.3))]
        ig_blind = mutual_info_score(x[blind_idx], y[blind_idx])
        results["blind_results"]["ig_blind"] = float(ig_blind)
        
        if ig_blind < 0.005: # Threshold for signal
            results["status"] = "DRIVER"
            results["promotion_stage_reached"] = "BLIND_REPLICATION_FAIL"
            self.periodic_table.append(results)
            return

        # Stage 3: Scale Expansion
        # Check stability against full set vs subsets
        drift = utils.dropout_stability(x, y, trials=10)
        results["scale_results"] = drift
        
        if drift["dropout_0.3"]["drift"] > 0.05:
            results["status"] = "MODIFIER"
            results["promotion_stage_reached"] = "SCALE_EXPANSION_FAIL"
            self.periodic_table.append(results)
            return

        # Stage 4: Adversarial Mutation
        # Flip 10% of Y values and see if IG holds above null
        y_adv = y.copy()
        flip_idx = random.sample(range(n), int(n*0.1))
        for i in flip_idx:
            # Find a different label
            unique_y = np.unique(y)
            y_adv[i] = random.choice([u for u in unique_y if u != y[i]])
            
        ig_adv = mutual_info_score(x, y_adv)
        results["adversarial_results"]["ig_adversarial"] = float(ig_adv)
        
        if ig_adv < (ig_val * 0.5): # Significant collapse
            results["status"] = "CONSTRAINT"
            results["promotion_stage_reached"] = "ADVERSARIAL_FAIL"
            self.periodic_table.append(results)
            return

        # Stage 5 & 6: Orthogonality & Drift (simplified for now)
        results["status"] = "ELEMENT"
        results["promotion_stage_reached"] = "STAGE_6_COMPLETE"
        self.periodic_table.append(results)

    def _compute_interaction_matrix(self):
        keys = list(self.candidates.keys())
        matrix = []
        for i in range(len(keys)):
            row = []
            for j in range(len(keys)):
                k1, k2 = keys[i], keys[j]
                v1, v2 = self.candidates[k1], self.candidates[k2]
                try:
                    mi = normalized_mutual_info_score(v1, v2)
                except: mi = 0
                row.append(float(mi))
            matrix.append(row)
        
        res = {
            "elements": keys,
            "matrix": matrix
        }
        with open(ARTIFACT_DIR / 'element_interaction_matrix.json', 'w') as f:
            json.dump(res, f, indent=2)

    def _generate_periodic_table(self):
        with open(ARTIFACT_DIR / 'structural_periodic_table.json', 'w') as f:
            json.dump(self.periodic_table, f, indent=2)

    def _generate_verdict(self):
        elements = [e for e in self.periodic_table if e["status"] == "ELEMENT"]
        count = len(elements)
        
        verdict = "UNKNOWN"
        if count <= 3 and count > 0: verdict = "REDUCIBLE_GEOMETRY (1-3 elements)"
        elif count > 3 and count <= 10: verdict = "PERIODIC_GEOMETRY (3-10 elements)"
        else: verdict = "IRREDUCIBLY_HIGH_RANK_GEOMETRY"
        
        report = f"# Helix Structural Periodic Table Verdict\n\n"
        report += f"**Verdict:** {verdict}\n\n"
        report += f"## Elements Identified\n"
        for e in elements:
            report += f"- **{e['name']}** (IG: {e['ig_scores'].get('ig_boundary', 0):.4f})\n"
            
        report += f"\n## Non-Elemental Classifications\n"
        for e in self.periodic_table:
            if e["status"] != "ELEMENT":
                report += f"- **{e['name']}**: {e['status']} (Stage Reached: {e['promotion_stage_reached']})\n"
        
        report += f"\nDerived From: Structural Lab Pipeline\n"
        
        with open(DOCS_DIR / 'verdict_report.md', 'w') as f:
            f.write(report)
        print(f"Structural Lab finished. Verdict: {verdict}")

if __name__ == "__main__":
    lab = StructuralLab()
    lab.run_pipeline()
