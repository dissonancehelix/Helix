from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.kernel.runtime.orchestration.experiment_runner import ExperimentRunner
    from core.kernel.runtime.orchestration.sweep_runner import SweepRunner


class Scheduler:
    """
    Routes HIL envelopes to the correct handler.

    Verb routing table
    ------------------
    RUN        -> _handle_run      (experiment_runner)
    SWEEP      -> _handle_sweep    (sweep_runner)
    PROBE      -> _handle_probe    (experiment_runner, probe convention)
    COMPILE    -> _handle_compile  (atlas_compiler)
    INTEGRITY  -> _handle_integrity (integrity_tests)
    ATLAS      -> _handle_atlas    (atlas queries)
    EXPORT     -> _handle_export   (wiki_exporter)
    ANALYZE    -> _handle_analyze  (invariant_engine)
    SYSTEM     -> system_handler
    OPERATOR   -> system_handler
    other      -> _handle_unimplemented (clear error, no silent crash)
    """

    def __init__(self, experiment_runner: ExperimentRunner, sweep_runner: SweepRunner):
        self.experiment_runner = experiment_runner
        self.sweep_runner = sweep_runner

        repo_root = Path(__file__).resolve().parent.parent.parent
        from core.kernel.system_handler import SystemHandler
        self.system_handler = SystemHandler(str(repo_root))
        self.repo_root = repo_root

    # ── Main dispatch ─────────────────────────────────────────────────────────

    def dispatch(self, envelope: dict) -> dict:
        verb = envelope.get("verb", "").upper()

        routes = {
            "RUN":       self._handle_run,
            "SWEEP":     self._handle_sweep,
            "PROBE":     self._handle_probe,
            "COMPILE":   self._handle_compile,
            "INTEGRITY": self._handle_integrity,
            "ATLAS":     self._handle_atlas,
            "EXPORT":    self._handle_export,
            "ANALYZE":   self._handle_analyze,
            "GRAPH":     self._handle_shortcut,
            "SCAN":      self._handle_shortcut,
            "INDEX":     self._handle_shortcut,
            "INGEST":    self._handle_shortcut,
            "LIST":      self._handle_shortcut,
            "TRAIN":     self._handle_shortcut,
            "ATTRIBUTION": self._handle_shortcut,
            "DISCOVER":  self._handle_shortcut,
            "SYSTEM":    lambda e: self.system_handler.handle(e),
            "OPERATOR":  lambda e: self.system_handler.handle(e),
        }

        handler = routes.get(verb, self._handle_unimplemented)
        return handler(envelope)

    # ── RUN ───────────────────────────────────────────────────────────────────

    def _handle_run(self, envelope: dict) -> dict:
        params = envelope.get("params", {})
        repeat = params.get("repeat", 1)
        try:
            repeat = int(repeat)
        except (ValueError, TypeError):
            repeat = 1

        if repeat <= 1:
            return self.experiment_runner.run(envelope)

        results = []
        for _ in range(repeat):
            results.append(self.experiment_runner.run(envelope))

        return {
            "status":  "ok",
            "message": f"Completed {repeat} runs",
            "runs":    results,
        }

    # ── PROBE ─────────────────────────────────────────────────────────────────

    def _handle_probe(self, envelope: dict) -> dict:
        """
        Route PROBE through the experiment runner using the same labs/invariants
        convention as RUN. Probe modules return their own status.
        """
        return self.experiment_runner.run(envelope)

    # ── SWEEP ─────────────────────────────────────────────────────────────────

    def _handle_sweep(self, envelope: dict) -> dict:
        params = envelope.get("params", {})

        parameter = envelope.get("target")
        range_expr = params.get("range")
        steps = params.get("steps", 10)
        try:
            steps = int(steps)
        except (ValueError, TypeError):
            steps = 10

        experiment = params.get("experiment")
        if not experiment:
            for t in envelope.get("targets", []):
                if isinstance(t, str) and t.startswith("experiment:"):
                    experiment = t.split(":", 1)[1]
                    break

        experiment = experiment or "unknown_experiment"
        engine = params.get("engine", "python")

        low, high = 0.0, 1.0
        if isinstance(range_expr, str) and ".." in range_expr:
            try:
                lo, hi = range_expr.split("..")
                low, high = float(lo), float(hi)
            except ValueError:
                pass

        return self.sweep_runner.run_sweep(
            parameter_name=parameter,
            low=low,
            high=high,
            steps=steps,
            experiment_name=experiment,
            engine_name=engine,
            base_params=params,
        )

    # ── COMPILE ───────────────────────────────────────────────────────────────

    def _handle_compile(self, envelope: dict) -> dict:
        subcommand = (envelope.get("subcommand") or "atlas").lower()

        if subcommand in ("atlas", "entries", "graph"):
            try:
                from core.compiler import atlas_compiler
                atlas_compiler.run(verbose=True)
                return {"status": "ok", "message": "Atlas compiled successfully."}
            except Exception as e:
                return {"status": "error", "message": f"Compile failed: {e}"}

        return {"status": "error", "message": f"Unknown COMPILE target: {subcommand}"}

    # ── INTEGRITY ─────────────────────────────────────────────────────────────

    def _handle_integrity(self, envelope: dict) -> dict:
        subcommand = (envelope.get("subcommand") or "check").lower()

        try:
            from core.integrity.integrity_tests import gate
            verbose = subcommand in ("report", "verbose")
            ok = gate(verbose=verbose)
            return {
                "status":  "ok" if ok else "FAIL",
                "message": "Integrity PASS — real execution environment confirmed."
                           if ok else "Integrity FAIL — environment may be simulated.",
                "passed":  ok,
            }
        except ImportError as e:
            return {"status": "error", "message": f"Integrity module unavailable: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Integrity check failed: {e}"}

    # ── ATLAS ─────────────────────────────────────────────────────────────────

    def _handle_atlas(self, envelope: dict) -> dict:
        subcommand = (envelope.get("subcommand") or "list").lower()
        target = envelope.get("target", "")

        if subcommand == "list":
            index_path = self.repo_root / "atlas" / "index.md"
            if index_path.exists():
                return {"status": "ok", "index": index_path.read_text()}
            return {"status": "error", "message": "codex/atlas/index.md not found — run COMPILE atlas"}

        if subcommand in ("lookup", "status", "verify"):
            # Resolve target to a markdown file
            targets = envelope.get("targets", [])
            for t in targets:
                t_str = str(t)
                if ":" in t_str:
                    kind, name = t_str.split(":", 1)
                    md_path = self.repo_root / "atlas" / f"{kind}s" / f"{name}.md"
                    if md_path.exists():
                        return {"status": "ok", "entry": md_path.read_text()}
                    return {
                        "status": "error",
                        "message": f"Atlas entry not found: {md_path.relative_to(self.repo_root)}",
                    }

            return {"status": "error", "message": f"ATLAS {subcommand} requires a typed target"}

        return {"status": "error", "message": f"Unknown ATLAS subcommand: {subcommand}"}

    # ── EXPORT ────────────────────────────────────────────────────────────────

    def _handle_export(self, envelope: dict) -> dict:
        target = envelope.get("target", "").lower()
        sub = (envelope.get("subcommand") or "").lower()
        params = envelope.get("params", {})
        fmt = params.get("format", "wiki").lower()
        output = params.get("output", "helix_wiki")

        if sub == "composer_report" or target == "composer_report":
            # Map COMPOSER_REPORT to music_lab/analysis/composer_reports.py?
            # Or just run it as an experiment shortcut
            return self._handle_shortcut(envelope)

        if target == "atlas" and fmt == "wiki":
            try:
                from interface.wiki.wiki_exporter import WikiExporter
                WikiExporter(output_dir=output).export()
                return {"status": "ok", "message": f"Wiki exported to {output}"}
            except Exception as e:
                return {"status": "error", "message": f"Export failed: {e}"}

        return {"status": "error", "message": f"Export {target}/{fmt} not supported"}

    # ── ANALYZE ───────────────────────────────────────────────────────────────

    def _handle_analyze(self, envelope: dict) -> dict:
        target = envelope.get("target", "").lower()
        sub = (envelope.get("subcommand") or "").lower()

        if target in ("music", "track", "composer", "soundtrack") or sub in ("music", "track", "composer", "soundtrack"):
            return self._handle_shortcut(envelope)

        if target == "atlas" or sub == "atlas":
            try:
                from core.analysis.invariant_engine import InvariantEngine
                engine = InvariantEngine()
                results = []
                for art_dir in engine._get_historical_artifacts():
                    res = engine.analyze_new_artifact(art_dir)
                    if res:
                        results.append(res)
                return {"status": "ok", "count": len(results)}
            except Exception as e:
                return {"status": "error", "message": f"Analysis failed: {e}"}

        return {"status": "error", "message": f"ANALYZE target {target!r} not supported"}

    # ── Shortcut routing ──────────────────────────────────────────────────────

    def _handle_shortcut(self, envelope: dict) -> dict:
        """Translates high-level HIL verbs/subcommands into underlying experiments."""
        verb = envelope.get("verb", "").upper()
        sub = (envelope.get("subcommand") or "").lower()
        target = (envelope.get("target") or "").lower()
        
        # Primary mapping: (verb, subcommand) -> experiment_name
        mapping = {
            ("SCAN", "filesystem"): "filesystem_scan",
            ("SCAN", "music_library"): "music_library_index",
            ("INDEX", "music_library"): "music_library_index",
            ("INGEST", "music_library"): "music_library_ingestion",
            ("INGEST", "composer_dataset"): "composer_training_sets",
            ("LIST", "tracks"): "music_lab_list",
            ("LIST", "composers"): "music_lab_list", 
            ("LIST", "franchises"): "music_lab_list",
            ("TRAIN", "composer_vectors"): "composer_style_vectors",
            ("ATTRIBUTION", "soundtrack"): "composer_attribution",
            ("GRAPH", "similarity"): "composer_similarity_graph",
            ("GRAPH", "motif"): "motif_network_analysis",
            ("GRAPH", "composer_styles"): "composer_style_space",
            ("ANALYZE", "track"): "music_symbolic_analysis",
            ("ANALYZE", "music"): "music_symbolic_analysis",
            ("ANALYZE", "composer"): "composer_style_vectors",
            ("ANALYZE", "soundtrack"): "soundtrack_analysis",
            ("DISCOVER", "regimes"): "discovery_engine",
            ("EXPORT", "composer_report"): "composer_report",
        }
        
        # Check by target if subcommand missing or doesn't match
        target_exp = mapping.get((verb, sub)) or mapping.get((verb, target))
        
        if not target_exp:
             return {"status": "error", "message": f"HIL Shortcut {verb} {sub or target} not mapped to an experiment"}

        # Reroute to RUN experiment:<target_exp>
        envelope["target"] = target_exp
        if "params" not in envelope: envelope["params"] = {}
        envelope["params"]["subcommand"] = sub or target
        
        return self._handle_run(envelope)

    # ── Unimplemented verbs ───────────────────────────────────────────────────

    def _handle_unimplemented(self, envelope: dict) -> dict:
        verb = envelope.get("verb", "UNKNOWN")
        return {
            "status": "not_implemented",
            "message": (
                f"{verb} is a valid HIL command but has no dispatcher implementation yet.\n"
                f"Working commands: RUN, SWEEP, PROBE, COMPILE, INTEGRITY, ATLAS, "
                f"EXPORT, ANALYZE, SYSTEM, OPERATOR"
            ),
        }
