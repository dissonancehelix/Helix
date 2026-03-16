"""
Python Experiment Loader
========================
Resolves HIL experiment names to importable Python modules.

Resolution order:
  1. ExperimentRegistry (canonical registry + auto-discovery fallbacks)
  2. Legacy probe registry (engines/python/probes/) — backward compat

All experiment execution must enter through HIL:
  RUN experiment:<name> engine:python

Direct invocation via shell is not a supported path.
"""
from __future__ import annotations

import importlib

from engines.python.experiment_registry import (
    resolve,
    list_experiments,
    ExperimentNotFoundError,
    ExperimentLoadError,
)


class PythonExperimentLoader:
    """
    Loads Python experiment modules by HIL experiment name.
    Primary resolver: ExperimentRegistry.
    Fallback: legacy engines/python/probes/ registry.
    """

    # Legacy probe registry — kept for backward compatibility only.
    # New experiments must be added to experiment_registry.py instead.
    _LEGACY_PROBES: dict[str, str] = {
        "network":      "probes.network",
        "dynamical":    "probes.dynamical",
        "oscillator":   "probes.oscillator",
        "cellular":     "probes.cellular",
        "evolutionary": "probes.evolutionary",
        "information":  "probes.information",
        "dataset":      "probes.dataset",
    }

    @staticmethod
    def load(experiment_name: str):
        """
        Load an experiment module by name.

        Returns the module on success.
        Returns None if not found (caller should check).
        Raises ExperimentLoadError if registered but broken.
        """
        # 1. Primary: ExperimentRegistry (canonical + auto-discovery)
        module_path, module = resolve(experiment_name)
        if module is not None:
            return module

        # 2. Legacy: engines/python/probes/ (keyword matching)
        probe_key = experiment_name.split(".")[-1] if "." in experiment_name else experiment_name
        for key, path in PythonExperimentLoader._LEGACY_PROBES.items():
            if key in probe_key:
                try:
                    return importlib.import_module(f"engines.python.{path}")
                except ImportError:
                    pass

        return None

    @staticmethod
    def load_strict(experiment_name: str):
        """
        Load an experiment module, raising ExperimentNotFoundError if not found.
        Use this in the execution path to surface clear HIL guidance.
        """
        module = PythonExperimentLoader.load(experiment_name)
        if module is None:
            raise ExperimentNotFoundError(experiment_name)
        return module

    @staticmethod
    def list_available() -> list[str]:
        """Return all registered experiment names."""
        return list_experiments()
