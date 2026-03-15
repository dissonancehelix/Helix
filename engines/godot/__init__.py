# Helix Godot Engine
# Spatial simulation substrate for embodied, multi-agent, and physics experiments.
# Communicates with a headless Godot process via telemetry bridge.

from .adapter import GodotAdapter

__all__ = ["GodotAdapter"]
