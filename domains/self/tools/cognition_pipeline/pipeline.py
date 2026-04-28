"""
Cognition Substrate Pipeline — domains/cognition/pipeline.py
=============================================================
Implements CognitionSubstratePipeline.

HSL entry point:
    SUBSTRATE run name:cognition
    SUBSTRATE run name:cognition fixture:branching schedule:linear seed:42
    SUBSTRATE run name:cognition fixture:attractor seed:42 steps:80
    SUBSTRATE run name:cognition fixture:branching schedule:none  # null control

Wraps the cognition e2e path (fixture → trajectory log → probe extraction
→ collapse detection → morphology assignment) and exposes it through HSL.

Pipeline stages (from e2e):
    1. Branching / linear constraint      — baseline DCP case
    2. Branching / no constraint          — null control
    3. Branching / perturbation           — recovery behavior
    4. Attractor / strong pull + perturb  — circular / transformative contrast

When fixture and schedule are specified, runs only the matching configuration
instead of all four.
"""
from __future__ import annotations

from typing import Any


class CognitionSubstratePipeline:
    """
    Runnable Helix cognition substrate pipeline.

    Parameters
    ----------
    fixture : str | None
        Which fixture to run: 'branching' or 'attractor'.
        If None, runs the full four-run e2e suite.
    schedule : str
        Constraint schedule for the branching fixture:
        'linear' | 'step' | 'exponential' | 'none'.
        Ignored if fixture='attractor'.
    seed : int
        Random seed. Default 42.
    steps : int | None
        Number of simulation steps. If None, uses fixture defaults.
    compile_to_atlas : bool
        Reserved — Atlas integration not yet wired in this domain.
    output_name : str | None
        Optional label for the output artifact.
    """

    def __init__(
        self,
        fixture: str | None = None,
        schedule: str = "linear",
        seed: int = 42,
        steps: int | None = None,
        compile_to_atlas: bool = False,
        output_name: str | None = None,
    ) -> None:
        self.fixture = fixture.lower() if fixture else None
        self.schedule = schedule.lower()
        self.seed = int(seed)
        self.steps = int(steps) if steps is not None else None
        self.compile_to_atlas = compile_to_atlas
        self.output_name = output_name

    def run(self) -> dict[str, Any]:
        """
        Execute the cognition substrate pipeline.

        If fixture is None, delegates to the full e2e suite (four runs).
        Otherwise runs the specified fixture/schedule combination only.

        Returns a dict containing:
        - schema_version
        - runs: list of per-run result dicts with:
            label, fixture_id, n_steps, initial/final/min breadth,
            max_tension, collapse_step, final_morphology,
            qualification_status, perturbation_step/response
        - pipeline_params
        - atlas_status (if compile_to_atlas is set)
        """
        if self.fixture is None:
            return self._run_full_suite()

        if self.fixture == "branching":
            return self._run_branching()
        if self.fixture == "attractor":
            return self._run_attractor()

        raise ValueError(
            f"Unknown fixture {self.fixture!r}. Use 'branching', 'attractor', or omit for full suite."
        )

    def _run_full_suite(self) -> dict[str, Any]:
        from model.domains.self.e2e import run_e2e
        result = run_e2e(verbose=False)
        result["pipeline_params"] = {
            "fixture": "all",
            "seed": self.seed,
        }
        if self.compile_to_atlas:
            result["atlas_status"] = "not_implemented"
        return result

    def _run_branching(self) -> dict[str, Any]:
        from model.domains.self.fixtures import branching
        from model.domains.self.fixtures.branching import BranchingConfig
        from model.domains.self.analysis.morphology_classifier import morphology_summary
        from core.invariants.dcp.morphology import CollapseMorphology, MORPHOLOGY_PROFILES

        cfg = BranchingConfig(
            constraint_schedule=self.schedule,
            seed=self.seed,
            **({"n_steps": self.steps} if self.steps is not None else {}),
        )
        log = branching.run(cfg)
        s = log.summary()
        s["label"] = f"branching_{self.schedule}"

        morphology = CollapseMorphology(log.final_morphology) if log.final_morphology else None
        if morphology and morphology in MORPHOLOGY_PROFILES:
            s["morphology_description"] = MORPHOLOGY_PROFILES[morphology].description
        else:
            s["morphology_description"] = None

        result: dict[str, Any] = {
            "schema_version": "cognition_pipeline_v1",
            "runs": [s],
            "pipeline_params": {
                "fixture": "branching",
                "schedule": self.schedule,
                "seed": self.seed,
                "steps": self.steps,
            },
        }
        if self.compile_to_atlas:
            result["atlas_status"] = "not_implemented"
        return result

    def _run_attractor(self) -> dict[str, Any]:
        from model.domains.self.fixtures import attractor
        from model.domains.self.fixtures.attractor import AttractorConfig
        from core.invariants.dcp.morphology import CollapseMorphology, MORPHOLOGY_PROFILES

        cfg = AttractorConfig(
            seed=self.seed,
            **({"n_steps": self.steps} if self.steps is not None else {}),
        )
        log = attractor.run(cfg)
        s = log.summary()
        s["label"] = "attractor"

        morphology = CollapseMorphology(log.final_morphology) if log.final_morphology else None
        if morphology and morphology in MORPHOLOGY_PROFILES:
            s["morphology_description"] = MORPHOLOGY_PROFILES[morphology].description
        else:
            s["morphology_description"] = None

        result: dict[str, Any] = {
            "schema_version": "cognition_pipeline_v1",
            "runs": [s],
            "pipeline_params": {
                "fixture": "attractor",
                "seed": self.seed,
                "steps": self.steps,
            },
        }
        if self.compile_to_atlas:
            result["atlas_status"] = "not_implemented"
        return result

