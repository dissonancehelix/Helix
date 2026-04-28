import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent

ALLOWED_ROOT = {'helix', 'domains', 'labs', 'apps', 'data', 'DISSONANCE.md', 'WORKSPACE.md', 'AGENT_RULES.md', 'MANIFEST.yaml', 'extract.ps1', 'exec.ps1', 'tree.ps1', 'docsweep.py', 'exec_moves.py', 'exec_moves2.py', 'write_docs.py', '.gitignore', '.gitattributes', '.env', '.claude', '.agents', '.pytest_cache'}
FORBIDDEN_NAMES = {'work', 'workspace', 'out', 'outputs', 'artifacts', 'resources', 'misc', 'scratch', 'temp', 'content', 'generated', 'reports', 'exports', 'builds', 'logs', 'runs', 'figures'}

def check_boundaries():
    violations = []

    # 1. Root check
    for item in ROOT.iterdir():
        if item.name not in ALLOWED_ROOT and not item.name.startswith('.'):
            violations.append(f"Root Violation: {item.name} is not an allowed semantic pillar.")

    # 2. Forbidden names check
    for p in ROOT.rglob('*'):
        if p.name.lower() in FORBIDDEN_NAMES and '.git' not in p.parts:
            if not ('apps' in p.parts or 'labs' in p.parts or 'docs' in p.parts): 
                violations.append(f"Forbidden Bucket: {p.relative_to(ROOT)} uses a generic name outside of local context.")
            
    # 3. Domains check
    if (ROOT / 'domains').exists():
        for domain in (ROOT / 'domains').iterdir():
            if domain.is_dir():
                for sub in domain.iterdir():
                    if sub.is_dir() and sub.name not in {'models', 'indexes', 'maps', 'notes', 'exports', 'scripts', '__pycache__'}:
                        violations.append(f"Domain Violation: {sub.relative_to(ROOT)} is not a valid structured knowledge surface.")

    if violations:
        print("BOUNDARY VALIDATION FAILED:")
        for v in violations:
            print(f" - {v}")
        return False
    else:
        print("Boundary validation passed.")
        return True

if __name__ == "__main__":
    if not check_boundaries():
        sys.exit(1)
