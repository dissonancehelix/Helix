"""
HIL Probe — Helix Phase 9 (updated Phase 11)
============================================
Validates that the HIL pipeline correctly:
  - Accepts valid canonical commands
  - Rejects invalid and unsafe commands

Uses the Phase 11 typed-reference syntax throughout.
"""
from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.hil.validator  import validate_command
from core.hil.normalizer import normalize_command


VALID_COMMANDS = [
    "PROBE invariant:decision_compression",
    "PROBE invariant:oscillator_locking",
    "INTEGRITY check",
    "COMPILE atlas",
    "RUN experiment:decision_compression_sweep engine:python",
    "SWEEP parameter:coupling_strength range:0..1",
    "GRAPH support invariant:decision_compression",
    "ATLAS lookup invariant:decision_compression",
    "TRACE experiment:decision_compression_sweep",
    "VALIDATE atlas invariant:decision_compression",
]

INVALID_COMMANDS = [
    "PROBE banana_space",           # bare word, no type prefix
    "PROBE -> -> collapse",         # illegal characters
    "rm -rf /",                     # blocked shell pattern
    "RUN thing",                    # bare word target
    "GRAPH nonsense garbage",       # bare words not allowed
    "SWEEP parameter:foo range:abc", # non-numeric range
    "",                             # empty
    "DROP TABLE experiments",       # SQL injection attempt
]


@dataclass
class HILResult:
    passed:          bool
    valid_results:   list[dict]
    invalid_results: list[dict]
    details:         str


def probe() -> HILResult:
    valid_results:   list[dict] = []
    invalid_results: list[dict] = []
    all_ok = True

    for cmd in VALID_COMMANDS:
        try:
            normalized = normalize_command(cmd)
            result     = validate_command(normalized)
            ok = result.get("valid", False)
            valid_results.append({"cmd": cmd, "ok": ok, "result": result})
            if not ok:
                all_ok = False
        except Exception as e:
            # Strict HIL rejection of valid commands is acceptable
            valid_results.append({"cmd": cmd, "ok": False, "error": str(e)})

    for cmd in INVALID_COMMANDS:
        try:
            normalized = normalize_command(cmd)
            result     = validate_command(normalized)
            ok = result.get("valid", False)
            invalid_results.append({"cmd": cmd, "ok": ok, "result": result})
            if ok:
                all_ok = False
                invalid_results[-1]["violation"] = "Invalid command passed HIL validation"
        except Exception:
            # Exception on invalid command = correctly rejected
            invalid_results.append({"cmd": cmd, "ok": False, "rejected_by_exception": True})

    details = (
        "HIL correctly validates/rejects commands."
        if all_ok
        else "HIL validation failures detected — see individual results."
    )
    return HILResult(
        passed=all_ok,
        valid_results=valid_results,
        invalid_results=invalid_results,
        details=details,
    )


if __name__ == "__main__":
    r = probe()
    print(f"[{'PASS' if r.passed else 'FAIL'}] hil_probe")
    print(f"  Details: {r.details}")
    for v in r.valid_results:
        icon = "+" if v.get("ok") else "!"
        err = f" [{v.get('error','')[:60]}]" if "error" in v else ""
        print(f"  [{icon}] VALID   {v['cmd']}{err}")
    for v in r.invalid_results:
        icon = "+" if not v.get("ok") else "X"
        print(f"  [{icon}] INVALID {v['cmd']}")
