"""
HIL Normalizer
==============
Converts raw input into canonical HIL, two ways:

  normalize(raw)         -> str   canonical HIL string     (new API)
  normalize_command(raw) -> dict  legacy envelope dict     (compat API)

Pipeline:
  1. Alias resolution   (human-ish -> canonical shorthand)
  2. Parser             (canonical -> typed AST)
  3. canonical()        (AST -> deterministic canonical string)

Design note (SQL influence):
  Like SQL normalization, the same semantic query must always produce
  the same canonical string, regardless of input capitalization or spacing.
"""
from __future__ import annotations

from core.hil.aliases import resolve_alias
from core.hil.parser import parse
from core.hil.errors import HILError


def normalize(raw: str) -> str:
    """
    Normalize raw input to a canonical HIL string.
    Applies alias resolution before parsing.
    """
    tokens = raw.strip().split()
    if not tokens:
        from core.hil.errors import HILSyntaxError
        raise HILSyntaxError("Empty command", raw=raw)

    alias = resolve_alias(tokens)
    if alias:
        raw = alias

    cmd = parse(raw)
    return cmd.canonical()


def normalize_command(raw: str) -> dict:
    """
    Compat API: normalize raw input and return a legacy envelope dict.
    Used by hil_probe and other pre-Phase-11 callers.
    """
    tokens = raw.strip().split()
    if not tokens:
        from core.hil.errors import HILSyntaxError
        raise HILSyntaxError("Empty command", raw=raw)

    alias = resolve_alias(tokens)
    if alias:
        raw = alias

    cmd = parse(raw)
    primary = cmd.primary_target()
    return {
        "verb":      cmd.verb.lower(),
        "target":    str(primary) if primary else (cmd.subcommand or ""),
        "params":    {k: str(v) for k, v in cmd.params.items()},
        "source":    "hil",
        "version":   "1.0",
        "canonical": cmd.canonical(),
        "ast":       cmd.to_dict(),
    }
