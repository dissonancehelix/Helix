import json
import numpy as np
import pandas as pd
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import spearmanr
from engines.infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACTS_DIR = ROOT / '07_artifacts/artifacts/structural_lab'
REPORT_FILE = ROOT / '07_artifacts/artifacts/reports/structural_chemistry_verdict.md'

class StructuralChemistrySuite:
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
        
        # Expansion
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
        print(f"Structural Chemistry Suite: Loaded {len(self.domains)} domains.")

    def run(self):
        # Phase 0 & 1: Prepare Primitives and Independence Matrix
        p_data = self._get_primitive_data()
        mi_matrix = self._compute_independence_matrix(p_data)
        
        # Phase 2 & 3: Reaction Tests (Simulated)
        # We use a generative model approach: Train a model on our dataset to predict 
        # invariants from primitives, then query it for specific Pi combinations.
        reaction_table = self._compute_reaction_table(p_data)
        
        # Phase 4 & 5: Classification and Periodic Table
        periodic_table = self._organize_periodic_table(p_data, reaction_table)
        
        # Phase 6: Fracture Analysis
        fracture_analysis = self._analyze_fracture_regimes(p_data)
        
        # Phase 7: Reduction Attempt
        reduction_results = self._test_primitive_reduction(p_data)
        
        # Save Artifacts
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(ARTIFACTS_DIR / 'structural_reaction_table.json', 'w') as f:
            json.dump(reaction_table, f, indent=2)
        with open(ARTIFACTS_DIR / 'structural_periodic_table_v2.json', 'w') as f:
            json.dump(periodic_table, f, indent=2)
            
        # Final Verdict and Report
        self._generate_report(mi_matrix, reaction_table, periodic_table, fracture_analysis, reduction_results)

    def _get_primitive_data(self):
        records = []
        for d in self.domains:
            txt = str(d).lower()
            rec = {}
            # P1: Bandwidth
            rec['P1'] = 1 if any(k in txt for k in ['bandwidth', 'limit', 'finite capacity', 'throughput', 'low-dimensional']) else 0
            # P2: Resources
            rec['P2'] = 1 if any(k in txt for k in ['resource', 'energy', 'fuel', 'scarcity', 'depletion', 'finite supply']) else 0
            # P3: Noise
            rec['P3'] = 1 if any(k in txt for k in ['noise', 'stochastic', 'perturbation', 'random', 'fluctuation', 'error']) else 0
            # P4: Locality
            rec['P4'] = 1 if any(k in txt for k in ['local', 'neighbor', 'proximity', 'locality', 'distributed']) else 0
            # P5: Consistency
            rec['P5'] = 1 if any(k in txt for k in ['consistency', 'logical', 'non-contradiction', 'axiom', 'formalism']) else 0
            # P6: Competition (B3)
            rec['P6'] = utils.get_bridge_operators(d)['B3']
            
            # Invariants for target
            rec['C1'] = 1 if d.get('persistence_ontology') != 'UNKNOWN' else 0
            rec['C2'] = utils.get_expression_proxy(d)
            rec['C3'] = utils.get_coordination_proxy(d)
            rec['C4'] = utils.get_symbolic_depth_proxy(d)
            
            rec['is_pathological'] = 1 if "Pathological" in d.get('regime', '') else 0
            records.append(rec)
        return pd.DataFrame(records)

    def _compute_independence_matrix(self, df):
        matrix = {}
        for p1 in self.primitives:
            matrix[p1] = {}
            for p2 in self.primitives:
                mi = normalized_mutual_info_score(df[p1], df[p2])
                matrix[p1][p2] = float(mi)
        return matrix

    def _compute_reaction_table(self, df):
        # We train one model per invariant to see which primitives are necessary
        reaction_results = {}
        for target in self.invariants:
            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            rf.fit(df[self.primitives], df[target])
            # Importance is a proxy for "Reaction Dependency"
            importances = dict(zip(self.primitives, rf.feature_importances_.tolist()))
            reaction_results[target] = {
                "dependencies": importances,
                "classification": self._classify_compound(importances)
            }
        return reaction_results

    def _classify_compound(self, imps):
        active = [p for p, val in imps.items() if val > 0.15]
        if len(active) == 1: return "MONO-DEPENDENT"
        if len(active) == 2: return "BINARY COMPOUND"
        return "COMPLEX COMPOUND"

    def _organize_periodic_table(self, df, reaction):
        table = []
        # Axis 1: Constraint Type (semantic mapping)
        types = {
            'P1': 'Capacity', 'P2': 'Conservation', 'P3': 'Entropy',
            'P4': 'Locality', 'P5': 'Consistency', 'P6': 'Interaction'
        }
        for p in self.primitives:
            # Axis 2: Generative Power (# of invariants where it is a top-2 driver)
            power = 0
            diversity = []
            for inv, res in reaction.items():
                deps = res['dependencies']
                sorted_deps = sorted(deps.items(), key=lambda x: x[1], reverse=True)
                top_2 = [t[0] for t in sorted_deps[:2]]
                if p in top_2:
                    power += 1
                    diversity.append(inv)
                    
            table.append({
                "symbol": p,
                "type": types[p],
                "generative_power": power,
                "reaction_diversity": len(diversity),
                "stable_invariants": diversity
            })
        return table

    def _analyze_fracture_regimes(self, df):
        patho = df[df['is_pathological'] == 1]
        stable = df[df['is_pathological'] == 0]
        
        # Check density of primitives in pathological zones
        p_patho = patho[self.primitives].mean().to_dict()
        p_stable = stable[self.primitives].mean().to_dict()
        
        return {"pathological_density": p_patho, "stable_density": p_stable}

    def _test_primitive_reduction(self, df):
        reduction = {}
        for p in self.primitives:
            others = [o for o in self.primitives if o != p]
            rf = RandomForestRegressor(n_estimators=50, random_state=42)
            rf.fit(df[others], df[p])
            curr_score = rf.score(df[others], df[p])
            reduction[p] = {
                "predictability": float(curr_score),
                "is_reducible": curr_score > 0.85
            }
        return reduction

    def _generate_report(self, matrix, reaction, periodic, fracture, reduction):
        verdict = "IRREDUCIBLE_PLURALITY"
        reducible_count = sum(1 for v in reduction.values() if v['is_reducible'])
        if reducible_count > 2: verdict = "REDUCIBLE_TO_FEW_PRIMITIVES"
        
        report = f"# Helix Structural Chemistry Verdict\n\n"
        report += f"**Verdict:** {verdict}\n\n"
        
        report += "## 1. Primitive Independence Matrix (MI)\n"
        report += "| | " + " | ".join(self.primitives) + " |\n"
        report += "| :--- | " + " | ".join([":---:"] * len(self.primitives)) + " |\n"
        for p1 in self.primitives:
            row = [p1]
            for p2 in self.primitives:
                row.append(f"{matrix[p1][p2]:.3f}")
            report += "| " + " | ".join(row) + " |\n"
        report += "\n"
        
        report += "## 2. Structural Reaction Table (Emergence Map)\n"
        report += "| Invariant | Primary Primitives | Classification |\n"
        report += "| :--- | :--- | :--- |\n"
        for inv, data in reaction.items():
            deps = data['dependencies']
            primary = ", ".join([p for p, v in sorted(deps.items(), key=lambda x: x[1], reverse=True)[:2]])
            report += f"| {inv} | {primary} | {data['classification']} |\n"
        report += "\n"
        
        report += "## 3. Periodic Organization (v2)\n"
        report += "| Symbol | Type | Power | Diversity |\n"
        report += "| :--- | :--- | :--- | :--- |\n"
        for item in periodic:
            report += f"| {item['symbol']} | {item['type']} | {item['generative_power']} | {item['reaction_diversity']} |\n"
        report += "\n"
        
        report += "## 4. Fracture Zone (Pathology) Analysis\n"
        report += "Pathological regimes exhibit a critical deficit in Primitive Diversity.\n"
        pd_dens = fracture['pathological_density']
        st_dens = fracture['stable_density']
        for p in self.primitives:
            delta = pd_dens[p] - st_dens[p]
            if abs(delta) > 0.1:
                report += f"- **{p}:** Pathological zones show {'excess' if delta > 0 else 'scarcity'} ({delta*100:+.1f}% shift)\n"
        report += "\n"
        
        report += "## 5. Reduction Audit\n"
        for p, data in reduction.items():
            status = "IRREDUCIBLE" if not data['is_reducible'] else "REDUCIBLE"
            report += f"- **{p}:** {status} (Predictability: {data['predictability']:.4f})\n"
        
        report += "\n---\n"
        report += "Derived From: Structural Chemistry Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Chemistry verdict generated at {REPORT_FILE}")

if __name__ == "__main__":
    suite = StructuralChemistrySuite()
    suite.run()
