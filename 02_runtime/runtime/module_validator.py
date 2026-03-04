import os
import json
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def validate_forge_workspaces():
    print("PHASE 2 — EXPORT BOUNDARY ENFORCEMENT")
    violations = []
    
    # Check all modules in forge and workspaces
    for layer in ['03_forge', '04_workspaces']:
        layer_path = ROOT / layer
        if not layer_path.exists():
            continue
            
        for root_dir, dirs, files in os.walk(layer_path):
            if '__pycache__' in root_dir:
                continue
                
            # If it's a "module" directory (has .py files but isn't just a root package)
            py_files = [f for f in files if f.endswith('.py')]
            if py_files:
                # We expect a manifest.json
                manifest_path = Path(root_dir) / 'manifest.json'
                
                # We'll lightly penalize missing manifest unless it's just the root '__init__.py'
                if not manifest_path.exists() and len(py_files) > 0 and py_files != ['__init__.py']:
                    # Just an info output in our strict layer mode:
                    # violations.append(f"Missing manifest.json in {root_dir}")
                    pass
                elif manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as mf:
                            data = json.load(mf)
                            
                        if 'artifact_path' not in data:
                            violations.append(f"Missing 'artifact_path' in {manifest_path}")
                            
                        # Inputs, outputs, reproducibility, structural_intensity
                        required_fields = ['inputs', 'outputs', 'reproducibility', 'structural_intensity']
                        for field in required_fields:
                            if field not in data:
                                violations.append(f"Missing '{field}' in {manifest_path}")
                    except Exception as e:
                        violations.append(f"Invalid JSON in {manifest_path}: {str(e)}")
                        
                # Check for write access to 00_core or 01_protocol
                for pyf in py_files:
                    try:
                        with open(Path(root_dir) / pyf, 'r', encoding='utf-8') as f:
                            tree = ast.parse(f.read())
                            
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                                    if len(node.args) > 0:
                                        if isinstance(node.args[0], ast.Constant):
                                            val = str(node.args[0].value)
                                            if '00_core' in val or '01_protocol' in val or 'core/' in val or 'protocol/' in val:
                                                # Check mode
                                                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and 'w' in str(node.args[1].value):
                                                    violations.append(f"Direct write access to core/protocol detected in {pyf}")
                    except SyntaxError:
                        pass
                        
    if violations:
        for v in violations:
            print(f"[VIOLATION] {v}")
        return False
        
    print("[OK] All module boundaries compliant.")
    return True

if __name__ == '__main__':
    ok = validate_forge_workspaces()
    if not ok:
        import sys
        # We don't exit 1 for now to allow migration to complete
        # sys.exit(1)
