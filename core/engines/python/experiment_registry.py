"""
Experiment Registry
===================
Canonical mapping of HIL experiment names to their Python module paths,
plus automatic discovery of any file under labs/**/experiments/*.py.

This is the authoritative resolver for:
  RUN experiment:<name> engine:python

Resolution order:
  1. REGISTRY lookup   — explicit, pinned entries
  2. Auto-discovery    — scans labs/**/experiments/*.py at import time
  3. Fallback patterns — legacy path guessing
  4. Fail with structured error listing all known experiments

Adding a new experiment:
  Drop a Python file with a run() function into any
  labs/**/experiments/ directory. It will be discovered automatically.
  No manual registration required.

No experiment may be executed by constructing a direct shell command.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

_LABS_ROOT = Path(__file__).resolve().parents[2] / "labs"

# ── Explicit registry ──────────────────────────────────────────────────────────
# Pinned entries for experiments that live outside labs/**/experiments/
# or that need a non-default HIL name.

REGISTRY: dict[str, str] = {
    # ── Invariant probes ──────────────────────────────────────────────────────
    "epistemic_irreversibility": "labs.invariants.epistemic_irreversibility_probe",
    "decision_compression":      "labs.invariants.decision_compression_probe",
    "oscillator_locking":        "labs.invariants.oscillator_locking_probe",
    "local_incompleteness":      "labs.invariants.local_incompleteness_probe",
    "regime_transition":         "labs.invariants.regime_transition_probe",

    # ── Systems ───────────────────────────────────────────────────────────────
    "network_consensus":         "labs.systems.network_consensus.experiment",
    "oscillator_sync":           "labs.systems.oscillator_sync.experiment",

    # ── Simulation ────────────────────────────────────────────────────────────
    "decision_compression_suite": "labs.systems.simulation.experiments.dcp_decision_compression_suite",
    "megatest":                   "labs.systems.simulation.megatest.phase_megatest",
    "cross_domain_compression":   "labs.systems.simulation.cross_domain_compression.phase_cdc",
    "regime_superposition":       "labs.systems.simulation.regime_superposition.phase_regime_superposition",
    "memory_regimes":             "labs.systems.simulation.memory_regimes.phase_memory",
    "riim":                       "labs.systems.simulation.riim.phase_riim",
    "discovery_engine":           "labs.systems.simulation.discovery_engine.phase_discovery_engine",
    "pgp_decision":               "labs.systems.simulation.pgp_decision.phase_dec_pgp",
    "pgp_adapt":                  "labs.systems.simulation.pgp_adapt.phase_adapt_multi_pgp",

    # ── Music Lab ─────────────────────────────────────────────────────────────
    "music_ingestion":            "domains.music.experiments.music_ingestion",
    "music_symbolic_analysis":    "domains.music.experiments.music_symbolic_analysis",
    "music_mir_analysis":         "domains.music.experiments.music_mir_analysis",
    "music_chip_analysis":        "domains.music.experiments.music_chip_analysis",
    "composer_style_space":       "domains.music.experiments.composer_style_space",
    "composer_similarity_graph":  "domains.music.experiments.composer_similarity_graph",
    "motif_network_analysis":     "domains.music.experiments.motif_network_analysis",
    "composer_attribution":       "domains.music.experiments.composer_attribution",
    "s3k_analysis":               "domains.music.experiments.s3k_analysis",
    "soundtrack_analysis":        "domains.music.experiments.soundtrack_analysis",
    "filesystem_scan":            "domains.music.experiments.filesystem_scan",
    "music_library_index":        "domains.music.experiments.music_library_index",
    "music_library_ingestion":    "domains.music.experiments.music_library_ingestion",
    "composer_training_sets":     "domains.music.experiments.composer_training_sets",
    "composer_style_vectors":     "domains.music.experiments.composer_style_vectors",
}

# ── Auto-discovery ─────────────────────────────────────────────────────────────
# Scans labs/**/experiments/*.py at import time.
# File stem becomes the HIL experiment name.
# Discovered entries are added to REGISTRY (explicit entries take priority).

def _discover() -> dict[str, str]:
    """
    Walk labs/**/experiments/*.py and return {stem: dotted_module_path}.
    Converts file path to module path relative to the repo root.
    """
    discovered: dict[str, str] = {}
    if not _LABS_ROOT.exists():
        return discovered
    for exp_file in sorted(_LABS_ROOT.rglob("experiments/*.py")):
        if exp_file.name.startswith("_"):
            continue
        stem = exp_file.stem  # e.g. "comprehension_probe"
        # Build dotted path: relative to repo root (parent of labs/)
        repo_root = _LABS_ROOT.parent
        try:
            rel = exp_file.relative_to(repo_root)
        except ValueError:
            continue
        module_path = ".".join(rel.with_suffix("").parts)  # e.g. "labs.cognition.language.experiments.comprehension_probe"
        discovered[stem] = module_path
    return discovered


_DISCOVERED: dict[str, str] = _discover()

# Merge: explicit REGISTRY takes priority over discovered entries
_FULL_REGISTRY: dict[str, str] = {**_DISCOVERED, **REGISTRY}

# ── Fallback patterns ──────────────────────────────────────────────────────────
# Tried only when both REGISTRY and discovery fail.

_FALLBACK_PATTERNS: list[str] = [
    "labs.invariants.{name}_probe",
    "labs.systems.{name}.experiment",
    "labs.systems.simulation.{name}",
    "labs.systems.simulation.{name}.phase_{name}",
    "labs.cognition.{name}",
    "labs.cognition.language.experiments.{name}",
]


# ── Public API ─────────────────────────────────────────────────────────────────

def resolve(experiment_name: str) -> tuple[str, object] | tuple[None, None]:
    """
    Resolve an experiment name to (module_path, module).
    Returns (module_path, module) on success, (None, None) on failure.
    Raises ExperimentLoadError if registered but broken.
    """
    # 1. Full registry (explicit + discovered)
    if experiment_name in _FULL_REGISTRY:
        module_path = _FULL_REGISTRY[experiment_name]
        try:
            return module_path, importlib.import_module(module_path)
        except ImportError as e:
            raise ExperimentLoadError(
                f"Experiment '{experiment_name}' registered at '{module_path}' "
                f"but failed to import: {e}"
            )

    # 2. Fallback pattern guessing
    for pattern in _FALLBACK_PATTERNS:
        module_path = pattern.format(name=experiment_name)
        try:
            return module_path, importlib.import_module(module_path)
        except ImportError:
            continue

    return None, None


def list_experiments() -> list[str]:
    """Return sorted list of all known experiment names (explicit + discovered)."""
    return sorted(_FULL_REGISTRY.keys())


def registry_source(name: str) -> str:
    """Return 'explicit', 'discovered', or 'unknown' for an experiment name."""
    if name in REGISTRY:
        return "explicit"
    if name in _DISCOVERED:
        return "discovered"
    return "unknown"


# ── Exceptions ─────────────────────────────────────────────────────────────────

class ExperimentLoadError(RuntimeError):
    """Raised when a registered experiment cannot be imported."""
    pass


class ExperimentNotFoundError(RuntimeError):
    """Raised when an experiment name cannot be resolved."""

    def __init__(self, name: str):
        all_known = list_experiments()
        super().__init__(
            f"Experiment '{name}' not found.\n"
            f"Use: RUN experiment:<name> engine:python\n"
            f"Known experiments ({len(all_known)}): {', '.join(all_known)}"
        )
        self.experiment_name = name
