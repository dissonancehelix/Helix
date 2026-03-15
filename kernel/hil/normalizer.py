# HIL Normalizer
# Converts a validated HIL command into a canonical normalized form
# ready for dispatch to the appropriate engine or subsystem.

from .grammar import parse_command
from .validator import validate_command


def normalize_command(raw: str) -> dict:
    """
    Full pipeline: parse → validate → normalize.
    Returns a normalized command envelope for the dispatcher.
    """
    cmd = parse_command(raw)
    validate_command(cmd)

    normalized = {
        "verb":    cmd["verb"],
        "target":  cmd.get("target"),
        "params":  cmd.get("params", {}),
        "source":  "hil",
        "version": "1.0",
    }
    return normalized
