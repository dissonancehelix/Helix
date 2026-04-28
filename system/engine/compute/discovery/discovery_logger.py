import os
import json
import datetime
from pathlib import Path
from typing import Any, Dict

class DiscoveryLogger:
    """Logs discovery run results to artifacts/discovery_runs/."""
    
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parent.parent.parent
        self.log_dir = self.root / "artifacts" / "discovery_runs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_run(self, triggered_invariant: str, generated_commands: list, artifact_path: str = "") -> str:
        """Log a discovery run and return the log file path."""
        timestamp = datetime.datetime.now().isoformat()
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = self.log_dir / f"discovery_{run_id}.json"
        
        record = {
            "timestamp": timestamp,
            "triggered_invariant": triggered_invariant,
            "generated_commands": generated_commands,
            "experiment_artifact": artifact_path,
            "atlas_update": False, # TBD: Set to True if Atlas was updated
            "confidence_delta": 0.0, # TBD: Calculate delta
        }
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
            
        return str(log_file)
