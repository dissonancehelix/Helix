"""
Math Domain DCP Hook — core/probes/math/analysis/dcp.py
=====================================================
First integration point between the math domain (Kuramoto model)
and the Decision Compression Principle.

This module translates Kuramoto simulation outputs into a DCPEvent
using math-specific proxy signals. It is the ONLY place where
Kuramoto results are interpreted in DCP terms.

Key relationship:
  Oscillator locking (Kuramoto K → K_c) is the canonical math
  expression of a DCP compression event:
    - Possibility space = phase angle dispersion before coupling
    - Constraint = coupling strength K / critical coupling K_c
    - Tension = order-parameter variance near K_c
    - Compression = sharp rise in R (order parameter) at locking
    - Post-collapse = locked synchrony; phase variance near zero

This does NOT prove DCP. It demonstrates:
  1. The mapping is plausible and inspectable
  2. The Kuramoto model produces measurable DCP-like signatures
  3. The signature can be compared across coupling strengths

Limitations:
  - K_c estimate is approximate (mean-field theory: K_c ≈ 2σ/π)
  - basin_permeability uses sync-based proxy, not actual Lyapunov
  - Tension proxy uses variance at a single coupling, not a time series
  - Cross-domain metric normalization not implemented here

Usage:
    from helix.research.invariants.math.math.analysis.dcp import extract_dcp_event
    event = extract_dcp_event(kuramoto_results, K=2.0, natural_freqs=freqs)
    print(event.qualification_status())
    print(event.to_json())
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() or (p / "README.md").exists()
)
sys.path.insert(0, str(ROOT))

from core.invariants.dcp.event import DCPEvent
from core.invariants.dcp.metrics import compute_dcp_score


def _estimate_Kc(natural_freqs: Sequence[float]) -> float:
    """
    Mean-field estimate of the critical coupling K_c for the Kuramoto model.

    K_c ≈ 2σ/π   where σ = std of natural frequencies.

    This is accurate for large N with Gaussian frequency distributions.
    """
    sigma = float(np.std(natural_freqs))
    return (2.0 * sigma) / math.pi


def extract_dcp_event(
    sim_results: dict,
    K: float,
    natural_freqs: Sequence[float],
    source_artifact: str = "math_kuramoto",
    seed: int | None = None,
) -> DCPEvent:
    """
    Extract a DCPEvent from Kuramoto simulation results.

    Maps Kuramoto outputs to the five DCP component proxies:

      possibility_space_proxy:
        Normalized phase angle variance BEFORE significant coupling.
        Estimated from: 1 - sync_index (uniform phases when uncoupled).
        We use 1 - sync_index to represent dispersion: higher sync_index
        = less dispersion = lower possibility space.
        Proxy: 1 - sim_results['sync_index'] if K is near zero,
               else we approximate from expected initial variance.

      constraint_proxy:
        K / K_c_estimate — how much of critical coupling is applied.
        Clipped to [0, 1].

      tension_proxy:
        Variance of the order parameter trajectory near K_c.
        Proxy: if K is near K_c, order parameter fluctuates (tension).
        Estimated from: how close K is to K_c (in [0,1]).
        Note: this is a structural proxy, not a time-series measurement.
        A time-series probe would be more accurate.

      collapse_proxy:
        Sharpness of collapse estimated from sync_index.
        High sync_index (> 0.8) after coupling indicates sharp locking.
        Proxy: sync_index * constraint_proximity

      post_collapse_narrowing:
        1 - (phase_variance_post_lock / estimated_initial_variance)
        Approximated from sync_index: high sync → low post variance.

    Args:
        sim_results:    dict from KuramotoSystem.get_results_summary()
        K:              coupling strength used in the simulation
        natural_freqs:  natural frequency array (for K_c estimation)
        source_artifact: artifact ID/path for provenance
        seed:           optional RNG seed for provenance

    Returns:
        DCPEvent with provenance and qualification status.
    """
    sync_index = float(sim_results.get("sync_index", 0.0))
    n_oscillators = int(sim_results.get("n_oscillators", 1))

    K_c_estimate = _estimate_Kc(natural_freqs)

    # --- Possibility space proxy ---
    # Uncoupled system: phases uniformly distributed → entropy max
    # After locking: phases clustered → entropy low
    # We approximate pre-coupling dispersion as 1 (maximum spread),
    # and represent the pre-event possibility space as high.
    # If K = 0, use actual sync_index as ground truth for dispersion.
    if K < 0.1:
        possibility_space = float(np.clip(1.0 - sync_index, 0.0, 1.0))
    else:
        # Estimate: uncoupled system would have sync_index ~ 0.1-0.2
        # so initial possibility space ≈ 0.8-0.9
        possibility_space = 0.85

    # --- Constraint proxy ---
    if K_c_estimate > 1e-6:
        constraint = float(np.clip(K / K_c_estimate, 0.0, 1.0))
    else:
        constraint = 0.0

    # --- Tension proxy ---
    # Near K_c, order parameter fluctuates → tension present.
    # Proxy: how close K is to K_c, but not past it.
    # K/K_c near 1.0 → high tension; K/K_c >> 1 → already locked.
    if K_c_estimate > 1e-6:
        k_ratio = K / K_c_estimate
        if k_ratio < 1.0:
            tension = float(np.clip(k_ratio, 0.0, 1.0))
        else:
            # Already past critical point — tension dissipated at locking
            tension = float(np.clip(2.0 - k_ratio, 0.0, 1.0))
    else:
        tension = 0.0

    # --- Collapse proxy ---
    # High sync after coupling → sharp locking event occurred.
    # Scale by constraint (weak constraint can't produce sharp collapse).
    if sync_index > 0.6:
        collapse = float(np.clip(sync_index * constraint, 0.0, 1.0))
    else:
        collapse = 0.0

    # --- Post-collapse narrowing ---
    # High sync = phases clustered = low trajectory diversity.
    post_narrowing = float(np.clip(sync_index, 0.0, 1.0))

    # --- Composite score ---
    dcp_score = compute_dcp_score(
        possibility_space=possibility_space,
        constraint=constraint,
        tension=tension,
        collapse=collapse,
        post_narrowing=post_narrowing,
    )

    # Confidence: conservative — these are all proxies, not direct measurements
    # A proper confidence would require null-baseline calibration.
    confidence = float(np.clip(dcp_score * 0.7, 0.0, 0.85))  # cap at 0.85 provisional

    event_id = f"math.dcp.kuramoto-K{K:.2f}-n{n_oscillators}"
    if seed is not None:
        event_id += f"-s{seed}"

    k_over_kc_str = f"{K/K_c_estimate:.3f}" if K_c_estimate > 1e-6 else "N/A"
    return DCPEvent(
        source_domain="math",
        source_artifact=source_artifact,
        event_id=event_id,
        possibility_space_proxy=possibility_space,
        constraint_proxy=constraint,
        tension_proxy=tension,
        collapse_proxy=collapse,
        post_collapse_narrowing=post_narrowing,
        confidence=confidence,
        calibration_status="provisional",
        notes=(
            f"Kuramoto K={K:.3f}, K_c_estimate={K_c_estimate:.3f}, "
            f"K/K_c={k_over_kc_str}, "
            f"sync_index={sync_index:.4f}, n={n_oscillators}. "
            "All proxies are structural estimates from simulation summary — "
            "not from a time series. Tension proxy is an approximation. "
            "Null-baseline calibration not performed."
        ),
        domain_metadata={
            "K": K,
            "K_c_estimate": K_c_estimate,
            "K_over_Kc": round(K / K_c_estimate, 4) if K_c_estimate > 1e-6 else None,
            "sync_index": sync_index,
            "n_oscillators": n_oscillators,
            "seed": seed,
            "dcp_composite_score": dcp_score,
        },
    )

