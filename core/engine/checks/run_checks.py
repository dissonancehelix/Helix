#!/usr/bin/env python3
"""core/engine/checks entry point.

Wraps the existing workspace boundary checker so that core/engine/checks/ is the
canonical location for drift checks going forward, without relocating the
underlying harness in this phase.
"""
from __future__ import annotations

import sys
from pathlib import Path

CORE_ENGINE = Path(__file__).resolve().parents[1]
HARNESS = CORE_ENGINE / "agent_harness"

sys.path.insert(0, str(HARNESS))

import check_workspace  # type: ignore  # noqa: E402


def main() -> int:
    return check_workspace.main()


if __name__ == "__main__":
    raise SystemExit(main())
