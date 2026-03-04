import json
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ENUM_PATH = ROOT / 'core/enums/eip_obstruction_enum.json'
EIP_PATH = ROOT / '06_artifacts/artifacts/eip/eip_overlay.json'

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
