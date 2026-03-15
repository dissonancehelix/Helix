"""
Experiment Manifest — 03_engines/experiment_engine/experiment_manifest.py
"""
import yaml
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())

def validate_experiment_manifest(exp_name):
    path = ROOT / "04_labs" / "experiments" / f"{exp_name}.yaml"
    if not path.exists():
        return False
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
        return "probes" in data and "labs" in data and "parameters" in data
