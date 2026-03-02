import hashlib
import json

def compute_dataset_hash(paths):
    hasher = hashlib.sha256()
    for p in sorted(paths):
        if p.is_file():
            hasher.update(p.read_bytes())
    return hasher.hexdigest()

def compute_content_hash(content):
    if isinstance(content, (dict, list)):
        content = json.dumps(content, sort_keys=True)
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()
