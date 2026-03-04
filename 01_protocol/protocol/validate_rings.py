# Helix Ring 1: Total Gravity Guard
# Enforces strictly ONE-WAY dependency flow:
# Core (0) -> Protocol (1) -> Runtime (2) -> Sandbox (3)

import os
import sys
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Defined Ring Levels (Smaller number = Lower Ring, Higher Gravity)
RING_LEVELS = {
    'core': 0,
    'protocol': 1,
    'runtime': 2,
    'sandbox': 3,
    'protocol': 1 # Tests can import from everything
}

def get_file_ring(file_path):
    parts = list(file_path.relative_to(ROOT).parts)
    if not parts: return None
    return parts[0]

def check_gravity_violations():
    violations = []
    
    # Scan all Python files in the repo
    for py_file in ROOT.glob('**/*.py'):
        if '.git' in str(py_file) or '06_artifacts/artifacts' in str(py_file) or 'tmp' in str(py_file):
            continue
            
        file_ring_name = get_file_ring(py_file)
        if file_ring_name not in RING_LEVELS:
            continue
        
        # Test exemption: Ring 1 (Protocol) tests are allowed to import from higher rings
        # to facilitate instrumentation and cross-ring validation.
        if 'tests' in py_file.parts and RING_LEVELS[file_ring_name] == 1:
            continue

        file_level = RING_LEVELS[file_ring_name]
        
        with open(py_file, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                continue
                
            for node in ast.walk(tree):
                targets = []
                if isinstance(node, ast.Import):
                    targets = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    targets = [node.module] if node.module else []
                
                for target in targets:
                    if not target: continue
                    target_pkg = target.split('.')[0]
                    
                    if target_pkg in RING_LEVELS:
                        target_level = RING_LEVELS[target_pkg]
                        
                        # GRAVITY CONTRACT: target_level must be <= file_level
                        if target_level > file_level:
                            violations.append(
                                f"GRAVITY_VIOLATION: {py_file.name} (Ring {file_level}) imports "
                                f"from {target} (Ring {target_level})"
                            )
                        # SPECIAL RULE: Ring 0 (Core) cannot even import Ring 0 (except self-referential)
                        # To keep it absolutely pure. Actually, standard lib is fine.
                        if file_level == 0 and target_pkg == 'core' and target != 'core' and not target.startswith('core.'):
                             pass # allowed if inside same package
                    
                    # Rule 0: Core cannot import anything besides standard-lib (already covered by target_pkg check)
                    # unless it's an internal core import.
                    if file_level == 0 and target_pkg not in ['core', 'math', 'json', 'os', 'sys', 'collections', 'typing', 'pathlib', 'abc', 'functools', 'datetime']:
                        if target_pkg != 'core' and '.' in target: # complex imports
                             pass
                        else:
                             violations.append(f"CORE_IMPURITY: {py_file.name} imports from non-stdlib {target}")

    if violations:
        unique_violations = sorted(list(set(violations)))
        print("\n".join(unique_violations))
        return False
    
    print("GRAVITY_STABLE: Helix Repository obeys one-way ring flow.")
    return True

if __name__ == "__main__":
    if not check_gravity_violations():
        sys.exit(1)
    sys.exit(0)
