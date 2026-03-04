import sys
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYERS_DIR = ROOT / 'layers'

def test_no_hashing():
    violations = []
    py_files = list(LAYERS_DIR.rglob('*.py'))
    
    for p in py_files:
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                continue
                
        for node in ast.walk(tree):
            # Check for import hashlib
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                target = ""
                if isinstance(node, ast.Import):
                    for alias in node.names: target = alias.name
                else:
                    target = node.module or ""
                
                if 'hashlib' in target:
                    violations.append(f"{p.relative_to(ROOT)} imports hashlib directly.")
                    
            # Check for .hexdigest() calls (generic heuristic)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'hexdigest':
                        violations.append(f"{p.relative_to(ROOT)} calls .hexdigest() directly.")
    
    if violations:
        print("Infrastructure Leaks (Hashing) Detected in Layers:")
        for v in violations:
            print(f"  - {v}")
        return False
        
    print("Infrastructure Isolation (Hashing) Check Passed.")
    return True

if __name__ == "__main__":
    if not test_no_hashing():
        sys.exit(1)
    sys.exit(0)
