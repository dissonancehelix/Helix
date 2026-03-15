import os
import json
import statistics
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
RRS_DIR = ROOT / '07_artifacts' / 'rrs'
META_DIR = ROOT / '07_artifacts' / '_meta'
META_DIR.mkdir(parents=True, exist_ok=True)

def safe_load(p):
    if p.exists():
        with open(p, 'r') as f:
            return json.load(f)
    return {}

def spearman_rank_correlation(x, y):
    if len(x) != len(y) or len(x) == 0: return 0.0
    def rank(arr):
        s = sorted(list(enumerate(arr)), key=lambda v: v[1])
        r = [0]*len(arr)
        for i, (orig_i, v) in enumerate(s):
            r[orig_i] = i
        return r
    rx = rank(x)
    ry = rank(y)
    n = len(x)
    d_sq = sum((rx[i] - ry[i])**2 for i in range(n))
    return 1 - (6 * d_sq) / (n * (n**2 - 1)) if n > 1 else 0.0

def main():
    blindspots = []
    sensitivities = []
    spikes = []
    
    for repo_dir in RRS_DIR.iterdir():
        if not repo_dir.is_dir() or repo_dir.name == 'stress': continue
        for run_dir in repo_dir.iterdir():
            if not run_dir.is_dir(): continue
            
            b_exp = safe_load(run_dir / 'blindspot_expansion.json')
            risk_rep = safe_load(run_dir / 'risk_report.json')
            metrics = safe_load(run_dir / 'metrics.json')
            e_curve = safe_load(run_dir / 'elasticity_curve.json')
            
            if not metrics: continue
            
            # compute mean blindspot density for the run
            b_dens = statistics.mean([m.get("blindspot_density", 0) for m in metrics])
            # compute mean collapse sensitivity
            c_sens = statistics.mean([m.get("Collapse_Sensitivity", 0) for m in metrics])
            
            shape = e_curve.get("classified_shape", "") if e_curve else ""
            spike_val = 1.0 if shape == "Chaotic Spike" else 0.0
            
            blindspots.append(b_dens)
            sensitivities.append(c_sens)
            spikes.append(spike_val)
            
    corr_bs = spearman_rank_correlation(blindspots, sensitivities)
    corr_be = spearman_rank_correlation(blindspots, spikes)
    corr_se = spearman_rank_correlation(sensitivities, spikes)
    
    res = {
        "correlation_blindspot_density_vs_collapse_sensitivity": round(corr_bs, 4),
        "correlation_blindspot_density_vs_elasticity_shape": round(corr_be, 4),
        "correlation_collapse_sensitivity_vs_elasticity_shape": round(corr_se, 4),
        "blindspot_floor_overweighted": corr_bs < 0.1
    }
    
    with open(META_DIR / 'blindspot_correlation_audit.json', 'w') as f:
        json.dump(res, f, indent=4)
        
    print(f"Phase 4 Complete. Correlation BS vs Sens: {corr_bs}")

if __name__ == "__main__":
    main()
