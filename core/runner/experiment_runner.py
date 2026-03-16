from __future__ import annotations
import os
import time
import json
from core.runner.run_manifest import RunManifest
from core.runner.metadata_logger import MetadataLogger
from core.kernel.engine_registry import EngineRegistry
from core.compiler import atlas_compiler
from core.kernel.dispatcher import router
from core.integrity import integrity_tests

try:
    from core.validation.adversarial_runner import AdversarialRunner
except ImportError:
    AdversarialRunner = None

try:
    from core.analysis.invariant_engine import InvariantEngine
    _invariant_engine = InvariantEngine()
except ImportError:
    _invariant_engine = None

_HIL_SOURCE_REQUIRED = True  # Set False only in unit tests


class ExperimentRunner:
    """
    Executes a single experiment through a selected engine.
    Handles artifact generation and Atlas compiler invocation.

    Enforcement rule: all envelopes must originate from the HIL pipeline.
    An envelope produced by direct shell invocation will be rejected.
    """
    def __init__(self, engine_registry: dict | None = None):
        # engine_registry is legacy/optional now
        self.legacy_registry = engine_registry or {}

    def run(self, envelope: dict) -> dict:
        # ── HIL source gate ───────────────────────────────────────────────────
        if _HIL_SOURCE_REQUIRED and envelope.get("source") != "hil":
            return {
                "status": "HIL_REQUIRED",
                "message": (
                    "Direct execution is blocked. "
                    "All experiments must enter through the HIL pipeline.\n"
                    "Use: RUN experiment:<name> engine:<engine>\n"
                    "Example: RUN experiment:epistemic_irreversibility engine:python"
                ),
            }

        experiment_name = envelope.get("target", "unknown")
        # Handle engine resolving from target or params
        engine_name = envelope.get("engine", "python")
        parameters = envelope.get("params", {})
        hil_command = envelope.get("raw", "")

        # 1. Resolve Engine
        engine = EngineRegistry.get_engine(engine_name) or self.legacy_registry.get(engine_name)
        if not engine:
            return {"status": "error", "message": f"Engine '{engine_name}' not found"}

        # 2. Create deterministic artifact directory
        artifact_dir = self._create_artifact_dir(experiment_name)
        
        start_time = time.time()
        
        # 3. Execute Experiment
        result = engine.run(envelope)
        
        duration = time.time() - start_time
        
        # 4. Collect Output & Write Artifacts
        artifact_paths = []
        
        # Results
        results_path = os.path.join(artifact_dir, "results.json")
        with open(results_path, "w") as f:
            json.dump(result.get("result", {}), f, indent=4)
        artifact_paths.append("results.json")
        
        # Parameters
        params_path = os.path.join(artifact_dir, "parameters.json")
        with open(params_path, "w") as f:
            json.dump(parameters, f, indent=4)
        artifact_paths.append("parameters.json")
        
        # 5. Metadata Logger
        MetadataLogger.log(
            artifact_dir,
            duration,
            engine_name,
            parameters,
            result.get("status", "unknown")
        )
        artifact_paths.append("metadata.json")
        
        # 6. Run Manifest
        manifest = RunManifest(
            experiment=experiment_name,
            engine=engine_name,
            parameters=parameters,
            hil_command=hil_command,
            artifact_paths=artifact_paths
        )
        manifest.save(artifact_dir)
        artifact_paths.append("run_manifest.yaml")
        
        # 7. Adversarial Validation Layer (Phase 14)
        validation_report = None
        if AdversarialRunner and not envelope.get("skip_validation"):
            adv_runner = AdversarialRunner(self)
            validation_report = adv_runner.run_all(envelope, artifact_dir)
            artifact_paths.append("validation_report.yaml")
        
        # 8. Invariant Discovery Loop (Phase 15)
        discovered_invariants = None
        if _invariant_engine and not envelope.get("skip_discovery"):
            discovered_invariants = _invariant_engine.analyze_new_artifact(artifact_dir)
            if discovered_invariants:
                artifact_paths.append("feature_vector.json")

        # 9. Atlas Compiler Hook
        try:
            atlas_compiler.run(verbose=False)
        except Exception as e:
            # Don't fail the experiment if compiler fails
            print(f"[experiment_runner] Atlas compiler failed: {e}")
            
        return {
            "status": result.get("status"),
            "message": result.get("message"),
            "artifact_dir": artifact_dir,
            "result": result.get("result"),
            "manifest_path": os.path.join(artifact_dir, "run_manifest.yaml"),
            "validation": validation_report,
            "discovered_invariants": discovered_invariants
        }

    def _create_artifact_dir(self, experiment_name: str) -> str:
        # Normalize name for filesystem
        clean_name = experiment_name.replace(":", "_").replace(".", "_")
        base_path = os.path.join("artifacts", clean_name)
        
        if not os.path.exists("artifacts"):
            os.makedirs("artifacts", exist_ok=True)
            
        i = 1
        while True:
            dir_name = f"{base_path}_{i:03d}"
            # Convert to absolute path or keep relative to REPO_ROOT
            # Dispatcher/Runner usually run from REPO_ROOT
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                return dir_name
            i += 1
