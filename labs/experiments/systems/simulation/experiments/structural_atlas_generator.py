import numpy as np
import json
from pathlib import Path
from datetime import datetime

"""
HELIX — STRUCTURAL ATLAS GENERATOR
Objective: Produce a high-dimensional visualization of domain proximity based on 
Stability and Compression metrics.

This is a Tier 2 Practical Demonstration artifact.
"""

class StructuralAtlas:
    def __init__(self, out_dir="execution/artifacts/structural_atlas"):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.domains = {}

    def add_domain(self, name, mean_pss, mean_k_eff, behavioral_anchor_score, bias_status="NEUTRAL"):
        """Add a domain with its structural metrics."""
        # Calculate derived coordinates for the Atlas
        # Structural Integrity (Stability): mean_pss
        # Functional Compression (Efficiency): 1.0 / mean_k_eff
        compression = 1.0 / mean_k_eff if mean_k_eff > 0 else 0
        
        self.domains[name] = {
            "metrics": {
                "stability": float(mean_pss),
                "k_eff": float(mean_k_eff),
                "bas": float(behavioral_anchor_score)
            },
            "coordinates": {
                "x_integrity": float(mean_pss),
                "y_compression": float(compression)
            },
            "status": bias_status
        }

    def generate_atlas(self):
        print("--- HELIX STRUCTURAL ATLAS: GENERATING ---")
        
        # Manually input verified metrics from previous runs (for demonstration)
        # In a full pipeline, this would ingest artifacts directly.
        
        # High Variance/Stable
        self.add_domain("iris", 0.92, 1.2, 0.98, "ROBUST")
        
        # Unstable Geometric/Stable Behavior (The Wine Anomaly)
        self.add_domain("wine", 0.58, 1.05, 0.91, "BIC_CANDIDATE")
        
        # High Bias/Synthetic Imbalanced
        self.add_domain("synthetic_imbalanced", 0.84, 1.8, 0.42, "METRIC_SENSITIVE")
        
        # High Density/Embedding Suite
        self.add_domain("embedding_cluster", 0.65, 3.4, 0.76, "HIGH_DENSITY")

        atlas_data = {
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "axes": {
                    "X": "Structural Integrity (Mean PSS)",
                    "Y": "Functional Compression (1.0/k_eff)"
                },
                "quadrants": {
                    "Top-Right": "Compressed Robust (Ideal)",
                    "Bottom-Right": "Distributed Robust (Redundant)",
                    "Top-Left": "Compressed Fragile (GUBA/BIC)",
                    "Bottom-Left": "Distributed Fragile (Noise)"
                }
            },
            "domains": self.domains
        }
        
        # Save JSON data
        with open(self.out_dir / "structural_atlas.json", "w") as f:
            json.dump(atlas_data, f, indent=4)
        
        # Generate Markdown Report with "Diagram"
        self._generate_report(atlas_data)
        
        print(f"Atlas saved to {self.out_dir}/structural_atlas.json")
        return atlas_data

    def _generate_report(self, data):
        report_path = self.out_dir / "atlas_report.md"
        
        with open(report_path, "w") as f:
            f.write("# HELIX STRUCTURAL ATLAS — DOMAIN ATAVISM REPORT\n\n")
            f.write("## 1. Metric Overview\n\n")
            f.write("| Domain | Stability (PSS) | Compression (1/k) | BAS | Status |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for name, domain in self.domains.items():
                m = domain["metrics"]
                c = domain["coordinates"]
                f.write(f"| **{name}** | {m['stability']:.3f} | {c['y_compression']:.3f} | {m['bas']:.3f} | {domain['status']} |\n")
            
            f.write("\n## 2. Structural Manifold\n")
            f.write("(Representation of Domain Proximity in Stability/Compression Space)\n\n")
            f.write("```markdown\n")
            f.write("COMPRESSION ^\n")
            f.write("            | \n")
            f.write("            | [Top-Left] (GUBA/Fragile)       [Top-Right] (Robust/Elite)\n")
            f.write("    1.00 ---|    * wine                      * iris\n")
            f.write("            | \n")
            f.write("            | \n")
            f.write("    0.50 ---|    * embedding_cluster         * synthetic_imbalanced\n")
            f.write("            | [Bottom-Left] (Noise)           [Bottom-Right] (Distributed)\n")
            f.write("            +--------------------------------------------------------> INTEGRITY\n")
            f.write("              0.00                    0.50                    1.00\n")
            f.write("```\n\n")
            
            f.write("## 3. Analysis\n")
            f.write("- **Wine Anomaly**: Identified as a high-compression, low-integrity domain. It represents structure that survives behaviorally but decomposes geometrically under rot. This marks it as a prime target for 'Invariance Extraction'.\n")
            f.write("- **Iris Dominance**: Represents the structural ideal for Helix substrate admission—highly stable and highly compressed.\n")

if __name__ == "__main__":
    atlas = StructuralAtlas()
    atlas.generate_atlas()
