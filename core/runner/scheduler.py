from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.runner.experiment_runner import ExperimentRunner
    from core.runner.sweep_runner import SweepRunner

class Scheduler:
    """
    Handles batch runs, repeated experiments, and sweep queuing.
    """
    def __init__(self, experiment_runner: ExperimentRunner, sweep_runner: SweepRunner):
        self.experiment_runner = experiment_runner
        self.sweep_runner = sweep_runner
        
        # Resolve repo root relative to core/runner/scheduler.py
        import os
        from pathlib import Path
        repo_root = Path(__file__).resolve().parent.parent.parent
        from core.kernel.system_handler import SystemHandler
        self.system_handler = SystemHandler(str(repo_root))

    def dispatch(self, envelope: dict) -> dict:
        verb = envelope.get("verb", "")
        
        if verb == "SWEEP":
            return self._handle_sweep(envelope)
        elif verb == "RUN":
            return self._handle_run(envelope)
        elif verb == "EXPORT":
            return self._handle_export(envelope)
        elif verb == "ANALYZE":
            return self._handle_analyze(envelope)
        elif verb in ("SYSTEM", "OPERATOR"):
            return self.system_handler.handle(envelope)
        else:
            # Fallback for PROBE, TRACE, etc.
            return self.experiment_runner.run(envelope)

    def _handle_run(self, envelope: dict) -> dict:
        params = envelope.get("params", {})
        # Check for repeat parameter
        # In HIL, params might be strings or objects. normalize.py usually converts them.
        repeat = params.get("repeat", 1)
        try:
            repeat = int(repeat)
        except (ValueError, TypeError):
            repeat = 1
            
        if repeat <= 1:
            return self.experiment_runner.run(envelope)
        
        results = []
        for i in range(repeat):
            # We might want to tag the run index
            res = self.experiment_runner.run(envelope)
            results.append(res)
            
        return {
            "status": "ok",
            "message": f"Executed {repeat} runs",
            "runs": results
        }

    def _handle_sweep(self, envelope: dict) -> dict:
        params = envelope.get("params", {})
        
        # SWEEP parameter:coupling_strength range:0..1 steps:100
        # RUN experiment:oscillator_lock_probe
        
        parameter = envelope.get("target") # Usually the first target is the parameter in SWEEP
        range_expr = params.get("range")
        steps = params.get("steps", 10)
        
        try:
            steps = int(steps)
        except (ValueError, TypeError):
            steps = 10
            
        # The next command in the pipeline would be the RUN command.
        # But in a single dispatch, we might have nested info or we assume the target is the experiment
        # if the verb is RUN but we are in a sweep context.
        
        # Actually, the HIL parser for SWEEP might produce a complex AST.
        # For now, let's assume the envelope contains what we need.
        
        experiment = params.get("experiment")
        if not experiment:
            for t in envelope.get("targets", []):
                if isinstance(t, str) and t.startswith("experiment:"):
                    experiment = t.split(":", 1)[1]
                    break
        
        experiment = experiment or "unknown_experiment"
        engine = params.get("engine", "python")
        
        # Parse range if it's a string "0..1"
        low, high = 0.0, 1.0
        if isinstance(range_expr, str) and ".." in range_expr:
            try:
                parts = range_expr.split("..")
                low = float(parts[0])
                high = float(parts[1])
            except ValueError:
                pass
        
        return self.sweep_runner.run_sweep(
            parameter_name=parameter,
            low=low,
            high=high,
            steps=steps,
            experiment_name=experiment,
            engine_name=engine,
            base_params=params
        )

    def _handle_export(self, envelope: dict) -> dict:
        target = envelope.get("target", "").lower()
        params = envelope.get("params", {})
        fmt = params.get("format", "wiki").lower()
        output = params.get("output", "helix_wiki")

        if target == "atlas" and fmt == "wiki":
            try:
                from interface.wiki.wiki_exporter import WikiExporter
                exporter = WikiExporter(output_dir=output)
                exporter.export()
                return {"status": "ok", "message": f"Wiki exported to {output}"}
            except Exception as e:
                return {"status": "error", "message": f"Export failed: {e}"}
        
        return {"status": "error", "message": f"Export target/format {target}/{fmt} not supported"}

    def _handle_analyze(self, envelope: dict) -> dict:
        target = envelope.get("target", "").lower()
        if target == "atlas":
            try:
                from core.analysis.invariant_engine import InvariantEngine
                engine = InvariantEngine()
                # Run batch analysis on all artifacts
                results = []
                for art_dir in engine._get_historical_artifacts():
                    res = engine.analyze_new_artifact(art_dir)
                    if res: results.append(res)
                return {"status": "ok", "count": len(results)}
            except Exception as e:
                return {"status": "error", "message": f"Analysis failed: {e}"}
        
        return {"status": "error", "message": f"Analysis target {target} not supported"}
