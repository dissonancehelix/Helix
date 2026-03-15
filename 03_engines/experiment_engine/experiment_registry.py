"""
Experiment Registry — 03_engines/experiment_engine/experiment_registry.py
"""
import os
import yaml
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())

def list_experiments():
    exp_dir = ROOT / "04_labs" / "experiments"
    experiments = []
    if exp_dir.exists():
        for f in exp_dir.glob("*.yaml"):
            experiments.append(f.stem)
    return experiments

def get_experiment_summary(exp_name):
    exp_dir = ROOT / "07_artifacts" / "experiments" / exp_name
    summary_file = exp_dir / "summary.json"
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            return f.read()
    return f"No summary found for {exp_name}"
