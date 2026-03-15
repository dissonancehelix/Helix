# Kernel Dispatcher Router
# Resolves engine from HIL envelope and delegates execution.

from engines.python.engine import PythonEngine
# from engines.godot.adapter import GodotAdapter  # uncomment in Phase 9


ENGINE_REGISTRY = {
    "python": PythonEngine(),
    # "godot": GodotAdapter(),  # Phase 9
}


class Dispatcher:
    """
    Routes normalized HIL envelopes to the correct engine.
    """

    def route(self, envelope: dict) -> dict:
        target = envelope.get("target", "")
        engine_key = target.split(".")[0] if "." in target else "python"

        engine = ENGINE_REGISTRY.get(engine_key)
        if engine is None:
            return {"status": "error", "message": f"No engine registered for '{engine_key}'"}

        return engine.run(envelope)
