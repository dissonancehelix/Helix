"""
Decision Compression Probe — 04_labs/probes/decision_compression_probe.py

Invariant: Decision Compression
In multi-agent systems, effective decision-making power concentrates on a
small subset of agents — the system behaves as if controlled by far fewer
agents than are nominally present.

Measurement: Effective participant count
    k_eff = 1 / Σ(w_i²)   where w_i are normalised influence weights
    signal_strength = 1 - k_eff / N

Detection threshold: signal_strength > 0.3

Dataset format:
    {
        "domain": "games" | "language" | "music" | ...,
        "agents": [{"id": str, "role": str, "influence_weight": float}, ...],
        "decision_rounds": [{"round": int, "weights": [float], "outcome": str}, ...]
    }
"""

from __future__ import annotations
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

VERSION = "1.0.0"

SIGNAL_THRESHOLD = 0.3


def _compute_k_eff(weights: list[float]) -> float:
    """Effective number of agents: 1/Σ(w_i²) on normalised weights."""
    total = sum(weights)
    if total <= 0:
        return float(len(weights))
    normalised = [w / total for w in weights]
    sum_sq = sum(w * w for w in normalised)
    return 1.0 / sum_sq if sum_sq > 0 else float(len(weights))


def run_decision_compression_probe(dataset: dict) -> dict[str, Any]:
    """
    Compute decision compression signal from a dataset.
    Returns a probe_result dict.
    """
    domain = dataset.get("domain", "unknown")
    agents = dataset.get("agents", [])
    decision_rounds = dataset.get("decision_rounds", [])

    n_agents = len(agents)
    if n_agents == 0:
        return {
            "probe_name": "decision_compression",
            "domain": domain,
            "passed": False,
            "signal": 0.0,
            "signal_strength": 0.0,
            "confidence": "insufficient_data",
            "error": "no agents in dataset",
        }

    # Gather all weight vectors (from agents + each round)
    all_weight_vectors: list[list[float]] = []

    agent_weights = [float(a.get("influence_weight", 1.0 / n_agents)) for a in agents]
    all_weight_vectors.append(agent_weights)

    for rnd in decision_rounds:
        rnd_weights = rnd.get("weights", [])
        if rnd_weights:
            all_weight_vectors.append([float(w) for w in rnd_weights])

    # Compute k_eff for each vector and average
    k_eff_values = [_compute_k_eff(wv) for wv in all_weight_vectors]
    mean_k_eff = sum(k_eff_values) / len(k_eff_values)

    signal_strength = 1.0 - (mean_k_eff / n_agents)
    signal_strength = max(0.0, min(1.0, signal_strength))

    passed = signal_strength > SIGNAL_THRESHOLD

    # Confidence label
    if signal_strength > 0.7:
        confidence = "strong"
    elif signal_strength > 0.4:
        confidence = "moderate"
    elif signal_strength > 0.2:
        confidence = "weak"
    else:
        confidence = "absent"

    return {
        "probe_name": "decision_compression",
        "domain": domain,
        "passed": passed,
        "signal": round(signal_strength, 4),
        "signal_strength": round(signal_strength, 4),
        "confidence": confidence,
        "decision_dimension": round(mean_k_eff, 4),
        "n_agents": n_agents,
        "n_rounds": len(decision_rounds),
        "k_eff_per_round": [round(k, 4) for k in k_eff_values],
        "compression_ratio": round(1.0 - mean_k_eff / n_agents, 4),
        "version": VERSION,
    }


if __name__ == "__main__":
    input_path = os.environ.get("HELIX_SYSTEM_INPUT")
    artifact_dir = os.environ.get("HELIX_ARTIFACT_DIR")

    if not input_path or not artifact_dir:
        print(
            "[PROBE] ERROR: HELIX_SYSTEM_INPUT and HELIX_ARTIFACT_DIR must be set.",
            file=sys.stderr,
        )
        sys.exit(2)

    with open(input_path, "r", encoding="utf-8") as f:
        system_input = json.load(f)

    dataset = system_input.get("dataset", system_input)
    result = run_decision_compression_probe(dataset)

    out_path = Path(artifact_dir) / "probe_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    sys.exit(0 if result.get("passed", False) else 1)
