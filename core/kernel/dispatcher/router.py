# Kernel Dispatcher Router — Phase 9
# Resolves engine from HIL envelope and delegates execution.
# Runs integrity gate before any experiment dispatch.

from __future__ import annotations

_INTEGRITY_CHECKED = False   # process-level gate: only check once per session


def _run_integrity_gate(verbose: bool = False) -> bool:
    """Run the Phase 9 integrity gate. Returns True if safe to proceed."""
    global _INTEGRITY_CHECKED
    if _INTEGRITY_CHECKED:
        return True
    try:
        from core.integrity.integrity_tests import gate
        ok = gate(verbose=verbose)
    except ImportError:
        # Integrity module not yet available — allow dispatch but warn
        print("[dispatcher] WARNING: core.integrity not found — skipping integrity gate")
        ok = True
    _INTEGRITY_CHECKED = True
    return ok




from core.runner.experiment_runner import ExperimentRunner
from core.runner.sweep_runner import SweepRunner
from core.runner.scheduler import Scheduler

from core.kernel.engine_registry import EngineRegistry

class Dispatcher:
    """
    Routes normalized HIL envelopes to the correct engine through the Orchestrator.

    Enforcement rules:
      - All envelopes must carry source="hil" (set by dispatch_interface.py)
      - RUN/PROBE/SWEEP envelopes must identify an experiment target
      - No raw shell commands may reach this layer

    Pipeline:
      HIL envelope -> source gate -> integrity gate -> scheduler -> engine -> result
    """

    # Verbs that require an experiment or invariant target
    _EXPERIMENT_VERBS: frozenset[str] = frozenset({"RUN", "PROBE", "SWEEP", "TRACE", "OBSERVE"})

    def __init__(self, skip_integrity: bool = False):
        self._skip_integrity = skip_integrity
        self.experiment_runner = ExperimentRunner()
        self.sweep_runner = SweepRunner(self.experiment_runner)
        self.scheduler = Scheduler(self.experiment_runner, self.sweep_runner)

    def route(self, envelope: dict) -> dict:
        # ── HIL source gate ───────────────────────────────────────────────
        if envelope.get("source") != "hil":
            return {
                "status": "HIL_REQUIRED",
                "message": (
                    "Execution rejected: envelope did not originate from the HIL pipeline. "
                    "All experiment execution must use the HIL command language.\n"
                    "Example: RUN experiment:epistemic_irreversibility engine:python"
                ),
            }

        # ── Experiment target gate ────────────────────────────────────────
        verb = envelope.get("verb", "").upper()
        if verb in self._EXPERIMENT_VERBS:
            targets = envelope.get("targets", [])
            has_experiment_target = any(
                str(t).startswith(("experiment:", "invariant:", "parameter:"))
                for t in targets
            )
            if not has_experiment_target and not envelope.get("target"):
                return {
                    "status": "HIL_INVALID",
                    "message": (
                        f"{verb} requires an experiment or invariant target.\n"
                        f"Example: {verb} experiment:<name> engine:python"
                    ),
                }

        # ── Phase 9: integrity gate ──────────────────────────────────────
        if not self._skip_integrity:
            ok = _run_integrity_gate(verbose=False)
            if not ok:
                return {
                    "status":  "INVALID_ENVIRONMENT",
                    "message": "Integrity gate failed — experiment halted. "
                               "Run core/integrity/integrity_tests.py for details.",
                    "artifact_flag": "INVALID_ENVIRONMENT",
                }

        # ── Orchestrator dispatch ────────────────────────────────────────
        return self.scheduler.dispatch(envelope)
