import json
import hashlib
from datetime import datetime

TRACE_LOG = []

def log_trace(claim, script, function, lines, excerpt_hash):
    TRACE_LOG.append({
        "claim": claim,
        "source": f"{script}:{function}",
        "lines": lines,
        "excerpt_hash": excerpt_hash
    })

def write_artifacts(artifact_dir, seed, np_ver, pd_ver, x_raw, verdict, mean_pss, base_top_dominance, results, script_name, obstructions):
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "seed": seed,
        "environment": {
            "numpy": np_ver,
            "pandas": pd_ver,
            "python": "3.10+"
        },
        "dataset": "synthetic_rank5_noisy",
        "dataset_hash": hashlib.sha256(x_raw.tobytes()).hexdigest()
    }
    with open(artifact_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)
        
    final_output = {
        "verdict": verdict,
        "mean_pss": mean_pss,
        "base_top_dominance": base_top_dominance,
        "transform_results": results
    }
    with open(artifact_dir / "results.json", "w") as f:
        json.dump(final_output, f, indent=4)
        
    report = f"# PSC Embedding Discovery Report\n\n## Objective\nAssess whether semantic axes in a synthetic (but structured) embedding space are stable structural dimensions or projection artifacts.\n\n## Results\n- **Verdict**: {verdict}\n- **Baseline Dominance (Top PCA Component)**: {base_top_dominance:.4f}\n- **Mean PSS (Family)**: {mean_pss:.4f}\n\n### Transformation Breakdown\n| Transform | RetentionOverlap | DominanceDrift | PSS |\n|-----------|------------------|----------------|-----|\n"
    for t_name, res in results.items():
        report += f"| {t_name} | {res['retention_overlap']:.4f} | {res['dominance_drift']:.4f} | {res['pss']:.4f} |\n"
    
    report += f"\n## Falsifiers\nIf the mean PSS falls below 0.60 under isotopic rotation and scaling, the dominance claim for this space is REJECTED as a PROJECTION_ARTIFACT.\n"
    with open(artifact_dir / "report.md", "w") as f:
        f.write(report)
        
    log_trace("PSC Result Stability", script_name, "run_embedding_psc", "70-120", hashlib.sha256(report.encode()).hexdigest())
    with open(artifact_dir / "trace_index.json", "w") as f:
        json.dump(TRACE_LOG, f, indent=4)
        
    with open(artifact_dir / "obstruction_log.json", "w") as f:
        json.dump(obstructions, f, indent=4)
