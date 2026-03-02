import json
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACTS_DIR = ROOT / 'artifacts'
DOCS_DIR = ROOT / 'docs'

def execute():
    ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)
    DOCS_DIR.mkdir(exist_ok=True, parents=True)

    registry = {
        "kernels": [
            {
                "id": "KERNEL-1",
                "name": "Substrate & Ontology Base",
                "status": "FROZEN_CORE",
                "axes": ["Substrate S1c", "Persistence Ontology"]
            },
            {
                "id": "KERNEL-2",
                "name": "Expression Topology",
                "status": "MATURING",
                "axes": ["Branching", "Recombination", "Slack Reserve"]
            }
        ],
        "modules": [
            {
                "id": "MODULE-EIP",
                "name": "Epistemic Irreversibility",
                "status": "ARCHIVED_SPARSE",
                "reason": "Collapsed into memory trace sub-component. Not orthogonal to K1."
            },
            {
                "id": "MODULE-TSM",
                "name": "Trajectory Stabilization Mechanism (Identity)",
                "status": "INDEPENDENT_PARALLEL",
                "axes": ["Memory", "Control", "Commitment"]
            }
        ]
    }

    with open(ARTIFACTS_DIR / 'kernel_registry.json', 'w') as f:
        json.dump(registry, f, indent=2)

    docs_content = """# Helix Kernel Registry

## Core Kernels (Dimensionally Orthogonal)

**KERNEL-1: Substrate & Ontology**
*Status: FROZEN CORE*
Defines the base coordinate space of physical/computational limits.

**KERNEL-2: Expression**
*Status: MATURING*
Defines the internal topological routing, slack, and combinatorial grammar of a system.
Mathematically proven independent of KERNEL-1.

## Modules (Archived or Parallel)

**MODULE-EIP (Archived)**: Epistemic Irreversibility. Shattered into sub-components, primarily 'Memory'.
**MODULE-TSM (Parallel)**: Identity/Persistence Atlas. Operates purely on regime stability (PERSISTS vs SHATTERS). Does not warp macro collapse geometry.
"""
    with open(DOCS_DIR / 'kernels.md', 'w') as f:
        f.write(docs_content)

if __name__ == "__main__":
    execute()
