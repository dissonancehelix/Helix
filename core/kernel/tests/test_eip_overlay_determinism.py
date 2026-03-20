import json
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT
import sys

ROOT = REPO_ROOT
ARTIFACTS_DIR = ROOT / 'execution/artifacts'

def test_eip_determinism():
    eip_file = ARTIFACTS_DIR / 'eip' / 'eip_overlay.json'
    assert eip_file.exists(), "EIP overlay missing"
    
    with open(eip_file, 'r') as f:
        data = json.load(f).get("data", {})
        
    # Test deterministic properties: check if summary matches details
    summary = data.get("summary", {})
    details = data.get("detail", [])
    
    assert summary.get("total") == len(details), "Count mismatch"
    assert summary.get("defined") == sum(1 for d in details if d["eip_status"] == "DEFINED")
    assert summary.get("irreversible") == sum(1 for d in details if d["eip_class"] == "IRREVERSIBLE")
    
    # Check that basis rules held
    for d in details:
        if d["eip_class"] == "IRREVERSIBLE" and d["eip_status"] == "DEFINED":
            assert d["eip_basis"] in ["COMMITMENT_LATCH", "EXTERNAL_LOCK", "OPERATOR_CLASS_CHANGE", "REACHABLE_SET_COLLAPSE"]
            
    print("test_eip_overlay_determinism: PASS")

if __name__ == "__main__":
    test_eip_determinism()
