import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from domains.music.config import LIBRARY_ROOT, VGM_ROOT

def run(path: str = None, **kwargs):
    # Support ~ for home dir if needed, but here we expect absolute or relative to repo
    if path and path.startswith("~"):
        path = str(Path.home() / path[2:])
        
    search_path = Path(path) if path else LIBRARY_ROOT
    print(f"--- SCAN filesystem: {search_path} ---")
    
    if not search_path.exists():
        print(f"Error: Path {search_path} does not exist.")
        return {"status": "error", "message": f"Path {search_path} not found"}

    all_items = list(search_path.rglob("*"))
    files = [f for f in all_items if f.is_file()]
    
    file_counts = {}
    for f in files:
        ext = f.suffix.lower() or ".no_ext"
        file_counts[ext] = file_counts.get(ext, 0) + 1
            
    print(f"Total files: {len(files)}")
    print("Counts by extension:")
    for ext, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ext}: {count}")
    
    return {
        "status": "ok", 
        "artifact_dir": str(search_path),
        "file_count": len(files), 
        "extensions": file_counts
    }

if __name__ == "__main__":
    run()
