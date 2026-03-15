# Python Engine — Helix execution substrate for computational experiments.
# This is the primary engine for non-spatial, mathematical experiments.

import importlib
import os


PROBE_REGISTRY = {
    "network":       "probes.network",
    "dynamical":     "probes.dynamical",
    "oscillator":    "probes.oscillator",
    "cellular":      "probes.cellular",
    "evolutionary":  "probes.evolutionary",
    "information":   "probes.information",
    "dataset":       "probes.dataset",
}


class PythonEngine:
    """
    Helix Python execution engine.
    Receives normalized HIL envelopes and routes them to probe modules.
    """

    name = "python"

    def run(self, envelope: dict) -> dict:
        target = envelope.get("target", "")
        params = envelope.get("params", {})

        probe_key = target.split(".")[-1] if "." in target else target

        if probe_key not in PROBE_REGISTRY:
            return {"status": "error", "message": f"Unknown probe '{probe_key}'"}

        try:
            module_path = PROBE_REGISTRY[probe_key]
            module = importlib.import_module(f"engines.python.{module_path}")
            result = module.run(params)
            return {"status": "ok", "result": result}
        except ImportError as e:
            return {"status": "not_implemented", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
