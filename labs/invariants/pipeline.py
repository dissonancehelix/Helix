"""
Math Substrate Pipeline — core/probes/math/pipeline.py
===================================================
Implements MathSubstratePipeline.

HSL entry point:
    SUBSTRATE run name:math
    SUBSTRATE run name:math K:2.5 n:100 steps:800 seed:42
    SUBSTRATE run name:math K:2.5 n:100 steps:800 seed:42 compile:true

Wraps the math e2e path (Kuramoto → MathStructuralVector → HelixEmbedding
→ invariant candidate → governance validation) and appends the math-domain
DCP extraction layer.

Pipeline stages:
    1. Kuramoto simulation (via e2e)
    2. MathStructuralVector extraction (via e2e)
    3. HelixEmbedding projection (via e2e)
    4. Invariant candidate construction (via e2e)
    5. Governance validation (via e2e)
    6. DCP event extraction (math-specific proxy mapping)
    7. Optional: compile to Atlas (deferred until enforce_persistence is wired)
"""
from __future__ import annotations

from typing import Any

import numpy as np


class MathSubstratePipeline:
    """
    Runnable Helix math substrate pipeline.

    Parameters
    ----------
    K : float
        Kuramoto coupling strength. K > K_c produces synchronization.
        Default 2.0 (above typical K_c for N=50, Gaussian freqs, σ=1).
    n : int
        Number of oscillators. Default 50.
    steps : int
        Simulation steps. Default 500.
    seed : int
        Random seed for reproducibility. Default 42.
    compile_to_atlas : bool
        If True and persistence_eligible, mark for Atlas commit.
        Actual commit requires enforce_persistence() — not yet wired.
    output_name : str | None
        Optional label for the output artifact.
    """

    def __init__(
        self,
        K: float = 2.0,
        n: int = 50,
        steps: int = 500,
        seed: int = 42,
        compile_to_atlas: bool = False,
        output_name: str | None = None,
    ) -> None:
        self.K = float(K)
        self.n = int(n)
        self.steps = int(steps)
        self.seed = int(seed)
        self.compile_to_atlas = compile_to_atlas
        self.output_name = output_name

    def run(self) -> dict[str, Any]:
        """
        Execute the full math substrate pipeline.

        Returns a dict containing:
        - simulation_results        (from Kuramoto)
        - math_structural_vector    (domain-local metrics)
        - helix_embedding           (shared cross-domain format)
        - invariant_candidate       (with status and falsifiers)
        - governance_validation     (AtomicityRule, FalsifiabilityRule)
        - persistence_eligible      (bool)
        - dcp_event                 (DCPEvent.to_dict() — math DCP proxy mapping)
        - dcp_qualification         (FULL / UNCONFIRMED / INCOMPLETE / INSUFFICIENT)
        - pipeline_params           (K, n, steps, seed)
        - atlas_status              (if compile_to_atlas is set)
        """
        from helix.research.invariants.math.math.e2e import run_e2e
        from helix.research.invariants.math.math.analysis.dcp import extract_dcp_event

        # Stages 1–5: simulation → vector → embedding → candidate → governance
        e2e_result = run_e2e(
            K=self.K,
            n=self.n,
            steps=self.steps,
            seed=self.seed,
            verbose=False,
        )

        # Stage 6: DCP event extraction.
        # Reconstruct natural_freqs with same seed to match what e2e used.
        # e2e calls rng.normal first (freqs), then rng.uniform (phases) — only need first draw.
        rng = np.random.default_rng(self.seed)
        natural_freqs = rng.normal(0.0, 1.0, self.n)

        dcp_event = extract_dcp_event(
            sim_results=e2e_result["simulation_results"],
            K=self.K,
            natural_freqs=natural_freqs,
            source_artifact=(
                self.output_name
                or f"math_substrate_K{self.K:.2f}_n{self.n}_s{self.seed}"
            ),
            seed=self.seed,
        )

        result: dict[str, Any] = {
            **e2e_result,
            "dcp_event": dcp_event.to_dict(),
            "dcp_qualification": dcp_event.qualification_status(),
            "pipeline_params": {
                "K": self.K,
                "n": self.n,
                "steps": self.steps,
                "seed": self.seed,
            },
        }

        # Stage 7: Atlas persistence (deferred)
        if self.compile_to_atlas:
            if e2e_result.get("persistence_eligible"):
                # TODO: wire to enforce_persistence() once compiler gate is ready
                result["atlas_status"] = "eligible_not_committed"
            else:
                result["atlas_status"] = "blocked_governance_or_confidence"

        return result
