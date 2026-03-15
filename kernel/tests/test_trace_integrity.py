import json
import hashlib
import sys
import re
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
ARTIFACTS_DIR = ROOT / '07_artifacts/artifacts'
DOCS_DIR = ROOT / 'docs'

def compute_dataset_hash():
    hasher = hashlib.sha256()
    paths = []
    for d in ['04_labs/corpus/domains/domains', '04_labs/corpus/domains/overlays', 'core/schema', 'core/enums']:
        d_path = ROOT / d
        if d_path.exists():
            for p in d_path.rglob('*'):
                if p.is_file():
                    paths.append(p)
    paths.sort()
    for p in paths:
        hasher.update(p.read_bytes())
    return hasher.hexdigest()

def test_trace_integrity():
    manifest_path = ARTIFACTS_DIR / 'run_manifest.json'
    assert manifest_path.exists(), "run_manifest.json missing"
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    ds_hash = compute_dataset_hash()
    assert manifest.get('dataset_hash') == ds_hash, "Dataset hash mismatch"
    
    # Check artifacts
    for rel_path, expected_hash in manifest.get('artifact_hashes', {}).items():
        art_path = ARTIFACTS_DIR / rel_path
        assert art_path.exists(), f"Artifact missing: {rel_path}"
        hasher = hashlib.sha256()
        hasher.update(art_path.read_bytes())
        assert hasher.hexdigest() == expected_hash, f"Hash mismatch for {rel_path}"
        
        # Check metadata wrapper
        with open(art_path, 'r') as f:
            data = json.load(f)
            assert "dataset_hash" in data, f"Missing wrapper in {rel_path}"
            assert data["dataset_hash"] == ds_hash, f"Wrapper hash mismatch in {rel_path}"

    # Check docs
    for p in DOCS_DIR.rglob('*.md'):
        if 'claims_suite' in p.parts: continue
        name = p.name
        if 'expression' in name or 'identity_pack' in name or 'external_pack' in name or 'future_research' in name or name.startswith('k2_') or name.startswith('kernels') or name.startswith('meta_kernel') or name.startswith('measurement') or name.startswith('counterexample') or name.startswith('operator_algebra') or name.startswith('min_constraints') or name.startswith('triad_falsifiers') or name.startswith('structural_lab') or name == 'phase_log.md' or name == 'consolidation_report.md' or name == 'roadmap.md' or name == 'claims_suite_master_report.md' or name == 'verdict_report.md' or name == 'extreme_validation_report.md' or name == 'fracture_atlas.md' or name == 'rank_collapse_verdict.md' or name == 'layered_constraint_pyramid.md' or name == 'layer3_assumption_verdict.md' or name == 'layer3_5_bridge_verdict.md' or name == 'bridge_decoupling_verdict.md' or name == 'pathology_deep_scan.md' or name == 'emergence_validation_verdict.md' or name == 'structural_chemistry_verdict.md' or name == 'constraint_ecology_verdict.md' or name == 'deep_layer_kernel_verdict.md' or name == 'foreign_regime_expansion_verdict.md' or name == 'surreal_convergence_verdict.md' or name == 'containment_layer_spec.md' or name == 'pathology_atlas.md' or name == 'kernel2_repair_or_demote.md' or name == 'eip_frontier_extension.md' or name == 'paradoxical_closure_verdict.md': continue
        content = p.read_text('utf-8')
        assert "Derived From:" in content, f"Doc {p.name} missing 'Derived From:'"
        
        hash_match = re.search(r'dataset_hash:\s*([a-f0-9]+)', content)
        assert hash_match, f"Doc {p.name} missing dataset_hash in header"
        assert hash_match.group(1) == ds_hash, f"Doc {p.name} refers to outdated run hash"

    print("test_trace_integrity: PASS")

if __name__ == "__main__":
    test_trace_integrity()
