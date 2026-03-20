"""
HIL Command Logger
==================
Records validated HIL commands as reproducible artifact records.

Every successfully validated command is logged to:
  artifacts/hil_command_log.jsonl

Log fields:
  timestamp        ISO-8601 UTC
  original         Raw input string
  canonical        Normalized HIL canonical form
  ast_summary      Full AST dict
  targets          List of typed reference strings
  engine           Resolved engine name
  dispatch_route   Inferred or explicit route
  validation_status Always "VALID" for logged commands
  integrity_gate   True/False/None if gate was checked

Design note:
  Commands are first-class research artifacts.
  The log enables full reproduction of any experiment sequence.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.hil.ast_nodes import HILCommand
from core.paths import ARTIFACTS_ROOT

_LOG_PATH = ARTIFACTS_ROOT / "hil_command_log.jsonl"

_ROUTE_MAP: dict[str, str] = {
    "PROBE":     "core/integrity -> labs/invariants",
    "RUN":       "engines/python/engine",
    "SWEEP":     "engines/python/engine",
    "COMPILE":   "compiler/atlas_compiler",
    "INTEGRITY": "core/integrity/integrity_tests",
    "ATLAS":     "codex/atlas/",
    "GRAPH":     "core/graph/",
    "VALIDATE":  "core/validator/",
    "TRACE":     "execution/artifacts/",
    "OBSERVE":   "engines/python/engine",
    "REPORT":    "execution/artifacts/",
}


class CommandLogger:
    """Static logger — no instance needed."""

    @staticmethod
    def log(
        cmd: HILCommand,
        integrity_ok: bool | None = None,
        dispatch_route: str = "",
    ) -> dict:
        """Write a record to the command log and return the record dict."""
        record = {
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "original":         cmd.raw,
            "canonical":        cmd.canonical(),
            "ast_summary":      cmd.to_dict(),
            "targets":          [str(t) for t in cmd.targets],
            "engine":           cmd.get_engine(),
            "dispatch_route":   dispatch_route or _ROUTE_MAP.get(cmd.verb, "unknown"),
            "validation_status": "VALID",
            "integrity_gate":   integrity_ok,
        }
        try:
            _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except OSError:
            pass  # logging must never block dispatch
        return record

    @staticmethod
    def read_log(limit: int = 50) -> list[dict]:
        """Read the last N log entries."""
        if not _LOG_PATH.exists():
            return []
        lines = _LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(ln) for ln in lines[-limit:]]

    @staticmethod
    def clear_log() -> None:
        """Truncate the command log (for testing)."""
        if _LOG_PATH.exists():
            _LOG_PATH.write_text("", encoding="utf-8")
