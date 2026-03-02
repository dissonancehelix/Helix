import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
SPINE_PATH = ROOT / "artifacts" / "spine_state.json"

@dataclass
class SpineState:
    schema_version: str
    baseline_beam_hash: Optional[str]
    current_dataset_hash: str
    last_successful_run_timestamp: Optional[str]
    active_axes: List[str]
    last_run_manifest_hash: Optional[str]

    def save(self):
        SPINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SPINE_PATH, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "SpineState":
        if not SPINE_PATH.exists():
            return cls(
                schema_version="unknown",
                baseline_beam_hash=None,
                current_dataset_hash="unknown",
                last_successful_run_timestamp=None,
                active_axes=["Substrate_S1c", "Persistence_Ontology"],
                last_run_manifest_hash=None
            )
        with open(SPINE_PATH, "r") as f:
            return cls(**json.load(f))
