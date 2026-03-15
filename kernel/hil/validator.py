# HIL Validator
# Validates parsed HIL command dicts against schema constraints.

from .grammar import HIL_SCHEMA


def validate_command(cmd: dict) -> bool:
    """
    Validate a parsed HIL command against the schema.
    Raises ValueError on invalid commands.
    Returns True if valid.
    """
    verb = cmd.get("verb")
    if verb not in HIL_SCHEMA:
        raise ValueError(f"No schema defined for verb '{verb}'")

    schema = HIL_SCHEMA[verb]
    required = schema.get("required", [])

    for field in required:
        if field == "target" and not cmd.get("target"):
            raise ValueError(f"Verb '{verb}' requires a target")
        elif field in cmd.get("params", {}) is False:
            raise ValueError(f"Verb '{verb}' requires param '{field}'")

    return True
