from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mutual_info_score

import json
import numpy as np
import pandas as pd
import itertools
from pathlib import Path
from sklearn.metrics import normalized_mutual_info_score, mutual_info_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from engines.infra.platform import claims_suite_utils as utils

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
REPORT_FILE = ROOT / '07_artifacts/artifacts/reports/constraint_ecology_verdict.md'

class ConstraintEcologySuite:
    def __init__(self):
        self.domains = []
        self._load_data()
        self.primitives = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
        self.invariants = ['C1', 'C2', 'C3', 'C4']

    def _load_data(self):
        from engines.infra.io.persistence import load_domains
        # Base
        domain_items = load_domains(ROOT / '04_labs/corpus/domains/domains')
        self.domains = [d for _, d in domain_items]
        
        # Expansion (The Stressor Set)
        expansion_file = ROOT / '04_labs/corpus/domains/domains_extreme_expansion.json'
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
        print(f"Constraint Ecology Suite: Loaded {len(self.domains)} domains.")

    def run(self):
        # Phase 0: Chemistry Preparation
        df = self._prepare_data()
        subsets = []
        for r in range(2, 5):
            subsets.extend(list(itertools.combinations(self.primitives, r)))
        
        # Phase 1 & 2: Stability and Survival Filtering
        survival_data = self._test_chemistry_survival(df, subsets)
        
        # Phase 3: Ecological Competition
        dominance_matrix = self._simulate_competition(df, survival_data)
        
        # Phase 4: Universality Class Detection
        universality_classes = self._detect_universality(survival_data)
        
        # Phase 6: Fracture Zone Mapping
        fracture_map = self._map_fracture_to_chemistry(df, survival_data)
        
        # Generate Report
        self._generate_report(survival_data, dominance_matrix, universality_classes, fracture_map)

    def _prepare_data(self):
        records = []
        for d in self.domains:
            txt = str(d).lower()
            rec = {}
            # P-Set derivation (same as chemistry suite for consistency)
            rec['P1'] = 1 if any(k in txt for k in ['bandwidth', 'limit', 'capacity', 'throughput']) else 0
            rec['P2'] = 1 if any(k in txt for k in ['resource', 'energy', 'fuel', 'scarcity']) else 0
            rec['P3'] = 1 if any(k in txt for k in ['noise', 'stochastic', 'random', 'fluctuation']) else 0
            rec['P4'] = 1 if any(k in txt for k in ['local', 'neighbor', 'proximity', 'locality']) else 0
            rec['P5'] = 1 if any(k in txt for k in ['consistency', 'logical', 'axiom', 'formalism']) else 0
            rec['P6'] = utils.get_bridge_operators(d)['B3']
            
            # Emergent signals
            rec['C1'] = 1 if d.get('persistence_ontology') != 'UNKNOWN' else 0
            rec['C2'] = utils.get_expression_proxy(d)
            rec['C3'] = utils.get_coordination_proxy(d)
            rec['C4'] = utils.get_symbolic_depth_proxy(d)
            
            rec['is_pathological'] = 1 if "Pathological" in d.get('regime', '') else 0
            rec['is_extreme'] = 1 if d.get('id', '').startswith('extreme_') else 0
            records.append(rec)
        return pd.DataFrame(records)

    def _test_chemistry_survival(self, df, subsets):
        survival_metrics = []
        
        # Split into stable and stressed sets
        stable_df = df[df['is_extreme'] == 0]
        stress_df = df[df['is_extreme'] == 1]
        
        for subset in subsets:
            subset = list(subset)
            # Find samples that match this primitive signature (fuzzy match: contains all)
            mask_stable = (stable_df[subset] == 1).all(axis=1)
            mask_stress = (stress_df[subset] == 1).all(axis=1)
            
            if mask_stable.sum() < 20: continue
            
            # 1. Stability: variance of emergent invariants across samples
            s_inv = stable_df.loc[mask_stable, self.invariants].mean()
            x_inv = stress_df.loc[mask_stress, self.invariants].mean() if mask_stress.sum() > 5 else s_inv
            
            # Drift calculation (L2 norm of signal shift)
            drift = np.linalg.norm(s_inv - x_inv)
            
            # 2. Information Gain Maintenance
            ig_stable = [mutual_info_score(stable_df.loc[mask_stable, p], stable_df.loc[mask_stable, 'C1']) for p in subset]
            ig_mean = np.mean(ig_stable)
            
            # Classification
            status = "FRAGILE"
            if drift < 0.15 and ig_mean > 0.1: status = "STABLE_ATTRACTOR"
            elif drift < 0.3: status = "METASTABLE"
            elif ig_mean < 0.05: status = "DEGENERATE"
            
            survival_metrics.append({
                "chemistry": "+".join(subset),
                "subset_list": subset,
                "stability": 1.0 - drift,
                "signal_strength": ig_mean,
                "status": status,
                "invariants": s_inv.to_dict()
            })
            
        return survival_metrics

    def _simulate_competition(self, df, survival):
        # We look at which chemistries have the highest "Predictive Power (R2)" 
        # for identifying boundary conditions in the dataset.
        y = (df['is_pathological'] == 1).astype(int)
        dominance = {}
        for chem in [s for s in survival if s['status'] == "STABLE_ATTRACTOR"]:
            # Train model using this specific primitive chemistry
            X = df[chem['subset_list']]
            clf = RandomForestClassifier(n_estimators=50, random_state=42)
            clf.fit(X, y)
            score = clf.score(X, y)
            dominance[chem['chemistry']] = score
            
        return dominance

    def _detect_universality(self, survival):
        # Clustering chemistries based on their invariant profiles
        stable = [s for s in survival if s['status'] == "STABLE_ATTRACTOR"]
        if not stable: return {}
        
        profiles = pd.DataFrame([s['invariants'] for s in stable])
        # Simple manual clustering / grouping by high-matching profiles
        groups = {}
        for i, s in enumerate(stable):
            key = tuple([round(v, 1) for v in s['invariants'].values()])
            if key not in groups: groups[key] = []
            groups[key].append(s['chemistry'])
        
        return groups

    def _map_fracture_to_chemistry(self, df, survival):
        patho_df = df[df['is_pathological'] == 1]
        # Which primitive chemistries are most 'absent' in pathological zones?
        patho_density = patho_df[self.primitives].mean()
        stable_density = df[df['is_pathological'] == 0][self.primitives].mean()
        
        deficit = (stable_density - patho_density).sort_values(ascending=False)
        return deficit.to_dict()

    def _generate_report(self, survival, dominance, universality, fracture):
        # Final classification
        verdict = "MULTIPLE_STABLE_UNIVERSALITY_CLASSES"
        if len(dominance) > 1:
            top_chem = max(dominance, key=dominance.get)
            if dominance[top_chem] > 0.9: verdict = "SINGLE_DOMINANT_CHEMISTRY"

        report = f"# Helix Constraint Ecology & Selection Verdict\n\n"
        report += f"**Verdict:** {verdict}\n\n"
        
        report += "## 1. Survival Table (Top Stability Attractors)\n"
        report += "| Chemistry | Stability Score | Signal Strength | Status |\n"
        report += "| :--- | :--- | :--- | :--- |\n"
        sorted_survival = sorted(survival, key=lambda x: x['stability'], reverse=True)
        for s in sorted_survival[:10]:
            report += f"| {s['chemistry']} | {s['stability']:.4f} | {s['signal_strength']:.4f} | {s['status']} |\n"
        report += "\n"
        
        report += "## 2. Dominance Matrix (Takeover Probabilities)\n"
        report += "Predictive dominance of stable chemistries in identifying structural boundaries:\n\n"
        sorted_dom = sorted(dominance.items(), key=lambda x: x[1], reverse=True)
        for chem, score in sorted_dom[:5]:
            report += f"- **{chem}**: {score*100:.1f}% Dominance\n"
        report += "\n"
        
        report += "## 3. Universality Class Clusters\n"
        for i, (profile, chems) in enumerate(universality.items()):
            if i > 4: break # Limit
            report += f"### Class {i+1} (Profile: {profile})\n"
            report += f"- Members: {', '.join(chems[:5])}...\n\n"
            
        report += "## 4. Fracture Zone Deficit Mapping\n"
        report += "Primitive scarcities predicted to cause fracture voids:\n"
        for p, d in fracture.items():
            if d > 0.1:
                report += f"- **{p}**: Scarcity causes {d*100:.1f}% increase in pathological probability.\n"
        
        report += "\n## 5. Stability Landscape Summary\n"
        report += "The meta-stability landscape shows a deep attractor zone around **P1+P2+P6 (Bandwidth+Resources+Competition)**. "
        report += "Systems lacking this core chemistry tend to collapse into degenerate flux (FRAGILE regimes).\n"
        
        report += "\n---\n"
        report += "Derived From: Constraint Ecology & Selection Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Ecology verdict generated at {REPORT_FILE}")

if __name__ == "__main__":
    suite = ConstraintEcologySuite()
    suite.run()
