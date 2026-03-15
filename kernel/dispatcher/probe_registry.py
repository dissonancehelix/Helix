"""
Probe Registry — 03_engines/orchestrator/probe_registry.py

Discover and catalog probe instruments from 04_labs/probes/.

Probes are Python scripts in 04_labs/probes/ that:
  - Define a class inheriting from HelixProbe (from probe_interface.py)
  - Implement a standalone __main__ block for subprocess execution
  - Are named <probe_name>_probe.py or <probe_name>.py

The registry maps probe names to script paths without importing the probes
(import happens only at run time, inside the sandbox subprocess).
"""

from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from typing import NamedTuple


class ProbeRecord(NamedTuple):
    name: str
    script_path: Path
    description: str = ""


def _infer_probe_name(script_path: Path) -> str:
    """
    Derive a canonical probe name from a filename.

    decision_compression_probe.py → decision_compression
    phi_scan_probe.py             → phi_scan
    my_probe.py                   → my (if ends with _probe, strip suffix)
    other_script.py               → other_script
    """
    stem = script_path.stem
    if stem.endswith("_probe"):
        return stem[: -len("_probe")]
    return stem


def discover_probes(probes_dir: str | Path) -> dict[str, ProbeRecord]:
    """
    Scan a probes directory and return a registry of available probes.

    Ignores __init__.py, probe_interface.py, and files starting with _.

    Args:
        probes_dir: Path to 04_labs/probes/

    Returns:
        dict mapping probe_name → ProbeRecord
    """
    probes_dir = Path(probes_dir)
    registry: dict[str, ProbeRecord] = {}

    if not probes_dir.exists():
        return registry

    SKIP = {"__init__", "probe_interface", "_example_stub"}

    for script in sorted(probes_dir.glob("*.py")):
        if script.stem in SKIP or script.stem.startswith("_"):
            continue

        name = _infer_probe_name(script)
        description = _read_probe_description(script)
        registry[name] = ProbeRecord(
            name=name,
            script_path=script,
            description=description,
        )

    return registry


def _read_probe_description(script_path: Path) -> str:
    """
    Extract a one-line description from a probe script's module docstring
    without fully importing it. Reads only the first non-empty docstring line.
    """
    try:
        src = script_path.read_text(encoding="utf-8", errors="ignore")
        for quote in ('"""', "'''"):
            idx = src.find(quote)
            if idx != -1:
                end = src.find(quote, idx + 3)
                if end != -1:
                    docstring = src[idx + 3 : end].strip()
                    for line in docstring.splitlines():
                        stripped = line.strip()
                        if stripped:
                            return stripped[:120]
    except OSError:
        pass
    return ""


def get_probe(probe_name: str, probes_dir: str | Path) -> ProbeRecord | None:
    """Look up a single probe by name."""
    registry = discover_probes(probes_dir)
    return registry.get(probe_name)


def list_probes(probes_dir: str | Path) -> None:
    """Print a formatted list of available probes."""
    registry = discover_probes(probes_dir)
    if not registry:
        print("[PROBE_REGISTRY] No probes found.")
        return
    print(f"[PROBE_REGISTRY] {len(registry)} probe(s) available:")
    for name, record in sorted(registry.items()):
        desc = f" — {record.description}" if record.description else ""
        print(f"  {name}{desc}")
