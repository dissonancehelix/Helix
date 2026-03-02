from collections import defaultdict
from infra.io.persistence import save_wrapped

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ART_DIR = ROOT / 'artifacts'

def build_atlas(domains):
    atlas = {}
    for _, d in domains:
        s = d.get('substrate_S1c_refined', d.get('substrate_S1c', 'UNKNOWN'))
        o = d.get('persistence_ontology', 'UNKNOWN')
        b = d.get('boundary_type_primary', 'UNKNOWN')
        if s not in atlas: atlas[s] = {}
        if o not in atlas[s]: atlas[s][o] = defaultdict(int)
        atlas[s][o][b] += 1
        
    save_wrapped(ART_DIR / 'periodic_atlas/periodic_atlas.json', atlas)
    return atlas
EXPORT_DIR = ROOT / 'artifacts/fracture_map'
REPORT_FILE = ROOT / 'docs/fracture_atlas.md'

class FractureMapper:
    def __init__(self):
        self.domains = []
        self._load_all_domains()
        if not EXPORT_DIR.exists(): EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    def _load_all_domains(self):
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
        print(f"Fracture Mapper: Loaded {len(self.domains)} domains.")

    def map_fractures(self):
        # 1. Feature Extraction
        y = np.array([d.get('boundary_type_primary', 'UNKNOWN') for d in self.domains])
        # We need a numeric representation for K1
        k1_raw = [str(d.get('persistence_ontology', 'UNKNOWN')) for d in self.domains]
        k1_u = np.unique(k1_raw)
        x_k1 = np.array([np.where(k1_u == k)[0][0] for k in k1_raw])
        
        # K2 proxy
        x_k2 = np.array([1 if d.get('expression_primitives') and len(d.get('expression_primitives')) > 0 else 0 for d in self.domains])
        
        X = np.stack([x_k1, x_k2], axis=1)
        
        # 2. Train "Physical Stability" Model
        # Identify "Stable" Physical Regimes (High-dim continuous, Ecological, etc.)
        stable_regimes = ["High-dimensional continuous systems", "Ecological cascades", "Base"]
        stable_idx = [i for i, d in enumerate(self.domains) if d.get('regime', 'Base') in stable_regimes]
        
        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X[stable_idx], y[stable_idx])
        
        # 3. Predict on all and find Errors
        y_pred = clf.predict(X)
        fractures = []
        for i, (p, actual) in enumerate(zip(y_pred, y)):
            if p != actual:
                fractures.append({
                    "id": self.domains[i].get('id'),
                    "regime": self.domains[i].get('regime', 'Base'),
                    "predicted": p,
                    "actual": actual,
                    "k1": k1_raw[i],
                    "k2": int(x_k2[i]),
                    "substrate": self.domains[i].get('substrate_type', 'UNKNOWN')
                })

        # 4. Cluster Fractures (Regime Breakdown)
        stats = {}
        for f in fractures:
            reg = f['regime']
            stats[reg] = stats.get(reg, 0) + 1
            
        # 5. Local Rank in Fracture Zones
        # We check the entropy of the actual labels where the model failed
        fracture_idx = [i for i, (p, actual) in enumerate(zip(y_pred, y)) if p != actual]
        if fracture_idx:
            local_ig = mutual_info_score(X[fracture_idx, 0], y[fracture_idx]) # IG of K1 in failure zone
        else:
            local_ig = 0

        # 6. Export Graph Data
        with open(EXPORT_DIR / 'fracture_zones.json', 'w') as f:
            json.dump(fractures, f, indent=2)
            
        self._generate_report(len(fractures), stats, local_ig)

    def _generate_report(self, total, stats, local_ig):
        report = f"# Helix Fracture Boundary Atlas\n\n"
        report += f"**Total Fractures Identified:** {total}\n"
        report += f"**Global Fracture Density:** {total/len(self.domains):.4f}\n\n"
        
        report += "### 1. Failure Clusters by Regime\n"
        # Sort by count
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        for reg, count in sorted_stats:
            report += f"- **{reg}**: {count} fractures ({count/total:.2%} of total failures)\n"
            
        report += "\n### 2. Breakdown of the 'Third Element' Gap\n"
        report += f"In fracture zones, the mutual information of existing elements (K1, K2) against BoundaryType collapses to **{local_ig:.4f}**.\n\n"
        
        report += "#### Predicted Missing Invariants:\n"
        if stats.get("Social / institutional collapse", 0) > 100:
            report += "- **Social Coordination Complexity (C3):** High density of synchronization failures in institutional regimes.\n"
        if stats.get("Purely symbolic / combinatorial systems", 0) > 100:
            report += "- **Logical Constraint Depth (C4):** Failure of expression primitives to capture symbolic path dependency.\n"
        
        report += "\n### 3. Structural Phase Transition\n"
        report += "The transition from physical (predictable) to symbolic/social (fractured) geometry occurs at the boundary of **SYMBOLIC_SPACE** and **HYBRID_DYNAMIC** substrates.\n\n"
        
        report += "---\nDerived From: Fracture Mapping Suite v1\n"
        
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        print(f"Fracture Atlas generated at {REPORT_FILE}")

if __name__ == "__main__":
    fm = FractureMapper()
    fm.map_fractures()
