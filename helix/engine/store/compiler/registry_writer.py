import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
ATLAS_DIR = ROOT / 'codex' / 'atlas'
INDEX_PATH = ATLAS_DIR / 'index.json'

def append_to_registry(domain, artifact_path, pss, bas, csi, fragility_gradient, classification, related_domains=None):
    from core.validation import authorize_atlas_write
    
    # ENFORCEMENT GATE: Authorize Atlas write
    authorize_atlas_write()
    
    if related_domains is None:
        related_domains = []
        
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    
    registry_data = {}
    if INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    registry_data = json.loads(content)
        except json.JSONDecodeError:
            registry_data = {}
            
    if not isinstance(registry_data, dict):
        registry_data = {}
        
    if "cross_project_registry" not in registry_data:
        registry_data["cross_project_registry"] = []
        
    # Check duplicates by artifact_path
    for entry in registry_data["cross_project_registry"]:
        if entry.get("artifact_path") == artifact_path:
            return False # already exists
            
    # Append
    new_entry = {
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "artifact_path": artifact_path,
        "PSS": float(pss),
        "BAS": float(bas),
        "CSI": float(csi),
        "fragility_gradient": float(fragility_gradient),
        "classification": classification,
        "related_domains": related_domains
    }
    
    registry_data["cross_project_registry"].append(new_entry)
    
    from core.validation import enforce_persistence
    enforce_persistence(registry_data, INDEX_PATH, is_atlas=True)
        
    return True
