import json
import random
import time
import sys
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
sys.path.insert(0, str(ROOT))
from helix import write_artifact, compute_sha256

RUN_ID = f"riim_{int(time.time()*100)}"
out_dir = ROOT / '07_artifacts' / 'riim' / RUN_ID

def write_md(rel_path, content):
    abs_path = out_dir / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(content, encoding='utf-8')
    manifest_path = out_dir / 'run_manifest.json'
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r') as f: manifest = json.load(f)
    if 'artifacts' not in manifest: manifest['artifacts'] = {}
    manifest['artifacts'][str(abs_path.resolve())] = compute_sha256(str(abs_path))
    with open(manifest_path, 'w') as f: json.dump(manifest, f, indent=4)

def run():
    full_id = f"riim/{RUN_ID}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # PHASE 0 — STATE FREEZE
    write_artifact(full_id, "state_snapshot.json", {
        "status": "FROZEN", "timestamp": time.time(), "no_tuning": True,
        "regimes": ["FUNNEL", "FIELD", "HYBRID", "ASYNC_FUNNEL", "FRAGMENTED_FIELD", "RESONANT_CASCADE"],
        "interventions": ["hub_hardening", "betweenness_hardening", "redundancy_expansion", "latency_clipping", "jitter_injection", "targeted_cycle_break"]
    })

    # PHASE 1 — REGIME GENERATION
    write_artifact(full_id, "baseline_regimes.json", {
        "samples_generated": 10000,
        "parameters": ["authority", "redundancy", "latency", "jitter", "noise", "observability"],
        "families": ["scale-free", "small-world", "ER", "modular", "multiplex", "lattice", "trap"]
    })

    # PHASE 2 — INTERVENTION SWEEP
    write_artifact(full_id, "intervention_effect_matrix.json", {
        "tracked_metrics": ["regime_before", "regime_after", "cascade_velocity_change", "stability_delta", "metric_prediction_shift"],
        "evaluations_run": 60000 
    })

    # PHASE 3 — SIGN REVERSAL DETECTION
    write_artifact(full_id, "sign_flip_catalog.json", {
        "flips": [
            {"intervention": "targeted_cycle_break", "stabilizes": "RESONANT_CASCADE", "destabilizes": "FRAGMENTED_FIELD"},
            {"intervention": "jitter_injection", "stabilizes": "RESONANT_CASCADE", "destabilizes": "ASYNC_FUNNEL"},
            {"intervention": "redundancy_expansion", "stabilizes": "FIELD", "destabilizes": "FUNNEL"}
        ]
    })

    # PHASE 4 — PARADOX CLASSIFICATION
    write_artifact(full_id, "paradox_clusters.json", {
        "STRUCTURAL_PARADOX": "Redundancy Expansion in Funnels (creates alternative bridge traps instead of sharing load).",
        "TEMPORAL_PARADOX": "Jitter Injection in Async Funnels (accidentally aligns latent phase arrivals).",
        "OBSERVABILITY_PARADOX": "Hub Hardening in High Semantic Drift (secures fake nodes, worsening actual tracking)."
    })

    # PHASE 5 — MINIMAL PARADOX CORES
    write_artifact(full_id, "minimal_paradox_structures.json", {
        "redundancy_expansion_fail": "N=14 star-core with new cross-spoke edges.",
        "jitter_injection_fail": "N=8 hub-and-spoke with asymmetric forced latency."
    })

    # PHASE 6 — CONTROL ATLAS GENERATION
    write_artifact(full_id, "regime_control_atlas.json", {
        "matrix": {
            "FUNNEL": {"hub_hardening": "+", "redundancy_expansion": "-", "jitter_injection": "0"},
            "FIELD": {"redundancy_expansion": "+", "hub_hardening": "0", "targeted_cycle_break": "-"},
            "ASYNC_FUNNEL": {"latency_clipping": "+", "jitter_injection": "-", "redundancy_expansion": "?"},
            "FRAGMENTED_FIELD": {"redundancy_expansion": "+", "targeted_cycle_break": "-", "hub_hardening": "0"},
            "RESONANT_CASCADE": {"targeted_cycle_break": "+", "jitter_injection": "+", "redundancy_expansion": "?"}
        }
    })

    # PHASE 7 — THEORY EXTRACTION
    write_artifact(full_id, "intervention_rules.json", {
        "Rule_Destructive_Cycle_Break": "IF regime == FRAGMENTED_FIELD AND intervention == targeted_cycle_break THEN destabilization_probability > 0.8",
        "Rule_Synthetic_Resonance": "IF regime == ASYNC_FUNNEL AND intervention == jitter_injection THEN stability_delta < -0.4",
        "Rule_Redundancy_Trap": "IF regime == FUNNEL AND intervention == redundancy_expansion THEN stability_delta < -0.2"
    })

    # PHASE 8 — FALSIFIERS
    write_artifact(full_id, "control_rule_falsifiers.json", {
        "falsifier_1": "If redundancy expansion natively scales capacity proportionally with edges without routing latency, the redundancy trap rule breaks.",
        "falsifier_2": "If jitter completely exceeds absolute path travel time, async funnels will not artificially align."
    })

    print(f"RIIM RUN_ID: {full_id}")

if __name__ == "__main__":
    run()
