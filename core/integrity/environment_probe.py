"""
Environment Probe — Helix
=========================
Verifies Helix is running inside a supported execution environment.

Supported environments (in priority order):
  1. MSYS2   — any MSYSTEM value (MSYS, MINGW64, UCRT64, CLANG64, …)
  2. Windows  — sys.platform == "win32" without MSYSTEM (bare CPython)

Failure means the environment is entirely unrecognised.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass


# All known MSYS2 subsystem names
MSYS2_SYSTEMS = {
    "MSYS", "MINGW32", "MINGW64",
    "UCRT64", "CLANG32", "CLANG64", "CLANGARM64",
}


@dataclass
class EnvironmentResult:
    passed:    bool
    signature: str
    details:   str


def probe() -> EnvironmentResult:
    msystem = os.environ.get("MSYSTEM", "")

    # Primary: MSYS2 (any subsystem)
    if msystem:
        label = msystem if msystem in MSYS2_SYSTEMS else f"MSYS2/{msystem}"
        return EnvironmentResult(
            passed=True,
            signature=msystem,
            details=f"MSYS2 environment confirmed (MSYSTEM={msystem}).",
        )

    # Fallback: bare Windows CPython (no MSYS2 shell)
    if sys.platform == "win32":
        sig = f"win32/CPython-{sys.version.split()[0]}"
        return EnvironmentResult(
            passed=True,
            signature=sig,
            details=f"Windows native CPython environment ({sig}).",
        )

    return EnvironmentResult(
        passed=False,
        signature="UNKNOWN",
        details=(
            "Unrecognised environment. "
            "Helix requires MSYS2 (any subsystem) or Windows CPython. "
            f"MSYSTEM={msystem!r}, platform={sys.platform!r}"
        ),
    )


if __name__ == "__main__":
    r = probe()
    print(f"[{'PASS' if r.passed else 'FAIL'}] environment_probe")
    print(f"  Signature: {r.signature}")
    print(f"  Details:   {r.details}")
