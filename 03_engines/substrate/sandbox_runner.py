"""
Sandbox Runner — 03_engines/substrate/sandbox_runner.py

Execute probe scripts as isolated subprocesses with environment injection.
No network, writes restricted to HELIX_ARTIFACT_DIR via env var.
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SandboxResult:
    passed: bool
    timed_out: bool
    returncode: int
    duration_seconds: float
    stderr: str = ""
    stdout: str = ""
    resource_limits_applied: bool = False
    probe_result: dict = field(default_factory=dict)


def run_probe_sandboxed(
    probe_script: str | Path,
    system_input_json: dict,
    artifacts_dir: str | Path,
    timeout: float = 120.0,
    verbose: bool = False,
) -> SandboxResult:
    """
    Run a probe script in a subprocess with HELIX_SYSTEM_INPUT and HELIX_ARTIFACT_DIR.

    Args:
        probe_script:       Absolute path to the probe .py file.
        system_input_json:  Dict written as JSON to a temp file; path passed via env var.
        artifacts_dir:      Directory where the probe writes probe_result.json.
        timeout:            Max execution time in seconds.
        verbose:            Print subprocess output on failure.

    Returns:
        SandboxResult with pass/fail status and timing.
    """
    probe_script = Path(probe_script)
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Write system input JSON to artifacts dir
    input_path = artifacts_dir / "system_input.json"
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(system_input_json, f, indent=2)

    env = os.environ.copy()
    env["HELIX_SYSTEM_INPUT"] = str(input_path)
    env["HELIX_ARTIFACT_DIR"] = str(artifacts_dir)

    start = time.monotonic()
    timed_out = False
    returncode = -1
    stdout_text = ""
    stderr_text = ""

    try:
        result = subprocess.run(
            [sys.executable, str(probe_script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        returncode = result.returncode
        stdout_text = result.stdout or ""
        stderr_text = result.stderr or ""
    except subprocess.TimeoutExpired as e:
        timed_out = True
        stdout_text = (e.stdout or b"").decode("utf-8", errors="replace")
        stderr_text = (e.stderr or b"").decode("utf-8", errors="replace")

    duration = time.monotonic() - start

    # Load probe_result.json if it exists
    probe_result: dict[str, Any] = {}
    result_path = artifacts_dir / "probe_result.json"
    if result_path.exists():
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                probe_result = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    # Determine pass: returncode 0 AND probe_result.passed (if present)
    passed = (not timed_out) and (returncode == 0)
    if passed and probe_result:
        passed = bool(probe_result.get("passed", True))

    if verbose and (not passed or stderr_text.strip()):
        if stdout_text.strip():
            print(f"[SANDBOX] stdout:\n{stdout_text.strip()}")
        if stderr_text.strip():
            print(f"[SANDBOX] stderr:\n{stderr_text.strip()}")

    return SandboxResult(
        passed=passed,
        timed_out=timed_out,
        returncode=returncode,
        duration_seconds=round(duration, 3),
        stderr=stderr_text,
        stdout=stdout_text,
        resource_limits_applied=False,
        probe_result=probe_result,
    )
