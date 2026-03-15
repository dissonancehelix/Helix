import os
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Layer Definition (0 is top, higher can import lower layers or infra)
# Infra must not import layers.
LAYER_MAP = {
    "layers/l0_orchestrator": 0,
    "layers/l1_phenomena": 1,
    "layers/l2_elements": 2,
    "layers/l3_primitives": 3,
    "layers/l4_operators": 4,
    "layers/l5_expansion": 5,
    "infra": 100 # Infra is base
}

def get_layer(path):
    rel = Path(path).relative_to(ROOT).as_posix()
    for lp, lv in LAYER_MAP.items():
        if rel.startswith(lp):
            return lv
    return None

def test_directionality():
    violations = []
    py_files = list(ROOT.rglob('*.py'))
    
    for p in py_files:
        if '.git' in p.parts or 'tests' in p.parts or '__pycache__' in p.parts or '.gemini' in p.parts:
            continue
            
        src_lv = get_layer(p)
        if src_lv is None: continue 
        
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            try: tree = ast.parse(f.read())
            except SyntaxError: continue
                
        for node in ast.walk(tree):
            target = None
            if isinstance(node, ast.Import):
                for alias in node.names: target = alias.name
            elif isinstance(node, ast.ImportFrom):
                target = node.module
                
            if target:
                target_lv = None
                if target.startswith('layers.'):
                    parts = target.split('.')
                    if len(parts) >= 2: target_lv = LAYER_MAP.get(f"layers/{parts[1]}")
                elif target.startswith('infra.'):
                    target_lv = 100
                    
                if target_lv is not None:
                    allowed = False
                    if src_lv == 0: allowed = True # L0 imports all
                    elif src_lv == 1 and target_lv in [2, 100]: allowed = True # L1 -> L2, Infra
                    elif src_lv == 2 and target_lv in [3, 100]: allowed = True # L2 -> L3, Infra
                    elif src_lv == 3 and target_lv == 100: allowed = True # L3 -> Infra only
                    elif src_lv == 4 and target_lv in [3, 100]: allowed = True # L4 -> L3, Infra
                    elif src_lv == 5 and target_lv in [1, 2, 3, 4, 100]: allowed = True # L5 -> L1-L4, Infra
                    elif src_lv == 100 and target_lv == 100: allowed = True # Infra -> Infra
                    
                    if not allowed:
                        violations.append(f"{p.relative_to(ROOT)} (L{src_lv}) imports {target} (L{target_lv})")
    
    if violations:
        print("Layer Directionality Violations Found:")
        for v in violations:
            print(f"  - {v}")
        return False
    
    print("Layer Directionality Check Passed.")
    return True

if __name__ == "__main__":
    if not test_directionality():
        sys.exit(1)
    sys.exit(0)
