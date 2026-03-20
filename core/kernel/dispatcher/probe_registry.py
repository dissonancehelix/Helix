"""Probe Registry.

Discover and catalog invariant probes from ``labs/experiments/invariants``.
The registry maps canonical probe names to script paths without importing the
modules up front.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from core.paths import EXPERIMENTS_ROOT


class ProbeRecord(NamedTuple):
    name: str
    script_path: Path
    description: str = ""


PROBES_ROOT = EXPERIMENTS_ROOT / "invariants"


def _infer_probe_name(script_path: Path) -> str:
    stem = script_path.stem
    return stem[: -len("_probe")] if stem.endswith("_probe") else stem


def discover_probes(probes_dir: str | Path = PROBES_ROOT) -> dict[str, ProbeRecord]:
    probes_dir = Path(probes_dir)
    registry: dict[str, ProbeRecord] = {}
    if not probes_dir.exists():
        return registry

    skip = {"__init__", "probe_interface", "_example_stub"}
    for script in sorted(probes_dir.glob("*.py")):
        if script.stem in skip or script.stem.startswith("_"):
            continue
        registry[_infer_probe_name(script)] = ProbeRecord(
            name=_infer_probe_name(script),
            script_path=script,
            description=_read_probe_description(script),
        )
    return registry


def _read_probe_description(script_path: Path) -> str:
    try:
        src = script_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    for quote in ('"""', "'''"):
        idx = src.find(quote)
        if idx == -1:
            continue
        end = src.find(quote, idx + 3)
        if end == -1:
            continue
        for line in src[idx + 3 : end].strip().splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[:120]
    return ""


def get_probe(probe_name: str, probes_dir: str | Path = PROBES_ROOT) -> ProbeRecord | None:
    return discover_probes(probes_dir).get(probe_name)


def list_probes(probes_dir: str | Path = PROBES_ROOT) -> None:
    registry = discover_probes(probes_dir)
    if not registry:
        print("[PROBE_REGISTRY] No probes found.")
        return
    print(f"[PROBE_REGISTRY] {len(registry)} probe(s) available:")
    for name, record in sorted(registry.items()):
        desc = f" — {record.description}" if record.description else ""
        print(f"  {name}{desc}")
