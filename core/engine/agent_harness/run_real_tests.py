#!/usr/bin/env python3
"""Run Helix real-test smoke suite.

This runner executes existing repo harnesses and local fixture/dataset scripts.
It is intentionally a coordinator, not a replacement for the underlying tests.

Each command is run independently so one import or data failure does not hide the
rest of the test surface. The process exits non-zero if any required command
fails.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = ROOT / "artifacts" / "real_tests"


@dataclass
class TestCommand:
    name: str
    command: list[str]
    required: bool = True
    timeout_seconds: int = 120


@dataclass
class TestResult:
    name: str
    command: str
    required: bool
    exit_code: int | None
    passed: bool
    stdout_path: str
    stderr_path: str


def _run(test: TestCommand) -> TestResult:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = test.name.lower().replace(" ", "_").replace("/", "_")
    stdout_path = ARTIFACT_DIR / f"{safe_name}.stdout.txt"
    stderr_path = ARTIFACT_DIR / f"{safe_name}.stderr.txt"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    print(f"\n=== RUN {test.name} ===")
    print("$ " + " ".join(test.command))

    try:
        completed = subprocess.run(
            test.command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=test.timeout_seconds,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        exit_code: int | None = completed.returncode
        passed = completed.returncode == 0
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text((exc.stderr or "") + f"\nTIMEOUT after {test.timeout_seconds}s\n", encoding="utf-8")
        exit_code = None
        passed = False

    print(f"RESULT {test.name}: {'PASS' if passed else 'FAIL'}")
    if not passed:
        stderr = stderr_path.read_text(encoding="utf-8")[-4000:]
        stdout = stdout_path.read_text(encoding="utf-8")[-2000:]
        if stdout.strip():
            print("--- stdout tail ---")
            print(stdout)
        if stderr.strip():
            print("--- stderr tail ---")
            print(stderr)

    return TestResult(
        name=test.name,
        command=" ".join(test.command),
        required=test.required,
        exit_code=exit_code,
        passed=passed,
        stdout_path=str(stdout_path.relative_to(ROOT)),
        stderr_path=str(stderr_path.relative_to(ROOT)),
    )


def main() -> int:
    py = sys.executable
    tests = [
        TestCommand(
            name="workspace_contract",
            command=[py, "core/engine/checks/run_checks.py"],
            timeout_seconds=60,
        ),
        TestCommand(
            name="aoc_core_contract",
            command=[py, "core/engine/agent_harness/check_aoc_core.py"],
            timeout_seconds=60,
        ),
        TestCommand(
            name="manifest_health",
            command=[py, "core/engine/contract/validation/validation/manifest_health.py", "--verbose"],
            timeout_seconds=60,
        ),
        TestCommand(
            name="manifest_validator",
            command=[py, "core/engine/contract/validation/validation/manifest_validator.py"],
            timeout_seconds=60,
        ),
        TestCommand(
            name="structure_validator",
            command=[py, "core/engine/contract/validation/validation/structure_validator.py", "--verbose"],
            timeout_seconds=60,
        ),
        TestCommand(
            name="kuramoto_fixture",
            command=[py, "labs/invariants/validation/kuramoto_fixture.py", "--out", "artifacts/real_tests/kuramoto_fixture.json"],
            timeout_seconds=180,
        ),
        TestCommand(
            name="math_e2e",
            command=[py, "labs/invariants/e2e.py", "--K", "2.0", "--n", "50", "--steps", "500", "--json"],
            timeout_seconds=180,
        ),
        TestCommand(
            name="dcp_validation_baselines",
            command=[py, "labs/invariants/math/dcp_validation.py", "--mode", "baselines"],
            timeout_seconds=180,
        ),
        TestCommand(
            name="dcp_validation_games_null",
            command=[py, "labs/invariants/math/dcp_validation.py", "--mode", "null_tests", "--test", "3"],
            timeout_seconds=180,
        ),
    ]

    results = [_run(test) for test in tests]
    summary = {
        "passed": all(r.passed or not r.required for r in results),
        "total": len(results),
        "passed_count": sum(1 for r in results if r.passed),
        "failed_required": [r.name for r in results if r.required and not r.passed],
        "results": [asdict(r) for r in results],
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== REAL TEST SUMMARY ===")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
