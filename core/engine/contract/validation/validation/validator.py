from __future__ import annotations
import numpy as np

class ReplicationValidator:
    """
    Runs an experiment multiple times to check for result consistency.
    """
    def __init__(self, runner, replications: int = 5):
        self.runner = runner
        self.replications = replications

    def validate(self, envelope: dict) -> dict:
        results = []
        # We need to tell the runner to skip validation for these internal runs
        validation_envelope = envelope.copy()
        validation_envelope["skip_validation"] = True
        
        for _ in range(self.replications):
            res = self.runner.run(validation_envelope)
            if res.get("status") == "ok":
                # Extract a primary numeric signal if possible
                signal = self._extract_signal(res.get("result", {}))
                results.append(signal)

        if not results:
            return {"status": "error", "message": "No successful replications"}

        variance = float(np.var(results)) if len(results) > 1 else 0.0
        passed = variance < 0.05 # Default threshold
        
        return {
            "variance": variance,
            "passed": passed,
            "count": len(results)
        }

    def _extract_signal(self, result: dict) -> float:
        # Heuristic to find a numeric signal in the result
        for key in ["signal", "accuracy", "fitness", "score", "magnitude"]:
            if key in result and isinstance(result[key], (int, float)):
                return float(result[key])
        # Fallback to first numeric value found
        for v in result.values():
            if isinstance(v, (int, float)):
                return float(v)
        return 0.0
