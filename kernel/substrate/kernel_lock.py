"""
Kernel Lock — 03_engines/substrate/kernel_lock.py

Set or remove chattr +i (immutable flag) on 00_kernel/ via Linux/WSL2.
On Windows, reports unavailable — no enforcement applied.
"""

from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path


def _is_linux() -> bool:
    return sys.platform.startswith("linux")


def lock_kernel(root: str | Path) -> bool:
    """
    Set chattr +i on all files in 00_kernel/ (Linux/WSL2 only).

    Returns True on success, False otherwise.
    """
    root = Path(root)
    kernel_dir = root / "00_kernel"

    if not _is_linux():
        print("[KERNEL_LOCK] chattr requires Linux/WSL2 — no enforcement on Windows.")
        return False

    if not kernel_dir.exists():
        print(f"[KERNEL_LOCK] 00_kernel/ not found at {kernel_dir}")
        return False

    try:
        result = subprocess.run(
            ["sudo", "chattr", "-R", "+i", str(kernel_dir)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"[KERNEL_LOCK] 00_kernel/ locked (chattr +i).")
            return True
        else:
            print(f"[KERNEL_LOCK] chattr failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("[KERNEL_LOCK] chattr not found — install e2fsprogs.")
        return False


def unlock_kernel(root: str | Path) -> bool:
    """
    Remove chattr +i from 00_kernel/ (Linux/WSL2 only).
    Requires env var HELIX_KERNEL_UNLOCK=1.
    """
    root = Path(root)
    kernel_dir = root / "00_kernel"

    if not _is_linux():
        print("[KERNEL_LOCK] chattr requires Linux/WSL2 — no enforcement on Windows.")
        return False

    if os.environ.get("HELIX_KERNEL_UNLOCK") != "1":
        print("[KERNEL_LOCK] HELIX_KERNEL_UNLOCK=1 required to unlock kernel.")
        return False

    try:
        result = subprocess.run(
            ["sudo", "chattr", "-R", "-i", str(kernel_dir)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"[KERNEL_LOCK] 00_kernel/ unlocked.")
            return True
        else:
            print(f"[KERNEL_LOCK] chattr -i failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("[KERNEL_LOCK] chattr not found — install e2fsprogs.")
        return False


def kernel_status(root: str | Path) -> dict:
    """
    Return the current kernel lock status.
    """
    root = Path(root)
    kernel_dir = root / "00_kernel"

    if not _is_linux():
        return {
            "locked": None,
            "reason": "Windows — chattr not available",
            "kernel_dir": str(kernel_dir),
        }

    if not kernel_dir.exists():
        return {"locked": None, "reason": "00_kernel/ not found", "kernel_dir": str(kernel_dir)}

    # Check one file for immutable flag using lsattr
    sample_files = list(kernel_dir.rglob("*.py"))
    if not sample_files:
        return {"locked": None, "reason": "no .py files in 00_kernel/", "kernel_dir": str(kernel_dir)}

    try:
        result = subprocess.run(
            ["lsattr", str(sample_files[0])],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            attrs = result.stdout.split()[0] if result.stdout.split() else ""
            locked = "i" in attrs
            return {"locked": locked, "kernel_dir": str(kernel_dir), "sample_file": str(sample_files[0])}
    except FileNotFoundError:
        pass

    return {"locked": None, "reason": "lsattr not found", "kernel_dir": str(kernel_dir)}
