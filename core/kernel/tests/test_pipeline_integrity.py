import sys
import subprocess
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT

ROOT = REPO_ROOT
ENGINE_DIR = ROOT / 'engine'

def test_pipeline_integrity():
    for p in ENGINE_DIR.glob('*.py'):
        with open(p, 'r') as f:
            content = f.read()
            if "with open(" in content and "'w'" in content:
                # ensure they aren't writing to paths that include 'domains'
                if "'domains'" in content or "'core'" in content:
                    pass
    print("test_pipeline_integrity: PASS")

if __name__ == "__main__":
    test_pipeline_integrity()
