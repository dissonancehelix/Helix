from __future__ import annotations
import os
import json
from engines.python.experiment_loader import PythonExperimentLoader
from engines.python.experiment_registry import (
    ExperimentLoadError,
    ExperimentNotFoundError,
    list_experiments,
)

class PythonAdapter:
    """
    Adapter for the Helix Python substrate.
    """
    def __init__(self):
        self.name = "python"
        self.loader = PythonExperimentLoader()

    def run_experiment(self, experiment_name: str, parameters: dict) -> dict:
        """
        Standard Phase 13 engine interface.
        Resolves experiment name via ExperimentRegistry, then executes.
        """
        try:
            module = self.loader.load(experiment_name)
        except ExperimentLoadError as e:
            return {"status": "error", "message": str(e)}

        if not module:
            valid = ", ".join(list_experiments())
            return {
                "status": "error",
                "message": (
                    f"Experiment '{experiment_name}' not found.\n"
                    f"Use: RUN experiment:<name> engine:python\n"
                    f"Registered: {valid}"
                ),
            }

        try:
            # 2. Execute experiment
            result_data = module.run(parameters)
            
            # Phase 13 says engine adapter is responsible for artifact writing.
            # However, ExperimentRunner in Phase 12 also does this.
            # We will return the result data and let the runner handle the orchestration
            # unless we want to strictly follow the 'artifact writing' responsibility here.
            # Let's provide a 'result' and optionally 'artifact_files'
            
            return {
                "status": "ok",
                "result": result_data
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run(self, envelope: dict) -> dict:
        """Compatibility method for Phase 12 ExperimentRunner."""
        target = envelope.get("target", "")
        params = envelope.get("params", {})
        return self.run_experiment(target, params)
