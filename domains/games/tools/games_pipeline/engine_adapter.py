from __future__ import annotations
import os
import subprocess
import json
import time
from engines.godot.experiment_loader import GodotExperimentLoader

class GodotAdapter:
    """
    Adapter for the Helix Godot substrate.
    """
    def __init__(self):
        self.name = "godot"
        self.godot_bin = os.environ.get("HELIX_GODOT_BIN", "godot")
        self.templates_dir = os.path.join(os.path.dirname(__file__), "scene_templates")
        self.loader = GodotExperimentLoader(self.templates_dir)

    def run_experiment(self, experiment_name: str, parameters: dict) -> dict:
        """
        Standard Phase 13 engine interface.
        """
        scene_path = self.loader.load(experiment_name)
        if not scene_path:
            return {"status": "error", "message": f"Scene not found for experiment '{experiment_name}'"}

        # In a real environment, we would launch Godot --headless
        # For Helix internal validation without a full Godot install:
        if os.environ.get("HELIX_SIMULATE_GODOT") == "1":
            time.sleep(1)
            return {
                "status": "ok",
                "result": {
                    "spatial_sync": 0.88,
                    "agent_count": parameters.get("agent_count", 100),
                    "substrate": "godot_spatial"
                }
            }

        bridge_path = os.path.join(os.path.dirname(__file__), "helix_bridge.gd")
        args = [self.godot_bin, "--headless", "--script", bridge_path]
        
        # Pass experiment and parameters after '--' to be parsed by bread
        args.append("--")
        args.append(f"experiment={experiment_name}")
        args.append(f"scene={scene_path}")
        for k, v in parameters.items():
            args.append(f"{k}={v}")

        try:
            # Note: Godot writes to user:// (usually ~/.local/share/godot/...)
            # A real implementation would capture that or use a specific output path.
            process = subprocess.run(args, capture_output=True, text=True, timeout=120)
            
            if process.returncode != 0:
                return {
                    "status": "error",
                    "message": f"Godot exited with code {process.returncode}",
                    "stderr": process.stderr
                }
            
            # Logic to find and load results from Godot's output
            # For now, we return the stdout as a placeholder result if no JSON found
            return {
                "status": "ok",
                "result": {"stdout": process.stdout}
            }
            
        except FileNotFoundError:
            return {
                "status": "error", 
                "message": f"Godot binary '{self.godot_bin}' not found. Set HELIX_GODOT_BIN or HELIX_SIMULATE_GODOT=1."
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Godot experiment timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run(self, envelope: dict) -> dict:
        """Compatibility method for Phase 12 ExperimentRunner."""
        target = envelope.get("target", "")
        params = envelope.get("params", {})
        return self.run_experiment(target, params)
