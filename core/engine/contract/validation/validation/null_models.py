from __future__ import annotations

class NullModelTester:
    """
    Checks if a randomized/null model produces similar results to the experiment.
    """
    def __init__(self, runner):
        self.runner = runner

    def test(self, envelope: dict) -> dict:
        null_envelope = envelope.copy()
        null_envelope["skip_validation"] = True
        
        # Inject null flag into parameters for engine support
        params = null_envelope.get("params", {}).copy()
        params["null_control"] = True
        null_envelope["params"] = params
        
        original_res = self.runner.run({**envelope, "skip_validation": True})
        null_res = self.runner.run(null_envelope)
        
        if original_res.get("status") != "ok" or null_res.get("status") != "ok":
            return {"status": "error", "message": "Null model run failed"}
            
        orig_sig = self._extract_signal(original_res.get("result", {}))
        null_sig = self._extract_signal(null_res.get("result", {}))
        
        # We WANT a large difference from null model
        diff = abs(orig_sig - null_sig)
        significance = diff if orig_sig == 0 else diff / (abs(orig_sig) + 1e-9)
        
        return {
            "null_model_difference": significance,
            "passed": significance > 0.5 # Expecting at least 50% signal difference
        }

    def _extract_signal(self, result: dict) -> float:
        for key in ["signal", "accuracy", "fitness", "score"]:
            if key in result and isinstance(result[key], (int, float)):
                return float(result[key])
        return 0.0
