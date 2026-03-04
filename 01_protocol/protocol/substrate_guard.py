import os
import json
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def check_substrate(strict_mode=False):
    """
    Ensures that experimental layers (03_forge, 04_workspaces) 
    do not write back into the immutable substrate (00_core, 01_protocol, 02_runtime).
    """
    artifacts_dir = ROOT / '06_artifacts' / 'artifacts'
    log_path = artifacts_dir / 'substrate_violation_log.json'
    
    immutable_dirs = ['00_core', '01_protocol', '02_runtime']
    test_dirs = ['03_forge', '04_workspaces']
    
    violations = []
    
    for test_dir in test_dirs:
        layer_path = ROOT / test_dir
        if not layer_path.exists():
            continue
            
        for root_dir, dirs, files in os.walk(layer_path):
            if '__pycache__' in root_dir or '.git' in root_dir:
                continue
                
            py_files = [f for f in files if f.endswith('.py')]
            for pyf in py_files:
                try:
                    with open(Path(root_dir) / pyf, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                        
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'open':
                            if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                                val = str(node.args[0].value)
                                for imm in immutable_dirs:
                                    if imm in val:
                                        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and 'w' in str(node.args[1].value):
                                            violations.append({
                                                "file": f"{Path(root_dir).relative_to(ROOT)}/{pyf}",
                                                "target": val,
                                                "mode": str(node.args[1].value)
                                            })
                except Exception:
                    pass
                    
    if violations:
        print("[SUBSTRATE GUARD] Detected illegal upward write vectors!")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        # load existing logs if any
        log_entries = []
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    log_entries = json.load(f)
            except Exception:
                pass
                
        log_entries.extend(violations)
        try:
            with open(log_path, 'w') as f:
                json.dump(log_entries, f, indent=4)
        except Exception:
            pass
            
        if strict_mode:
            print("  STRICT MODE ERROR: Substrate mutation attempt blocks execution.")
            import sys
            sys.exit(1)
            
        return False
        
    return True

if __name__ == '__main__':
    check_substrate()
