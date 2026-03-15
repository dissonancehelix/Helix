# HIL — Helix Interface Language
# All commands entering Helix must normalize through this module before dispatch.

from .grammar import parse_command
from .validator import validate_command
from .normalizer import normalize_command

__all__ = ["parse_command", "validate_command", "normalize_command"]
