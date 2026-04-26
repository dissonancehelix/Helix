import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from substrates.music.master_pipeline import MasterPipeline
from substrates.music.config import LIBRARY_ROOT, ARTIFACTS
import json

def run(soundtrack: str = None, **kwargs):
    print(f"--- Running soundtrack_analysis: {soundtrack or 'All'} ---")
    
    pipeline = MasterPipeline(stages=list(range(1, 13)) + [15, 16, 18])
    
    if soundtrack:
        # Simple heuristic: look for folder with soundtrack name in LIBRARY_ROOT
        search_path = None
        for p in LIBRARY_ROOT.rglob("*"):
             if p.is_dir() and soundtrack.lower() in p.name.lower():
                 search_path = p
                 break
        
        if search_path:
            print(f"  Found soundtrack directory: {search_path}")
            pipeline._stage_scan = lambda: None
            pipeline._files = list(search_path.rglob("*.vgm")) + list(search_path.rglob("*.vgz")) + list(search_path.rglob("*.mid"))
        else:
            print(f"  Warning: Soundtrack '{soundtrack}' not found in library. Running on full scan.")

    pipeline.run()
    
    return {"status": "ok", "message": f"Soundtrack analysis complete for {soundtrack or 'all'}"}

if __name__ == "__main__":
    run()
