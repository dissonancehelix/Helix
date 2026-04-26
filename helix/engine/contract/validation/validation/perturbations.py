from __future__ import annotations
import random

class PerturbationTester:
    """
    Applies small parameter noise to check result stability.
    """
    def __init__(self, runner):
        self.runner = runner

    def test(self, envelope: dict) -> dict:
        original_params = envelope.get("params", {})
        perturbed_envelope = envelope.copy()
        perturbed_envelope["skip_validation"] = True
        
        # Apply ±5% noise to numeric parameters
        new_params = original_params.copy()
        for k, v in new_params.items():
            if isinstance(v, (int, float)) and v != 0:
                noise = 1.0 + (random.uniform(-0.05, 0.05))
                new_params[k] = v * noise
        
        perturbed_envelope["params"] = new_params
        
        original_res = self.runner.run({**envelope, "skip_validation": True})
        perturbed_res = self.runner.run(perturbed_envelope)
        
        if original_res.get("status") != "ok" or perturbed_res.get("status") != "ok":
            return {"status": "error", "message": "Perturbation run failed"}
            
        orig_sig = self._extract_signal(original_res.get("result", {}))
        pert_sig = self._extract_signal(perturbed_res.get("result", {}))
        
        delta = abs(orig_sig - pert_sig)
        resilience = 1.0 - delta if orig_sig == 0 else 1.0 - (delta / abs(orig_sig))
        resilience = max(0.0, resilience)
        
        return {
            "resilience": resilience,
            "passed": resilience > 0.8
        }

    def _extract_signal(self, result: dict) -> float:
        for key in ["signal", "accuracy", "fitness", "score"]:
            if key in result and isinstance(result[key], (int, float)):
                return float(result[key])
        return 0.0
