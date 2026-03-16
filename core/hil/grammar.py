"""
HIL Grammar — Compat Shim
==========================
Preserved for backward compatibility with pre-Phase-11 callers.
Internally delegates to the new core.hil.parser system.

New code should import directly from:
  core.hil.parser          (parse)
  core.hil.validator       (validate)
  core.hil.normalizer      (normalize)
  core.hil.command_registry (VALID_VERBS, get_spec)
"""
from __future__ import annotations

# ── Legacy constants (kept for compat) ────────────────────────────────────────
from core.hil.command_registry import VALID_VERBS as _VERBS

HIL_VERBS: set[str] = {v.lower() for v in _VERBS}

GRAPH_SUBCOMMANDS: set[str] = {"build", "query", "cluster", "export", "support", "trace"}

HIL_SCHEMA: dict = {
    "run":       {"required": ["target"], "optional": ["params", "mode", "engine"]},
    "probe":     {"required": ["target"], "optional": ["depth", "substrate", "engine"]},
    "sweep":     {"required": ["target"], "optional": ["range", "steps", "engine"]},
    "observe":   {"required": ["target"], "optional": ["window", "metric"]},
    "report":    {"required": [],         "optional": ["format", "output"]},
    "validate":  {"required": [],         "optional": ["strict"]},
    "reset":     {"required": [],         "optional": ["scope"]},
    "graph":     {"required": [],         "optional": ["node", "format"]},
    "integrity": {"required": [],         "optional": ["verbose", "no_atlas"]},
    "compile":   {"required": [],         "optional": ["overwrite", "quiet"]},
    "atlas":     {"required": [],         "optional": ["format", "verbose"]},
    "trace":     {"required": ["target"], "optional": ["depth", "format"]},
}


# ── Legacy parse_command ───────────────────────────────────────────────────────
def parse_command(raw: str) -> dict:
    """
    Legacy API: parse raw string -> command dict.
    Now delegates to the full HIL parser internally.
    """
    from core.hil.normalizer import normalize_command
    return normalize_command(raw)
