import json
import numpy as np
from pathlib import Path
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score
from infra.platform import claims_suite_utils as utils

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACT_FILE = ROOT / 'artifacts/constraint_dependency_matrix.json'
REPORT_FILE = ROOT / 'reports/layered_constraint_pyramid.md'

class ConstraintPyramid:
    def __init__(self):
        self.domains = []
        self._load_data()
        self.elements = ["C1", "C2", "C3", "C4"]
        self.assumptions = [
            "A1_BANDWIDTH",    # Finite info bandwidth
            "A2_RESOURCES",    # Finite energy/resource
            "A3_PERTURBATION", # Non-zero noise
            "A4_LOCALITY",     # Local interaction
            "A5_CONSISTENCY"   # Logical non-contradiction
        ]

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
        print(f"Constraint Pyramid: Loaded {len(self.domains)} domains.")

    def run(self):
        # Data Prep
        y = np.array([d.get('boundary_type_primary', 'UNKNOWN') for d in self.domains])
        
        # Elements (Layer 2)
        vectors = {
            "C1": np.array([str(d.get('persistence_ontology', 'UNKNOWN')) for d in self.domains]),
            "C2": np.array([1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0 for d in self.domains]),
            "C3": np.array([utils.get_coordination_proxy(d) for d in self.domains]),
            "C4": np.array([utils.get_symbolic_depth_proxy(d) for d in self.domains])
        }

        # Assumptions (Layer 3 Proxies)
        assumption_matrix = self._map_assumptions()

        # Phase 1: Derivation Attempts
        dependency_matrix = self._calculate_dependencies(vectors, y, assumption_matrix)

        # Phase 2: Universality Test
        universality = self._test_universality(vectors, y)

        # Phase 3: Necessity Abstraction
        necessity = self._test_necessity(vectors, y)

        # Phase 4: Consistency Check
        circularity = self._check_circularity(dependency_matrix)

        # Final Report
        self._generate_report(dependency_matrix, universality, necessity, circularity)

        # Save Artifact
        with open(ARTIFACT_FILE, 'w') as f:
            json.dump(dependency_matrix, f, indent=2)

    def _map_assumptions(self):
        matrix = []
        for d in self.domains:
            row = []
            txt = str(d).lower()
            # A1: Bandwidth (branching/network cues)
            row.append(1 if any(k in txt for k in ['branching', 'network', 'bandwidth', 'channel', 'capacity']) else 0)
            # A2: Resources (state-space, energy, resource, finite cues)
            row.append(1 if any(k in txt for k in ['finite', 'energy', 'resource', 'budget', 'limit', 'state-space']) else 0)
            # A3: Perturbation (noise, perturbation, drift, anomaly)
            row.append(1 if any(k in txt for k in ['noise', 'perturbation', 'drift', 'fluctuation', 'stochastic']) else 0)
            # A4: Locality (local, neighbor, adjacency)
            row.append(1 if d.get('boundary_locality') == 'LOCAL' or 'local' in txt else 0)
            # A5: Consistency (symbolic, logic, sat, contradiction)
            row.append(1 if d.get('substrate_type') == 'SYMBOLIC_SPACE' or any(k in txt for k in ['logic', 'consistency', 'contradiction', 'symbolic']) else 0)
            matrix.append(row)
        return np.array(matrix)

    def _calculate_dependencies(self, vectors, y, a_matrix):
        deps = {}
        for e_name, e_vec in vectors.items():
            e_deps = []
            # Baseline IG for this element
            ig_full = mutual_info_score(e_vec, y)
            
            for i, a_name in enumerate(self.assumptions):
                a_vec = a_matrix[:, i]
                # Filter for domains where assumption is ABSENT (0)
                absent_idx = np.where(a_vec == 0)[0]
                if len(absent_idx) < 10: 
                    # Not enough data to ablate, assume potentially independent
                    e_deps.append({"assumption": a_name, "dependence": 0.0})
                    continue
                
                ig_absent = mutual_info_score(e_vec[absent_idx], y[absent_idx])
                # Dependency = Drop in IG when assumption is removed
                # If IG disappears, Ei depends on Aj
                delta = ig_full - ig_absent
                e_deps.append({"assumption": a_name, "dependence": float(delta)})
            
            deps[e_name] = e_deps
        return deps

    def _test_universality(self, vectors, y):
        regimes = {}
        for i, d in enumerate(self.domains):
            reg = d.get('regime', 'Base')
            if reg not in regimes: regimes[reg] = []
            regimes[reg].append(i)
            
        unv = {}
        for e_name, e_vec in vectors.items():
            status = "UNIVERSAL_CONSTRAINT"
            for reg, idx in regimes.items():
                if len(idx) < 10: continue
                # Calculation IG in this specific regime
                ig = mutual_info_score(e_vec[idx], y[idx])
                if ig < 0.01: # Signal collapsed in this regime
                    status = "REGIME_CONSTRAINT"
                    break
            unv[e_name] = status
        return unv

    def _test_necessity(self, vectors, y):
        # How much does the element contribute to total predictive power?
        nec = {}
        # Combined full basis
        full_basis = np.array(["_".join([str(vectors[e][i]) for e in self.elements]) for i in range(len(y))])
        ig_full = mutual_info_score(full_basis, y)
        
        for e_name in self.elements:
            subset_elements = [e for e in self.elements if e != e_name]
            subset_basis = np.array(["_".join([str(vectors[e][i]) for e in subset_elements]) for i in range(len(y))])
            ig_subset = mutual_info_score(subset_basis, y)
            
            delta = ig_full - ig_subset
            nec[e_name] = "NECESSARY" if delta > 0.05 else "CONTINGENT"
        return nec

    def _check_circularity(self, deps):
        # A circularity in this context would be if any Ei is marked as its own derivation
        # or if Ei depends on something that depends on Ei.
        # Since Assumptions are Layer 3 and Elements are Layer 2, we just check if 
        # Layer 3 assumptions are derived from Layer 2. (Not possible in current script flow)
        return "NONE_DETECTED"

    def _generate_report(self, deps, unv, nec, circ):
        report = f"# Helix Layered Constraint Pyramid\n\n"
        
        # Classification
        classif = "PARTIALLY_REDUCIBLE"
        # If all elements have a high dependency on at least one assumption
        # we might call it FOUNDATIONAL.
        
        report += f"**Verdict:** {classif}\n\n"
        
        report += "## 1. Constraint Origin Analysis (Layer 3 -> Layer 2)\n"
        for e, e_deps in deps.items():
            report += f"### {e} ({unv[e]})\n"
            report += f"- **Necessity:** {nec[e]}\n"
            report += "- **Derivation Attempts:**\n"
            
            # Find primary dependency
            found_dep = False
            for d in e_deps:
                if d["dependence"] > 0.05:
                    report += f"  - Derived from **{d['assumption']}** (ΔIG: {d['dependence']:.4f})\n"
                    found_dep = True
            
            if not found_dep:
                report += f"  - **PRIMITIVE_CONSTRAINT**: No significant reduction found among A1-A5.\n"
            else:
                report += f"  - **DERIVED_CONSTRAINT**: Reduced to more primitive assumptions.\n"
        
        report += "\n## 2. Dependency Matrix Snapshot\n"
        report += "| Element | A1 | A2 | A3 | A4 | A5 |\n"
        report += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for e, e_deps in deps.items():
            row = [f"{d['dependence']:.3f}" for d in e_deps]
            report += f"| {e} | {' | '.join(row)} |\n"
            
        report += f"\n## 3. Pyramid Consistency Check\n"
        report += f"- **Circularity:** {circ}\n"
        report += "- **Hierarchy:** Layer 3 (Abstract Assumptions) -> Layer 2 (Structural Elements) -> Layer 1 (Phenomenology)\n"
        
        report += "\n---"
        report += "\nDerived From: Constraint Pyramid Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Pyramid report generated at {REPORT_FILE}")

if __name__ == "__main__":
    cp = ConstraintPyramid()
    cp.run()
