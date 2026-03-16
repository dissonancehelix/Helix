"""
Helix Music Lab — Tool Cloner
==============================
Clones external VGM/chip tool repositories into:
  labs/music_lab/tools/runtime/   — algorithmic modules used at analysis time
  labs/music_lab/tools/emulation/ — C libraries for Tier B emulation

Post-clone: strips GUI code, build artifacts, CI config, test suites,
and editor components.  Keeps only source files needed for decoding,
synthesis parameter extraction, MIDI conversion, and music analysis.

Usage:
    python labs/music_lab/tools/clone_tools.py [--dry-run] [--only <name>]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
LAB  = Path(__file__).parent.parent
TOOLS_RT  = LAB / "tools" / "runtime"
TOOLS_EMU = LAB / "tools" / "emulation"
TOOLS_REF = LAB / "tools" / "reference"

# ---------------------------------------------------------------------------
# Repository registry
# ---------------------------------------------------------------------------

REPOS = [
    # (name, url, dest_dir, strip_extras)
    # --- runtime algorithmic tools ---
    {
        "name":  "vgm2x",
        "url":   "https://github.com/vampirefrog/vgm2x",
        "dest":  TOOLS_RT / "vgm2x",
        "strip": ["test", "tests", ".github", "examples"],
    },
    {
        "name":  "vgmio",
        "url":   "https://github.com/vampirefrog/vgmio",
        "dest":  TOOLS_RT / "vgmio",
        "strip": ["test", "tests", ".github", "examples"],
    },
    {
        "name":  "libfmvoice",
        "url":   "https://github.com/vampirefrog/libfmvoice",
        "dest":  TOOLS_RT / "libfmvoice",
        "strip": ["test", "tests", ".github", "examples"],
    },
    {
        "name":  "fmtoy",
        "url":   "https://github.com/vampirefrog/fmtoy",
        "dest":  TOOLS_RT / "fmtoy",
        "strip": ["test", "tests", ".github", "gui", "editor", "ui"],
    },
    {
        "name":  "fm2x",
        "url":   "https://github.com/vampirefrog/fm2x",
        "dest":  TOOLS_RT / "fm2x",
        "strip": ["test", "tests", ".github"],
    },
    {
        "name":  "midilib",
        "url":   "https://github.com/vampirefrog/midilib",
        "dest":  TOOLS_RT / "midilib",
        "strip": ["test", "tests", ".github", "examples"],
    },
    {
        "name":  "mml2smf",
        "url":   "https://github.com/vampirefrog/mml2smf",
        "dest":  TOOLS_RT / "mml2smf",
        "strip": ["test", "tests", ".github"],
    },
    {
        "name":  "ym2608",
        "url":   "https://github.com/mtrberzi/ym2608",
        "dest":  TOOLS_RT / "ym2608",
        "strip": ["test", "tests", ".github"],
    },
    # --- emulation C libraries ---
    {
        "name":  "libvgm",
        "url":   "https://github.com/ValleyBell/libvgm",
        "dest":  TOOLS_EMU / "libvgm",
        "strip": ["player", "emu/cores/panning", ".github", "test", "tests",
                  "utils/DataLoader_File"],
    },
    {
        "name":  "vgmstream",
        "url":   "https://github.com/vgmstream/vgmstream",
        "dest":  TOOLS_EMU / "vgmstream",
        "strip": ["cli", "fb2k", "winamp", "xmplay", "audacious",
                  "winxp", "cmake", ".github", "test", "fuzzing",
                  "ext_libs", "doc"],
    },
]

# Dirs to always strip regardless of repo-specific list
ALWAYS_STRIP = {
    ".github", ".circleci", ".travis.yml", "appveyor.yml",
    "CMakeFiles", "build", "_build", "Release", "Debug",
    "installer", "setup", "packaging", "deploy",
    "gui", "GUI", "Gui", "editor", "Editor",
    "qt", "Qt", "wx", "win32", "Win32",
    "android", "ios", "osx", "macos",
    "doxygen", "Doxyfile",
}

# File patterns to always delete after clone
ALWAYS_DELETE_EXTS = {".exe", ".dll", ".so", ".dylib", ".lib", ".a",
                      ".o", ".obj", ".pdb", ".ilk", ".exp",
                      ".zip", ".tar.gz", ".7z", ".rar"}


def _run(cmd: list[str], cwd: Path | None = None) -> bool:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    STDERR: {result.stderr[:200]}")
    return result.returncode == 0


def _strip(dest: Path, extra: list[str], dry_run: bool) -> int:
    removed = 0
    strip_names = ALWAYS_STRIP | set(extra)

    for item in list(dest.rglob("*")):
        # Remove blacklisted dirs
        if item.is_dir() and item.name in strip_names:
            if not dry_run:
                shutil.rmtree(item, ignore_errors=True)
            print(f"    strip dir  {item.relative_to(dest)}")
            removed += 1
            continue
        # Remove binary/build artifacts
        if item.is_file() and item.suffix.lower() in ALWAYS_DELETE_EXTS:
            if not dry_run:
                item.unlink(missing_ok=True)
            print(f"    strip file {item.relative_to(dest)}")
            removed += 1

    return removed


def clone_repo(entry: dict, dry_run: bool = False) -> bool:
    name = entry["name"]
    url  = entry["url"]
    dest = entry["dest"]
    strip_extra = entry.get("strip", [])

    if dest.exists():
        print(f"  [SKIP] {name} — already cloned at {dest}")
        return True

    print(f"  [CLONE] {name}")
    print(f"          {url} → {dest}")

    if dry_run:
        print(f"          (dry-run: skipping git clone)")
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    ok = _run(["git", "clone", "--depth=1", url, str(dest)])
    if not ok:
        print(f"  [FAIL] git clone failed for {name}")
        return False

    removed = _strip(dest, strip_extra, dry_run)
    print(f"  [OK]   {name} — stripped {removed} items")
    return True


def write_reference_readme() -> None:
    TOOLS_REF.mkdir(parents=True, exist_ok=True)
    readme = TOOLS_REF / "README.md"
    if readme.exists():
        return
    readme.write_text("""\
