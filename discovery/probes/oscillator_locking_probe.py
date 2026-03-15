"""
Oscillator Locking Probe — 04_labs/probes/oscillator_locking_probe.py

Invariant: Oscillator Locking
    Coupled oscillators with sufficient coupling strength K spontaneously
    synchronise their phases, collapsing the effective state space.

Model: Kuramoto
    dθ_i/dt = ω_i + (K/N) * Σ_j sin(θ_j - θ_i)

Measurement:
    Order parameter R = |(1/N) * Σ exp(i*θ_j)| ∈ [0, 1]
    R ≈ 0  →  incoherent / unsynchronised
    R ≈ 1  →  fully phase-locked

Detection threshold: R > 0.6

Dataset format:
{
  "domain": "<str>",
  "oscillators": [
    {"id": "...", "initial_phase": <radians>, "natural_frequency": <float>}
  ],
  "coupling_strength": <float>,
  "n_steps": <int>,
  "dt": <float>
}
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

VERSION = "1.0.0"

LOCK_THRESHOLD = 0.6          # minimum R to declare phase locking
SIGNAL_THRESHOLD = 0.3        # minimum signal_strength to report detection
TAIL_FRACTION = 0.2           # fraction of steps used for tail statistics


# ---------------------------------------------------------------------------
# Kuramoto simulation
# ---------------------------------------------------------------------------

def _simulate_kuramoto(
    phases: list[float],
    freqs: list[float],
    K: float,
    n_steps: int,
    dt: float,
) -> list[list[float]]:
    """
    Simulate Kuramoto model.  Returns list of phase vectors, one per step.
    """
    N = len(phases)
    history: list[list[float]] = [phases[:]]
    current = phases[:]

    for _ in range(n_steps):
        new = []
        for i in range(N):
            coupling = sum(math.sin(current[j] - current[i]) for j in range(N))
            dtheta = freqs[i] + (K / N) * coupling
            new.append(current[i] + dtheta * dt)
        current = new
        history.append(current[:])

    return history


def _order_parameter(phases: list[float]) -> float:
    """R = |(1/N) * Σ exp(i*θ_j)|"""
    N = len(phases)
    if N == 0:
        return 0.0
    real = sum(math.cos(p) for p in phases) / N
    imag = sum(math.sin(p) for p in phases) / N
    return math.sqrt(real * real + imag * imag)


# ---------------------------------------------------------------------------
# Probe logic
# ---------------------------------------------------------------------------

def run_oscillator_locking_probe(dataset: dict) -> dict:
    """
    Run the oscillator locking probe on a dataset dict.

    Returns a result dict containing canonical probe fields plus
    oscillator-specific diagnostics.
    """
    domain = dataset.get("domain", "unknown")
    oscillators = dataset.get("oscillators", [])
    K = float(dataset.get("coupling_strength", 1.0))
    n_steps = int(dataset.get("n_steps", 500))
    dt = float(dataset.get("dt", 0.01))

    n_agents = len(oscillators)
    if n_agents == 0:
        return {
            "probe_name": "oscillator_locking",
            "domain": domain,
            "passed": False,
            "signal": 0.0,
            "signal_strength": 0.0,
            "confidence": "none",
            "order_parameter_R": 0.0,
            "order_parameter_R_initial": 0.0,
            "phase_lock_detected": False,
            "n_agents": 0,
            "n_steps": n_steps,
            "coupling_strength": K,
            "r_mean_tail": 0.0,
            "r_variance_tail": 0.0,
            "interpretation": "no oscillators provided",
            "version": VERSION,
        }

    phases = [float(o.get("initial_phase", 0.0)) for o in oscillators]
    freqs  = [float(o.get("natural_frequency", 1.0)) for o in oscillators]

    # Initial order parameter
    R_initial = _order_parameter(phases)

    # Simulate
    history = _simulate_kuramoto(phases, freqs, K, n_steps, dt)

    # Compute R at each step
    R_series = [_order_parameter(h) for h in history]

    # Final R
    R_final = R_series[-1]

    # Tail statistics (last TAIL_FRACTION of steps)
    tail_start = max(0, int(len(R_series) * (1 - TAIL_FRACTION)))
    tail = R_series[tail_start:]
    r_mean_tail = sum(tail) / len(tail) if tail else R_final
    r_var_tail = (
        sum((r - r_mean_tail) ** 2 for r in tail) / len(tail) if len(tail) > 1 else 0.0
    )

    phase_lock_detected = r_mean_tail > LOCK_THRESHOLD

    # signal_strength = how far R_mean_tail is from the threshold, normalised to [0,1]
    signal_strength = min(1.0, max(0.0, (r_mean_tail - 0.0) / 1.0))
    # signal is the raw R mean
    signal = r_mean_tail

    passed = phase_lock_detected and signal_strength > SIGNAL_THRESHOLD

    # Confidence estimate
    if r_mean_tail > 0.90:
        confidence = "high"
    elif r_mean_tail > 0.70:
        confidence = "medium"
    elif r_mean_tail > LOCK_THRESHOLD:
        confidence = "low"
    else:
        confidence = "none"

    if phase_lock_detected:
        interpretation = (
            f"Phase locking detected (R_tail={r_mean_tail:.4f} > {LOCK_THRESHOLD}). "
            f"Oscillators synchronised after {n_steps} steps with K={K}."
        )
    else:
        interpretation = (
            f"No phase locking (R_tail={r_mean_tail:.4f} ≤ {LOCK_THRESHOLD}). "
            f"Coupling K={K} insufficient for {n_agents} oscillators."
        )

    return {
        "probe_name": "oscillator_locking",
        "domain": domain,
        "passed": passed,
        "signal": round(signal, 6),
        "signal_strength": round(signal_strength, 6),
        "confidence": confidence,
        "order_parameter_R": round(R_final, 6),
        "order_parameter_R_initial": round(R_initial, 6),
        "phase_lock_detected": phase_lock_detected,
        "n_agents": n_agents,
        "n_steps": n_steps,
        "coupling_strength": K,
        "r_mean_tail": round(r_mean_tail, 6),
        "r_variance_tail": round(r_var_tail, 8),
        "interpretation": interpretation,
        "version": VERSION,
    }


# ---------------------------------------------------------------------------
# CLI entry point (called by sandbox_runner)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    system_input_path = os.environ.get("HELIX_SYSTEM_INPUT", "")
    artifact_dir = os.environ.get("HELIX_ARTIFACT_DIR", "")

    if not system_input_path or not artifact_dir:
        print("[oscillator_locking_probe] ERROR: env vars not set", file=sys.stderr)
        sys.exit(1)

    try:
        system_input = json.loads(Path(system_input_path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"[oscillator_locking_probe] ERROR reading system_input: {exc}", file=sys.stderr)
        sys.exit(1)

    dataset = system_input.get("dataset", system_input)

    result = run_oscillator_locking_probe(dataset)

    out_path = Path(artifact_dir) / "probe_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"[oscillator_locking] domain={result['domain']}  "
          f"R_tail={result['r_mean_tail']:.4f}  "
          f"passed={result['passed']}")

    sys.exit(0 if result["passed"] else 1)
