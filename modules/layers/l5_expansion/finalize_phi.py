import os
import json
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
KB_ARTIFACTS = ROOT / 'kb' / 'artifacts'
DOCS_DIR = ROOT / 'docs'

KB_ARTIFACTS.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

phi_artifact = {
    "id": "artifact-phi-001",
    "type": "NUMERICAL_ARTIFACT",
    "statement": "The golden ratio frequency boundary collapse observed near 1.625 is a flagged coincidence awaiting numeric operatorization.",
    "assumptions": ["KAM bounds strictly apply to operator thresholds, not discrete schema frequency counts."],
    "falsifiers": ["Operator fields must include numeric ratios with units + extraction method."],
    "status": "DEPRECATED",
    "references": ["phase27_29_orchestrator"],
    "verdict": "NUMERICAL_ARTIFACT",
    "evidence": "bootstrap P(|r-phi|<=0.01), z-score, stratified verdict",
    "failure_reason": "FAILED_NO_NUMERIC_OPERATOR_RATIOS",
    "resurrection_condition": "operator fields must include numeric ratios (e.g., Lyapunov exponents, spectral gaps, KAM tori destruction thresholds) with units + extraction method"
}

with open(KB_ARTIFACTS / 'phi_numerical_artifact.json', 'w') as f:
    json.dump(phi_artifact, f, indent=2)

ontology_md_path = DOCS_DIR / 'ontology.md'
phi_note = "\n\n## Archival Note: The φ (Golden Ratio) Artifact\nφ is not an axis, not a kernel, and not a formal mechanism within the Helix schema. It is a flagged numerical coincidence heavily observed during Phase 27–29 boundary ratio counts. Because it fails to extract numeric ratios directly from operator thresholds, it is officially classified as a `NUMERICAL_ARTIFACT` awaiting structural operationalization. Do not connect it to persistence space kernels.\n"

if ontology_md_path.exists():
    with open(ontology_md_path, 'a') as f:
        f.write(phi_note)
else:
    with open(ontology_md_path, 'w') as f:
        f.write("# Helix Ontology\n" + phi_note)
