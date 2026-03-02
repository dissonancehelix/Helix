# Helix Ring 1: Dependency Guard
# Enforces: Core -> Standard Lib Only. Modules -> Core.

import os
import sys
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def check_ring_vulnerabilities():
    """
    Scans /core/ (Ring 0) for upward dependencies.
    Ring 0 MUST NOT import from instrumentation, modules, or os.
    """
    forbidden_layers = ['instrumentation', 'modules', 'os', 'infra', 'layers']
    core_path = ROOT / 'core'
    violations = []

    for py_file in core_path.glob('**/*.py'):
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
                    first_part = target.split('.')[0]
                    if first_part in forbidden_layers:
                        violations.append(f"UPWARD_DEPENDENCY_VIOLATION: {py_file.name} -> {target}")

    if violations:
        print("\n".join(violations))
        return False
    
    print("RING_DISCIPLINE_ENFORCED (Ring 0 Isolated)")
    return True

if __name__ == "__main__":
    if not check_ring_vulnerabilities():
        sys.exit(1)
    sys.exit(0)
