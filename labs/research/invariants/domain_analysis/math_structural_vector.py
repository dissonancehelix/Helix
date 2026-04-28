"""
Math Structural Vector — core/probes/math/domain_analysis/math_structural_vector.py
===============================================================================
Defines the domain-local 6-axis structural metric vector for the math substrate.

This is NOT the same as the shared HelixEmbedding.
MathStructuralVector describes properties of simulation outputs in math-domain
terms. It must be projected into HelixEmbedding before it can be stored in the
Atlas or compared cross-domain.

See: core/probes/math/embedding/projection.py for the projection adapter.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.stats import entropy as scipy_entropy


@dataclass
class MathStructuralVector:
    """
    Domain-local structural metrics for a math-domain simulation output.

    All values are floats in [0.0, 1.0] after normalization, except where
    the normalization method is explicitly documented per axis.
    """
    attractor_stability: float    # A_s: inverse variance of periodic orbit
    generative_constraint: float  # G_c: restricted / total state space ratio
    recurrence_depth: float       # R_d: fractal dimension normalized
    structural_density: float     # S_d: event density, sigmoid normalized
    control_entropy: float        # C_e: normalized Shannon entropy
    basin_permeability: float     # B_p: exp(-lyapunov)

    def to_dict(self) -> dict[str, float]:
        return {
            "attractor_stability": self.attractor_stability,
            "generative_constraint": self.generative_constraint,
            "recurrence_depth": self.recurrence_depth,
            "structural_density": self.structural_density,
            "control_entropy": self.control_entropy,
            "basin_permeability": self.basin_permeability,
        }

    def as_array(self) -> np.ndarray:
        return np.array([
            self.attractor_stability,
            self.generative_constraint,
            self.recurrence_depth,
            self.structural_density,
            self.control_entropy,
            self.basin_permeability,
        ], dtype=float)

    @classmethod
    def from_kuramoto_results(cls, results: dict[str, Any]) -> "MathStructuralVector":
        """
        Compute a MathStructuralVector from a KuramotoSystem.get_results_summary()
        output dict.

        This is the canonical extraction path for Kuramoto simulation outputs.
        """
        sync_index = float(results.get("sync_index", 0.0))
        final_phases = np.array(results.get("final_phases", [0.0]))
        K = float(results.get("K", 0.0))

        # A_s: Attractor Stability — sync index is a direct proxy for attractor strength
        a_s = float(np.clip(sync_index, 0.0, 1.0))

        # G_c: Generative Constraint — derived from coupling strength K
        # K=0 → unconstrained, K→∞ → fully constrained; use sigmoid to normalize
        g_c = float(1.0 / (1.0 + math.exp(-K + 1.0)))

        # R_d: Recurrence Depth — use phase variance as a proxy (low variance = high R_d)
        phase_var = float(np.var(final_phases))
        # Normalize: max expected variance for uniform dist on [0, 2π] is π²/3 ≈ 3.29
        r_d = float(np.clip(1.0 - (phase_var / 3.29), 0.0, 1.0))

        # S_d: Structural Density — events per unit time; use n_oscillators as event count
        n = float(results.get("n_oscillators", 1))
        lam = 0.05
        s_d = float(1.0 / (1.0 + math.exp(-lam * n + 2.0)))

        # C_e: Control Entropy — Shannon entropy of phase distribution
        hist, _ = np.histogram(final_phases, bins=20, range=(0, 2 * math.pi), density=True)
        raw_entropy = float(scipy_entropy(hist + 1e-9))
        max_entropy = math.log(20)  # max entropy for 20-bin uniform dist
        c_e = float(np.clip(raw_entropy / max_entropy, 0.0, 1.0))

        # B_p: Basin Permeability — inverse of sync_index (high sync = low permeability)
        b_p = float(np.clip(1.0 - sync_index, 0.0, 1.0))

        return cls(
            attractor_stability=a_s,
            generative_constraint=g_c,
            recurrence_depth=r_d,
            structural_density=s_d,
            control_entropy=c_e,
            basin_permeability=b_p,
        )
