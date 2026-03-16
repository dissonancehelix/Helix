"""
Experiment Registry
===================
Canonical mapping of HIL experiment names to their Python module paths.

This is the authoritative resolver for:
  RUN experiment:<name> engine:python

Adding a new experiment to Helix requires an entry here.
No experiment may be executed by constructing a direct shell command.

Resolution order:
  1. REGISTRY lookup (exact match)
  2. Auto-discover from labs/ subdirectories (name_probe, experiment, run)
  3. Fail with a structured error listing valid experiment names
"""
from __future__ import annotations

import importlib
from pathlib import Path

# ── Canonical experiment registry ─────────────────────────────────────────────
# Format: "hil_experiment_name": "python.module.path"
# The HIL name is what appears in: RUN experiment:<hil_name>

REGISTRY: dict[str, str] = {
    # ── Invariant probes (labs/invariants/) ───────────────────────────────────
    "epistemic_irreversibility":        "labs.invariants.epistemic_irreversibility_probe",
    "decision_compression":             "labs.invariants.decision_compression_probe",
    "oscillator_locking":               "labs.invariants.oscillator_locking_probe",
    "local_incompleteness":             "labs.invariants.local_incompleteness_probe",
    "regime_transition":                "labs.invariants.regime_transition_probe",

    # ── Network / dynamics (labs/network_consensus/, labs/oscillator_sync/) ───
    "network_consensus":                "labs.network_consensus.experiment",
    "oscillator_sync":                  "labs.oscillator_sync.experiment",

    # ── Simulation experiments (labs/simulation/) ─────────────────────────────
    "decision_compression_suite":       "labs.simulation.experiments.dcp_decision_compression_suite",
    "megatest":                         "labs.simulation.megatest.phase_megatest",
    "cross_domain_compression":         "labs.simulation.cross_domain_compression.phase_cdc",
    "regime_superposition":             "labs.simulation.regime_superposition.phase_regime_superposition",
    "memory_regimes":                   "labs.simulation.memory_regimes.phase_memory",
    "riim":                             "labs.simulation.riim.phase_riim",
    "discovery_engine":                 "labs.simulation.discovery_engine.phase_discovery_engine",
    "pgp_decision":                     "labs.simulation.pgp_decision.phase_dec_pgp",
    "pgp_adapt":                        "labs.simulation.pgp_adapt.phase_adapt_multi_pgp",
}

# ── Auto-discovery fallback patterns ──────────────────────────────────────────
# Tried in order when exact registry lookup fails.
_FALLBACK_PATTERNS: list[str] = [
    "labs.invariants.{name}_probe",
    "labs.{name}.experiment",
    "labs.simulation.{name}",
    "labs.simulation.{name}.phase_{name}",
    "labs.cognition.{name}",
    "labs.creativity.{name}",
]


def resolve(experiment_name: str) -> tuple[str, object] | tuple[None, None]:
    """
    Resolve an experiment name to (module_path, module).

    Returns (module_path, module) on success, (None, None) on failure.
    """
    # 1. Exact registry match
    if experiment_name in REGISTRY:
        module_path = REGISTRY[experiment_name]
        try:
            return module_path, importlib.import_module(module_path)
        except ImportError as e:
            raise ExperimentLoadError(
                f"Experiment '{experiment_name}' is registered at '{module_path}' "
                f"but failed to import: {e}"
            )

    # 2. Auto-discover via fallback patterns
    for pattern in _FALLBACK_PATTERNS:
        module_path = pattern.format(name=experiment_name)
        try:
            return module_path, importlib.import_module(module_path)
        except ImportError:
            continue

    return None, None


def list_experiments() -> list[str]:
    """Return sorted list of all registered experiment names."""
    return sorted(REGISTRY.keys())


class ExperimentLoadError(RuntimeError):
    """Raised when a registered experiment cannot be imported."""
    pass


class ExperimentNotFoundError(RuntimeError):
    """Raised when an experiment name cannot be resolved."""

    def __init__(self, name: str):
        valid = ", ".join(list_experiments())
        super().__init__(
            f"Experiment '{name}' not found in registry or labs/.\n"
            f"Use: RUN experiment:<name> engine:python\n"
            f"Registered experiments: {valid}"
        )
        self.experiment_name = name
