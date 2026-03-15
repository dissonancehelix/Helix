import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
ENUM_PATH = ROOT / 'core/enums/eip_obstruction_enum.json'
EIP_PATH = ROOT / '07_artifacts/artifacts/eip/eip_overlay.json'

def test_obstruction_vocab():
    with open(ENUM_PATH, 'r') as f:
        enum_list = json.load(f)
        
    with open(EIP_PATH, 'r') as f:
        eip_wrapper = json.load(f)
    
    details = eip_wrapper.get("data", {}).get("detail", [])
    
    for d in details:
        if d.get("eip_status") == "UNDEFINED":
            obs = d.get("eip_obstruction")
            assert obs in enum_list, f"Obstruction '{obs}' not in allowed EIP vocabulary!"
                
    print("test_eip_obstruction_enum: PASS")

if __name__ == "__main__":
    test_obstruction_vocab()
