"""
Architecture Watchdog — 03_engines/substrate/architecture_watchdog.py

Polls architecture integrity at a fixed interval and logs violations.
Runs blocking (foreground) or can be called from a background thread.
"""

from __future__ import annotations
import time
from pathlib import Path


POLL_INTERVAL_SECONDS = 60


def _run_check(root: Path, artifacts_root: Path) -> list[str]:
    """
    Run a lightweight integrity check. Returns list of violation strings.
    """
    violations: list[str] = []

    # Check required layers exist
    required = [
        "00_kernel", "01_basis", "02_governance", "03_engines",
        "04_labs", "05_applications", "codex/atlas", "execution/artifacts",
    ]
    for layer in required:
        if not (root / layer).exists():
            violations.append(f"MISSING_LAYER: {layer}/")

    # Check no unauthorized root items
    allowed = {
        ".git", ".gitignore", ".agents",
        "HELIX.md", "OPERATOR.md", "REBUILD_CHECKPOINT.md", "operator.json",
        "helix.py",
        "00_kernel", "01_basis", "02_governance", "03_engines",
        "04_labs", "05_applications", "codex/atlas", "execution/artifacts",
        "docs", "__pycache__",
    }
    for item in root.iterdir():
        if item.name not in allowed:
            violations.append(f"UNAUTHORIZED_ROOT: {item.name}")

    return violations


def start_watchdog(
    root: str | Path,
    artifacts_root: str | Path,
    background: bool = False,
    poll_interval: float = POLL_INTERVAL_SECONDS,
) -> None:
    """
    Start the architecture watchdog.

    Args:
        root:           Repo root path.
        artifacts_root: Path to execution/artifacts/ for logging violations.
        background:     If True, return immediately (caller manages threading).
        poll_interval:  Seconds between checks.
    """
    root = Path(root)
    artifacts_root = Path(artifacts_root)
    log_path = artifacts_root / "watchdog_violations.log"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    print(f"[WATCHDOG] Watching {root} (interval={poll_interval}s)")

    while True:
        violations = _run_check(root, artifacts_root)

        if violations:
            msg = f"[WATCHDOG] {len(violations)} violation(s) detected:\n"
            for v in violations:
                msg += f"  - {v}\n"
            print(msg.strip())
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    import datetime
                    ts = datetime.datetime.utcnow().isoformat()
                    f.write(f"\n[{ts}]\n{msg}")
            except OSError:
                pass
        else:
            print(f"[WATCHDOG] OK — architecture coherent.")

        if background:
            return

        try:
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n[WATCHDOG] Interrupted.")
            break
