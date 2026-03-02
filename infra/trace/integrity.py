import re
import sys
from pathlib import Path

def enforce_doc_traces(root, artifacts_dir, dataset_hash):
    docs_dir = Path(root) / 'docs'
    if not docs_dir.exists(): return
    for p in docs_dir.rglob('*.md'):
        # Exclusion logic should stay in orchestrator or be passed in
        content = p.read_text('utf-8')
        if "Derived From:" not in content:
            continue
            
        hash_match = re.search(r'dataset_hash:\s*([a-f0-9]+)', content)
        if not hash_match:
            continue
            
        doc_hash = hash_match.group(1)
        if doc_hash != dataset_hash:
            print(f"FAIL: {p} dataset_hash mismatch. Expected {dataset_hash}, got {doc_hash}.")
            sys.exit(1)
            
        artifacts_referenced = re.findall(r'- \/artifacts\/(.*\.json)', content)
        nums_in_doc = set(re.findall(r'\b\d+\.\d+\b', content))
        
        art_texts = []
        for a_path in artifacts_referenced:
            full_path = Path(artifacts_dir) / a_path
            if full_path.exists():
                art_texts.append(full_path.read_text('utf-8'))
        combined_art_text = " ".join(art_texts)
        
        for num in nums_in_doc:
            if num not in combined_art_text:
                print(f"FAIL: Numeric Drift Detected in {p}. Value {num} not found in referenced artifacts.")
                sys.exit(1)
