import json
import hashlib
from datetime import datetime

def write_impact_artifacts(artifact_dir, summary_results, perf_matrix, drift_metrics):
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    with open(artifact_dir / "results.json", "w") as f:
        json.dump(summary_results, f, indent=4)
        
    with open(artifact_dir / "performance_matrix.json", "w") as f:
        json.dump(perf_matrix, f, indent=4)
        
    with open(artifact_dir / "drift_metrics.json", "w") as f:
        json.dump(drift_metrics, f, indent=4)
        
    report = "# PSC Behavioral Impact Report\n\n## Objective\nDetermine whether projection-unstable components materially affect classification performance or induce fragility under drift.\n\n## Hypotheses\n- **H1**: Unstable components cause high drift under transforms.\n- **H2**: Stable components retain core predictive power.\n\n## Cross-Dataset Summary\n"
    
    for ds_name, res in summary_results.items():
        report += f"### Dataset: {ds_name}\n"
        report += f"- **Stable/Unstable Split**: {res['stable_count']} / {res['unstable_count']}\n"
        report += f"- **Full Stability Ratio**: {drift_metrics[ds_name]['full_stability_ratio']:.4f}\n"
        report += f"- **Stable Model Delta (Perf Loss)**: {drift_metrics[ds_name]['full_stable_delta']:.4f}\n"
        report += f"- **Verdict**: {res['verdict']}\n\n"
        
    with open(artifact_dir / "report.md", "w") as f:
        f.write(report)
        
    trace = [
        {"claim": "Behavioral Impact Accuracy Matrix", "source": "psc_behavioral_impact_suite.py:run_behavioral_impact_suite", "lines": "100-150", "excerpt_hash": hashlib.sha256(report.encode()).hexdigest()}
    ]
    with open(artifact_dir / "trace_index.json", "w") as f:
        json.dump(trace, f, indent=4)
        
    falsifiers = "# Falsifier: Behavioral Impact Stability\n\n## Falsifier: Stable Redundancy\nIf `Model_Stable` accuracy falls below **70%** of `Model_Full` accuracy, the \"Stable-Only\" hypothesis (H2) is falsified for that domain.\n\n## Falsifier: Unstable Relevance\nIf `Model_Unstable` stability ratio is > **0.90**, then \"unstable\" components according to PSC are behaviorally robust, falsifying the PSC rejection logic (H1).\n"
    with open(artifact_dir / "falsifiers.md", "w") as f:
        f.write(falsifiers)