# Reference Tools

These repositories are checked out in `runtime/deps/helix_sources/sound_drivers/`
and serve as **source study material only** — chip behavior documentation,
register maps, format specs, and driver internals.

They are never imported at runtime.

| Repo | Location | Purpose |
|------|----------|---------|
| furnace | `runtime/deps/helix_sources/sound_drivers/furnace/` | Multi-chip tracker — chip emulation reference |
| mame | `runtime/deps/helix_sources/sound_drivers/mame/` | YM2612, SN76489, SPC700 cores |
| Dn-FamiTracker | `runtime/deps/helix_sources/sound_drivers/Dn-FamiTracker/` | NES APU reference |
| AddmusicK | `runtime/deps/helix_sources/sound_drivers/AddmusicK/` | SNES N-SPC engine reference |
| Echo | `runtime/deps/helix_sources/sound_drivers/Echo/` | Genesis SMPS-class driver |
| SMPSPlay | `runtime/deps/helix_sources/sound_drivers/SMPSPlay/` | SMPS format player |
| s2-sound-driver-plus | `runtime/deps/helix_sources/sound_drivers/s2-sound-driver-plus/` | Sonic 2 driver reference |
| MidiConverters | `runtime/deps/helix_sources/sound_drivers/MidiConverters/` | Format → MIDI conversion reference |
| ExtractorsDecoders | `runtime/deps/helix_sources/sound_drivers/ExtractorsDecoders/` | Proprietary format decoders |
| libADLMIDI | `runtime/deps/helix_sources/sound_drivers/libADLMIDI/` | OPL FM synthesis reference |
""")


def run(dry_run: bool = False, only: str | None = None) -> None:
    print(f"\nHelix Music Lab — Tool Cloner")
    print(f"  runtime → {TOOLS_RT}")
    print(f"  emulation → {TOOLS_EMU}")
    print(f"  dry_run = {dry_run}\n")

    repos = REPOS if not only else [r for r in REPOS if r["name"] == only]
    if only and not repos:
        print(f"Unknown repo: {only}")
        sys.exit(1)

    results = {}
    for entry in repos:
        ok = clone_repo(entry, dry_run=dry_run)
        results[entry["name"]] = "ok" if ok else "failed"

    write_reference_readme()

    print(f"\nResults:")
    for name, status in results.items():
        mark = "✓" if status == "ok" else "✗"
        print(f"  {mark}  {name}: {status}")

    failed = [k for k, v in results.items() if v == "failed"]
    if failed:
        print(f"\nFailed: {failed}")
        sys.exit(1)
    else:
        print(f"\nAll {len(results)} repos ready.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", default=None, help="Clone only one repo by name")
    args = p.parse_args()
    run(dry_run=args.dry_run, only=args.only)
