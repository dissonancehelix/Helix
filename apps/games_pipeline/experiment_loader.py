import os

class GodotExperimentLoader:
    """
    Maps experiment names to Godot scene files.
    """
    SCENE_MAPPING = {
        "oscillator_lock_probe": "oscillator_field.tscn",
        "swarm_synchronization": "agent_swarm.tscn",
        "coordination_game": "coordination_game.tscn",
        "flocking_system": "flocking_system.tscn",
        "test_scene": "test_scene.tscn"
    }

    def __init__(self, templates_dir: str):
        self.templates_dir = templates_dir

    def load(self, experiment_name: str) -> str | None:
        scene_file = self.SCENE_MAPPING.get(experiment_name)
        if not scene_file:
            # Fallback to direct name if it ends in .tscn
            if experiment_name.endswith(".tscn"):
                scene_file = experiment_name
            else:
                return None
        
        full_path = os.path.join(self.templates_dir, scene_file)
        # We don't necessarily need to check existence here if it's handled by adapter
        return full_path
