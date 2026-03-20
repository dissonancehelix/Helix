import json
import math
from pathlib import Path
from typing import Any
from domains.music.ingestion.config import ARTIFACTS, COMPOSER_PROFILES_PATH

def generate_composer_reports(profiler_data: dict[str, Any]):
    """
    Generate the stylistic summary reports for each composer.
    """
    report_desc = "# HELIX MUSIC LAB — COMPOSER STYLE REPORT\n\n"
    report_desc += "This report summarizes the stylistic fingerprints of the target composers based on the expanded training dataset.\n\n"
    
    for composer, profile in profiler_data.items():
        centroid = profile.get("centroid", [])
        variance = profile.get("var", [])
        n_tracks = profile.get("n", 0)
        
        report_desc += f"## {composer}\n"
        report_desc += f"- **Training Tracks:** {n_tracks}\n"
        
        # Interpret some key dimensions (v1 schema)
        # dims 0-11: Pitch Class Histogram
        pc_hist = centroid[0:12]
        top_pc = pc_hist.index(max(pc_hist)) if pc_hist else 0
        pc_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        report_desc += f"- **Dominant Pitch Class:** {pc_names[top_pc]}\n"
        
        # dims 30-37: FM Algorithm Distribution
        alg_dist = centroid[30:38]
        top_alg = alg_dist.index(max(alg_dist)) if alg_dist else 0
        report_desc += f"- **Preferred FM Algorithm:** {top_alg}\n"
        
        # dims 85: Tempo
        avg_tempo = centroid[85] * 200 + 40 # Rough denormalization
        report_desc += f"- **Average Tempo:** {int(avg_tempo)} BPM\n"
        
        # dims 49: DAC Density
        dac_density = centroid[49]
        report_desc += f"- **DAC Usage Intensity:** {'High' if dac_density > 0.5 else 'Moderate' if dac_density > 0.2 else 'Low'}\n"
        
        report_desc += "\n"

    report_path = ARTIFACTS / "music_lab" / "sonic3_composer_style_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_desc)
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    if Path(COMPOSER_PROFILES_PATH).exists():
        with open(COMPOSER_PROFILES_PATH) as f:
            data = json.load(f)
            generate_composer_reports(data)
