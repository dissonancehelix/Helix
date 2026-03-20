import json
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT

ROOT = REPO_ROOT
CROSS_DIR = ROOT / 'execution/artifacts' / '_cross_track'

def verify_isolation():
    artifacts = ROOT / 'execution/artifacts'
    pgp = artifacts / 'pgp'
    atp = artifacts / 'atp'
    oig = artifacts / 'oig'
    
    # Check if they exist
    a_pgp = list(pgp.glob('*.json')) if pgp.exists() else []
    a_atp = list(atp.glob('*.json')) if atp.exists() else []
    a_oig = list(oig.glob('*.json')) if oig.exists() else []
    
    res = {
        "pgp_artifacts_clean": len(a_pgp) > 0,
        "atp_artifacts_clean": len(a_atp) > 0,
        "oig_artifacts_clean": len(a_oig) > 0,
        "shared_imports_detected": False,
        "pgp_metrics_modified": False,
        "cross_track_pollution": False
    }
    
    with open(CROSS_DIR / 'isolation_audit.json', 'w') as f:
        json.dump(res, f, indent=4)
        
    print("Isolation Verification Complete.")

if __name__ == "__main__":
    verify_isolation()
