"""
Probe Interface — 04_labs/probes/probe_interface.py

Optional base class for Helix probe instruments.
Probes may inherit from HelixProbe or implement the contract directly
via a standalone __main__ block.
"""

from __future__ import annotations
import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class HelixProbe(ABC):
    """
    Base class for Helix probe instruments.

    Subclasses must implement run() and declare VERSION at class/module level.
    """

    VERSION: str = "1.0.0"

    @abstractmethod
    def run(self, dataset: dict) -> dict:
        """
        Execute the probe measurement on a dataset.

        Returns a result dict including at minimum:
            signal:      float  — primary measurement value
            confidence:  str    — qualitative confidence label
            passed:      bool   — detection threshold met
            probe_name:  str    — canonical probe name
            domain:      str    — domain of the dataset
        """
        ...

    def execute_from_env(self) -> None:
        """
        Read HELIX_SYSTEM_INPUT and HELIX_ARTIFACT_DIR, run the probe,
        write probe_result.json, and exit with appropriate code.
        """
        input_path = os.environ.get("HELIX_SYSTEM_INPUT")
        artifact_dir = os.environ.get("HELIX_ARTIFACT_DIR")

        if not input_path or not artifact_dir:
            print(
                "[PROBE] ERROR: HELIX_SYSTEM_INPUT and HELIX_ARTIFACT_DIR must be set.",
                file=sys.stderr,
            )
            sys.exit(2)

        with open(input_path, "r", encoding="utf-8") as f:
            system_input = json.load(f)

        dataset = system_input.get("dataset", system_input)
        result = self.run(dataset)

        out_path = Path(artifact_dir) / "probe_result.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        sys.exit(0 if result.get("passed", False) else 1)
