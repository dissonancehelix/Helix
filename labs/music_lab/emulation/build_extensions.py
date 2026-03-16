"""
build_extensions.py — Tier B C-library build detector / builder
================================================================
Detects cmake, attempts to build libvgm and vgmstream from
labs/music_lab/tools/emulation/.  Writes build_status.json so all
other Tier B modules can gate themselves without re-running cmake.

This module NEVER raises — all failures are logged to build_status.json.
Tier A / C / D are completely unaffected by failure here.

Usage:
    python -m labs.music_lab.emulation.build_extensions [--force]
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths (relative to this file — avoids importing config at build time)
# ---------------------------------------------------------------------------

_THIS   = Path(__file__).parent
_EMU    = _THIS.parent / "tools" / "emulation"
_STATUS = _THIS / "build_status.json"

LIBRARIES = {
    "libvgm": {
        "src_dir": _EMU / "libvgm",
        "cmake_args": [
            "-DBUILD_PLAYER=OFF",
            "-DBUILD_VGM2WAV=OFF",
            "-DBUILD_TESTS=OFF",
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        "shared_lib_glob": "*.so*",   # Linux
        "dll_glob":        "*.dll",   # Windows
        "dylib_glob":      "*.dylib", # macOS
        "provides": "VGM emulation (YM2612, SN76489, YM2151, OPL, etc.)",
    },
    "vgmstream": {
        "src_dir": _EMU / "vgmstream",
        "cmake_args": [
            "-DBUILD_AUDACIOUS=OFF",
            "-DBUILD_WINAMP_PLUGIN=OFF",
            "-DBUILD_XMPLAY_PLUGIN=OFF",
            "-DBUILD_VGMSTREAM_CLI=OFF",
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        "shared_lib_glob": "*.so*",
        "dll_glob":        "*.dll",
        "dylib_glob":      "*.dylib",
        "provides": "Broad game audio format decoding (SPC, NSF, HES, GBS, KSS, …)",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_cmake() -> str | None:
    return shutil.which("cmake")


def _find_output_lib(build_dir: Path, lib_name: str) -> Path | None:
    """Return first shared library found in build_dir tree."""
    globs = ["*.so*", "*.dll", "*.dylib", f"lib{lib_name}*", f"{lib_name}*"]
    for g in globs:
        hits = list(build_dir.rglob(g))
        if hits:
            return hits[0]
    return None


def _build_one(name: str, spec: dict[str, Any], cmake_path: str, force: bool) -> dict[str, Any]:
    """Build a single library.  Returns a status record."""
    src = spec["src_dir"]
    build_dir = src / "_build"
    result: dict[str, Any] = {
        "library": name,
        "src_dir": str(src),
        "built": False,
        "skipped": False,
        "lib_path": None,
        "error": None,
        "ts": _ts(),
    }

    if not src.exists():
        result["skipped"] = True
        result["error"] = f"Source directory not found: {src} — run clone_tools.py first"
        return result

    # If already built and not forcing, reuse
    existing = _find_output_lib(build_dir, name)
    if existing and not force:
        result["built"] = True
        result["lib_path"] = str(existing)
        result["skipped"] = True  # skipped rebuild
        result["error"] = None
        return result

    build_dir.mkdir(exist_ok=True)

    # Configure
    cfg_cmd = [cmake_path, str(src), *spec["cmake_args"]]
    try:
        subprocess.run(
            cfg_cmd, cwd=build_dir, check=True,
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.CalledProcessError as e:
        result["error"] = f"cmake configure failed: {e.stderr[-2000:]}"
        return result
    except subprocess.TimeoutExpired:
        result["error"] = "cmake configure timed out (300 s)"
        return result
    except Exception as e:
        result["error"] = f"cmake configure error: {e}"
        return result

    # Build
    build_cmd = [cmake_path, "--build", str(build_dir), "--config", "Release",
                 "--parallel", "4"]
    try:
        subprocess.run(
            build_cmd, cwd=build_dir, check=True,
            capture_output=True, text=True, timeout=600,
        )
    except subprocess.CalledProcessError as e:
        result["error"] = f"cmake build failed: {e.stderr[-2000:]}"
        return result
    except subprocess.TimeoutExpired:
        result["error"] = "cmake build timed out (600 s)"
        return result
    except Exception as e:
        result["error"] = f"cmake build error: {e}"
        return result

    lib_path = _find_output_lib(build_dir, name)
    if lib_path:
        result["built"] = True
        result["lib_path"] = str(lib_path)
    else:
        result["error"] = "Build succeeded but no shared library found in output"

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_all(force: bool = False) -> dict[str, Any]:
    """
    Attempt to build all emulation libraries.
    Returns the full status dict (also written to build_status.json).
    Never raises.
    """
    cmake = _find_cmake()
    status: dict[str, Any] = {
        "cmake_found": cmake,
        "ts": _ts(),
        "libraries": {},
    }

    if cmake is None:
        status["error"] = "cmake not found on PATH — Tier B unavailable"
        _write_status(status)
        return status

    for name, spec in LIBRARIES.items():
        try:
            lib_status = _build_one(name, spec, cmake, force)
        except Exception as e:
            lib_status = {
                "library": name, "built": False, "skipped": False,
                "lib_path": None, "error": str(e), "ts": _ts(),
            }
        status["libraries"][name] = lib_status

    _write_status(status)
    return status


def _write_status(status: dict[str, Any]) -> None:
    try:
        _STATUS.write_text(json.dumps(status, indent=2))
    except Exception:
        pass  # best-effort


def load_status() -> dict[str, Any]:
    """Load the most recent build status.  Returns empty dict if not built yet."""
    try:
        return json.loads(_STATUS.read_text())
    except Exception:
        return {}


def is_built(library: str) -> bool:
    """Quick check: was `library` successfully compiled?"""
    s = load_status()
    return bool(s.get("libraries", {}).get(library, {}).get("built"))


def lib_path(library: str) -> Path | None:
    """Return Path to compiled shared library, or None."""
    s = load_status()
    p = s.get("libraries", {}).get(library, {}).get("lib_path")
    return Path(p) if p else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    force = "--force" in sys.argv
    print(f"[build_extensions] Attempting Tier B builds (force={force}) …")
    result = build_all(force=force)

    print(f"  cmake: {result.get('cmake_found') or 'NOT FOUND'}")
    for name, lib in result.get("libraries", {}).items():
        state = "OK" if lib.get("built") else ("SKIPPED" if lib.get("skipped") else "FAILED")
        path  = lib.get("lib_path") or ""
        err   = lib.get("error") or ""
        print(f"  {name:15s}: {state:8s}  {path or err}")

    print(f"\n  Status written → {_STATUS}")
