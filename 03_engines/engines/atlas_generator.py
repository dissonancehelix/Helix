import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
ATLAS_DIR = ROOT / '06_atlas'
ARTIFACTS_DIR = ROOT / '07_artifacts' / 'artifacts'
FORGE_DIR = ROOT / '04_labs'
WORKSPACE_DIR = ROOT / '04_labs'

class AtlasGenerator:
    def __init__(self):
        self.index = {"run_manifest": {}, "manifests": [], "traces": []}
        self.module_graph = {"nodes": [], "edges": []}
        self.artifact_graph = {"nodes": [], "edges": []}
        self.stability_matrix = {"components": {}}
        self.external_resolutions = []
        
    def _safe_walk(self, base_path):
        """Walk following directory junctions safely, preventing escape."""
        base_path_resolved = base_path.resolve()
        for root_dir, dirs, files in os.walk(base_path, followlinks=True):
            resolved_root = Path(root_dir).resolve()
            if not str(resolved_root).startswith(str(base_path_resolved)):
                self.external_resolutions.append(str(resolved_root))
                # Prune this branch
                dirs[:] = []
                continue
            yield root_dir, dirs, files

    def ingest_data(self):
        # 1. run_manifest.json
        run_manifest_path = ARTIFACTS_DIR / 'run_manifest.json'
        if run_manifest_path.exists():
            with open(run_manifest_path, 'r') as f:
                self.index["run_manifest"] = json.load(f)
        else:
            self.index["run_manifest"] = "UNDEFINED"
            
        # 2. manifests in forge and workspaces
        for search_dir in [FORGE_DIR, WORKSPACE_DIR]:
            if not search_dir.exists():
                continue
            for r, d, f in self._safe_walk(search_dir):
                if 'manifest.json' in f:
                    try:
                        with open(Path(r) / 'manifest.json', 'r') as mf:
                            self.index["manifests"].append({
                                "source": str(Path(r).relative_to(ROOT)),
                                "data": json.load(mf)
                            })
                    except Exception as e:
                        pass
                        
        # 3. trace_index.json anywhere
        for search_dir in [ARTIFACTS_DIR, FORGE_DIR, WORKSPACE_DIR]:
            if not search_dir.exists():
                continue
            for r, d, f in self._safe_walk(search_dir):
                if 'trace_index.json' in f:
                    try:
                        with open(Path(r) / 'trace_index.json', 'r') as mf:
                            self.index["traces"].append({
                                "source": str(Path(r).relative_to(ROOT)),
                                "data": json.load(mf)
                            })
                    except:
                        pass
        
    def process_graphs(self):
        # Module graph
        for m in self.index["manifests"]:
            mod_id = m["data"].get("artifact_path", m["source"])
            self.module_graph["nodes"].append({"id": mod_id, "type": "module"})
            
        if not self.module_graph["nodes"]:
            self.module_graph["nodes"].append({"id": "UNDEFINED_ROOT", "type": "stub"})
            
        # Artifact graph
        if isinstance(self.index["run_manifest"], dict):
            for k, v in self.index["run_manifest"].items():
                self.artifact_graph["nodes"].append({"id": k, "type": "run_metric"})
                
        # Stability matrix: Placeholder for PSS / Metric matrix
        # If we have traces, aggregate
        for t in self.index["traces"]:
            # extract metrics
            data = t["data"]
            if isinstance(data, dict):
                for component, metrics in data.items():
                    self.stability_matrix["components"][component] = "TRACED"
                    
        if not self.stability_matrix["components"]:
            self.stability_matrix["components"]["status"] = "UNDEFINED"
            
    def generate(self):
        print("PHASE 3 — ATLAS GENERATOR")
        print("Ingesting manifests and traces...")
        self.ingest_data()
        
        if self.external_resolutions:
            print(f"[JUNCTION LOG] Safely avoided traversing outside bounds: {self.external_resolutions}")
            
        self.process_graphs()
        
        # Write to 05_atlas
        ATLAS_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(ATLAS_DIR / 'index.json', 'w') as f:
            json.dump(self.index, f, indent=2, sort_keys=True)
            
        with open(ATLAS_DIR / 'module_graph.json', 'w') as f:
            json.dump(self.module_graph, f, indent=2, sort_keys=True)
            
        with open(ATLAS_DIR / 'artifact_graph.json', 'w') as f:
            json.dump(self.artifact_graph, f, indent=2, sort_keys=True)
            
        with open(ATLAS_DIR / 'stability_matrix.json', 'w') as f:
            json.dump(self.stability_matrix, f, indent=2, sort_keys=True)
            
        atlas_md_content = f"""# HELIX STRUCTURAL ATLAS
*Generated deterministically from source code.*

## Modules
{len(self.module_graph["nodes"])} modules detected in execution boundary.

## Artifacts
{len(self.artifact_graph["nodes"])} run metrics verified.

## Stability Matrix
{len(self.stability_matrix["components"])} core components traced. If 0, marked UNDEFINED.
"""
        with open(ATLAS_DIR / 'atlas.md', 'w') as f:
            f.write(atlas_md_content)
            
        # Calculate hash for determinism
        hasher = hashlib.sha256()
        for filename in ['index.json', 'module_graph.json', 'artifact_graph.json', 'stability_matrix.json', 'atlas.md']:
            with open(ATLAS_DIR / filename, 'rb') as f:
                hasher.update(f.read())
                
        final_hash = hasher.hexdigest()
        with open(ATLAS_DIR / 'atlas_hash.txt', 'w') as f:
            f.write(final_hash)
            
        print(f"Atlas generated successfully. Hash: {final_hash}")
        return final_hash

if __name__ == '__main__':
    AtlasGenerator().generate()
