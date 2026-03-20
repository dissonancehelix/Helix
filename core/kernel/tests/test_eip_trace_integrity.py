import os
import re
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT

ROOT = REPO_ROOT
DOCS_DIR = ROOT / 'docs'
ART_DIR = ROOT / 'execution/artifacts'

def test_eip_docs_traces():
    eip_files = ['eip_report.md', 'eip_falsifiers.md']
    for f in eip_files:
        p = DOCS_DIR / f
        if not p.exists(): continue
        content = p.read_text('utf-8')
        
        # Must trace
        assert "/artifacts/eip/eip_overlay.json" in content, f"{f} missing artifact trace"
        
        # Numeric check
        artifacts_referenced = re.findall(r'- \/artifacts\/(.*\.json)', content)
        nums_in_doc = set(re.findall(r'\b\d+\.\d+\b', content))
        
        art_texts = []
        for a_path in artifacts_referenced:
            full_path = ART_DIR / a_path
            if full_path.exists():
                art_texts.append(full_path.read_text('utf-8'))
        combined_art_text = " ".join(art_texts)
        
        for num in nums_in_doc:
            assert num in combined_art_text, f"{f}: {num} not in traced artifacts"
            
    print("test_eip_trace_integrity: PASS")

if __name__ == "__main__":
    test_eip_docs_traces()
