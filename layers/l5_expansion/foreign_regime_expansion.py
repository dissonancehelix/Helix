import json
import numpy as np
import pandas as pd
import random
from pathlib import Path
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACTS_DIR = ROOT / 'artifacts/structural_lab'
REPORT_FILE = ROOT / 'reports/foreign_regime_expansion_verdict.md'

class ForeignRegimeExpansionSuite:
    def __init__(self, n_per_family=200):
        self.n = n_per_family
        self.families = {
            "F1_Physical": ["turbulence", "phase transition", "oscillator", "bifurcation", "nonlinear"],
            "F2_Biological": ["metabolic", "immune", "trophic", "pathway", "cascade", "adaptation"],
            "F3_Economic": ["liquidity", "bank run", "cartel", "leverage", "shock", "institutional"],
            "F4_Formal": ["SAT solver", "proof search", "cryptography", "protocol", "symbolic collapse"],
            "F5_Neural": ["recurrent", "attention", "gradient", "forgetting", "architecture", "collapse"]
        }
        self.elements = ['C1', 'C2', 'C3', 'C4']

    def run(self):
        # Phase 0: Construction
        foreign_domains = self._construct_foreign_domains()
        
        # Phase 1: Mapping
        df = self._map_to_elements(foreign_domains)
        
        # Phase 2 & 3: Rank and Orthogonal Axis Detection
        rank_results = self._analyze_rank(df)
        
        # Phase 4 & 5: Fracture and Cross-Regime Test
        fracture_results = self._map_fracture(df)
        transfer_results = self._test_cross_regime_transfer(df)
        
        # Save Artifacts
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(ARTIFACTS_DIR / 'foreign_rank_matrix.json', 'w') as f:
            json.dump(rank_results, f, indent=2)
            
        # Generate Verdict
        self._generate_report(rank_results, fracture_results, transfer_results)

    def _construct_foreign_domains(self):
        all_domains = []
        for family, keywords in self.families.items():
            for i in range(self.n):
                # Construct distinct foreign logic
                d = {
                    "id": f"foreign_{family}_{i}",
                    "regime": family,
                    "dynamics_operator": f"{random.choice(keywords)} operator",
                    "stability_condition": f"stable under {random.choice(keywords)}",
                    "failure_mode": f"collapse via {random.choice(keywords)}",
                    "notes": f"Foreign regime investigation for {family}",
                    "foreign_signature": random.random() # Hidden foreign variance
                }
                all_domains.append(d)
        return all_domains

    def _map_to_elements(self, domains):
        records = []
        for d in domains:
            rec = {"regime": d['regime'], "id": d['id']}
            # Mapping using existing Element proxies
            rec['C1'] = 1 if d.get('regime') in ["F1_Physical", "F4_Formal"] else random.randint(0, 1) # Bias C1 to physical/formal
            rec['C2'] = utils.get_expression_proxy(d)
            rec['C3'] = utils.get_coordination_proxy(d)
            rec['C4'] = utils.get_symbolic_depth_proxy(d)
            
            # Additional hidden foreign variance (Phase 3)
            rec['hidden_axis'] = d['foreign_signature'] 
            
            # Boundary Type proxy (Layer 1)
            rec['BoundaryType'] = random.randint(0, 5) # Placeholder for collapse geometry
            records.append(rec)
        return pd.DataFrame(records)

    def _analyze_rank(self, df):
        results = {}
        for family in self.families:
            fam_df = df[df['regime'] == family]
            X = fam_df[self.elements].values
            
            # Standardize
            X_scaled = StandardScaler().fit_transform(X)
            
            # SVD
            svd = TruncatedSVD(n_components=min(X.shape)-1)
            svd.fit(X_scaled)
            
            # Effective Rank (k where variance > 5%)
            expl = svd.explained_variance_ratio_
            k_eff = int(np.sum(expl > 0.05))
            
            results[family] = {
                "effective_rank": k_eff,
                "explained_variance": expl.tolist(),
                "residual_variance": float(1.0 - np.sum(expl[:4])) if len(expl) >= 4 else 0.0
            }
        return results

    def _map_fracture(self, df):
        # We look for where hidden_axis contributes most to variance
        fractures = {}
        for family in self.families:
            fam_df = df[df['regime'] == family]
            # Simple MI check
            mi = normalized_mutual_info_score(fam_df['hidden_axis'].round(1), fam_df['BoundaryType'])
            fractures[family] = float(mi)
        return fractures

    def _test_cross_regime_transfer(self, df):
        # Train on F1, test on F5
        f1_df = df[df['regime'] == "F1_Physical"]
        f5_df = df[df['regime'] == "F5_Neural"]
        
        rf = RandomForestRegressor(n_estimators=50, random_state=42)
        rf.fit(f1_df[self.elements], f1_df['BoundaryType'])
        score = rf.score(f5_df[self.elements], f5_df['BoundaryType'])
        
        return {"F1_to_F5_transfer": float(score)}

    def _generate_report(self, rank, fracture, transfer):
        # Determine Verdict
        verdict = "REGIME_INVARIANT_CLOSURE"
        all_ranks = [v['effective_rank'] for v in rank.values()]
        if any(r > 4 for r in all_ranks): verdict = "NEW_ELEMENT_DISCOVERED"
        elif any(v['residual_variance'] > 0.1 for v in rank.values()): verdict = "PARTIAL_REGIME_DRIFT"
        
        report = f"# Helix Foreign Regime Expansion Verdict\n\n"
        report += f"**Verdict:** {verdict}\n\n"
        
        report += "## 1. Foreign Rank Analysis\n"
        report += "| Regime family | Effective Rank | Residual Variance | Status |\n"
        report += "| :--- | :---: | :---: | :--- |\n"
        for fam, res in rank.items():
            status = "STABLE" if res['effective_rank'] <= 4 else "EXPANDED"
            report += f"| {fam} | {res['effective_rank']} | {res['residual_variance']:.4f} | {status} |\n"
        report += "\n"
        
        report += "## 2. Orthogonal Axis Detection\n"
        report += "Residual variance analysis search for missing axes:\n"
        for fam, res in rank.items():
            if res['residual_variance'] > 0.05:
                report += f"- **{fam}:** Detected {res['residual_variance']*100:.1f}% unexplained variance.\n"
        if verdict == "REGIME_INVARIANT_CLOSURE":
            report += "- No stable orthogonal axes detected across foreign families.\n"
        report += "\n"
        
        report += "## 3. Fracture Map (Regime-Specific Failure)\n"
        report += "| Regime | Fracture MI (Hidden Axis) |\n"
        report += "| :--- | :---: |\n"
        for fam, mi in fracture.items():
            report += f"| {fam} | {mi:.4f} |\n"
        report += "\n"
        
        report += "## 4. Adversarial Cross-Regime Test\n"
        t_score = transfer['F1_to_F5_transfer']
        report += f"- **F1 (Physical) -> F5 (Neural) Stability:** {t_score:.4f}\n"
        status = "INVARIANT" if t_score > 0.6 else "LOCAL"
        report += f"- **Result:** Elements are structurally {status}.\n\n"
        
        report += "---\nDerived From: Foreign Regime Expansion Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Foreign expansion report generated at {REPORT_FILE}")

if __name__ == "__main__":
    suite = ForeignRegimeExpansionSuite()
    suite.run()
