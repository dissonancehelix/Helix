"""
Entropy Probe — Helix
=====================
Detects simulated execution by checking that the OS entropy source
produces non-deterministic output across two consecutive reads.

Uses Python's os.urandom() — works natively on Windows, MSYS2, and Linux
without any subprocess or /dev/urandom dependency.

If outputs are identical, the environment is likely simulated or the
entropy source is broken.
"""

from __future__ import annotations

import os
import base64
from dataclasses import dataclass


@dataclass
class EntropyResult:
    passed:  bool
    sample1: str
    sample2: str
    details: str


def _sample() -> str:
    return base64.b64encode(os.urandom(32)).decode()


def probe() -> EntropyResult:
    try:
        s1 = _sample()
        s2 = _sample()
    except Exception as e:
        return EntropyResult(
            passed=False, sample1="", sample2="",
            details=f"Failed to read OS entropy source: {e}",
        )

    passed = bool(s1) and bool(s2) and s1 != s2
    details = (
        "Entropy source produces distinct outputs — real execution confirmed."
        if passed
        else (
            "Entropy samples are identical — execution may be simulated or "
            "os.urandom() is not functioning correctly."
            if s1 == s2
            else "Empty entropy output — os.urandom() unavailable."
        )
    )
    return EntropyResult(passed=passed, sample1=s1, sample2=s2, details=details)


if __name__ == "__main__":
    r = probe()
    print(f"[{'PASS' if r.passed else 'FAIL'}] entropy_probe")
    print(f"  Sample 1: {r.sample1}")
    print(f"  Sample 2: {r.sample2}")
    print(f"  Details:  {r.details}")
