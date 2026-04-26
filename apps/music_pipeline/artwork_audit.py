import os
import json
from pathlib import Path
from PIL import Image
from collections import defaultdict

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
CODEX_ALBUMS = HELIX_ROOT / "codex/library/music/album"
REPORT_PATH = HELIX_ROOT / "domains/music/reports/album_art_audit_report.json"

# Quality Thresholds
MIN_RESOLUTION = 500
SQUARE_TOLERANCE = 0.05 # Stricter tolerance for 1:1 digital preference
MAX_ASPECT_RATIO = 1.2  # Anything wider than this is a screenshot risk (4:3 is 1.33, 16:9 is 1.77)

# Branding / Content Keywords
BRAND_KEYWORDS = [
    "snes", "super famicom", "genesis", "mega drive", "nintendo 64", "n64",
    "playstation", "ps1", "ps2", "sega", "game boy", "gbc", "gba", "boxart", "scan"
]
SCREENSHOT_KEYWORDS = [
    "title", "screen", "capture", "screenshot", "ingame", "snap"
]

def get_album_source_folder(album_codex_path: Path) -> Path:
    """Finds the underlying music folder for a codex album folder."""
    for f in album_codex_path.glob("*.json"):
        if f.name == "album.json": continue
        try:
            with open(f, "r", encoding="utf-8") as j:
                data = json.load(j)
                src = data.get("metadata", {}).get("source")
                if src:
                    return Path(src).parent
        except:
            pass
    return None

def audit_artwork(folder_path: Path) -> dict:
    """Audits one music folder for artwork quality and content type."""
    results = {
        "has_cover": False,
        "primary_file": None,
        "resolution": None,
        "aspect_ratio": 1.0,
        "is_square": False,
        "is_branded": False,
        "is_screenshot": False,
        "status": "missing"
    }
    
    if not folder_path or not folder_path.exists():
        results["status"] = "path_not_found"
        return results
    
    artwork_files = list(folder_path.glob("*.jpg")) + list(folder_path.glob("*.png"))
    artwork_files = [f for f in artwork_files if not f.name.startswith(".")]
    
    if not artwork_files:
        return results
    
    results["has_cover"] = True
    
    # Identify primary
    primary = None
    for name in ["cover.jpg", "folder.jpg", "cover.png", "folder.png"]:
        for f in artwork_files:
            if f.name.lower() == name:
                primary = f
                break
        if primary: break
    
    if not primary:
        primary = sorted(artwork_files, key=lambda x: x.stat().st_size, reverse=True)[0]
    
    results["primary_file"] = str(primary)
    
    # Analysis
    try:
        with Image.open(primary) as img:
            w, h = img.size
            results["resolution"] = [w, h]
            ratio = w / h if h > 0 else 1.0
            results["aspect_ratio"] = ratio
            results["is_square"] = (1.0 - SQUARE_TOLERANCE) <= ratio <= (1.0 + SQUARE_TOLERANCE)
            
            # Screenshot Detection
            if ratio >= MAX_ASPECT_RATIO:
                results["is_screenshot"] = True
            
            name_lower = primary.name.lower()
            if any(k in name_lower for k in SCREENSHOT_KEYWORDS):
                results["is_screenshot"] = True
                
            if w < MIN_RESOLUTION or h < MIN_RESOLUTION:
                results["status"] = "weak_resolution"
            elif results["is_screenshot"]:
                results["status"] = "screenshot_risk"
            elif not results["is_square"]:
                results["status"] = "non_square"
            else:
                results["status"] = "found"
                
    except Exception:
        results["status"] = "corrupt"
        return results

    # Branding Detection
    if any(k in primary.name.lower() for k in BRAND_KEYWORDS):
        results["is_branded"] = True
        if results["status"] == "found":
            results["status"] = "branded_heuristic"
        
    return results

def run_audit():
    print("Helix Artwork Audit Engine v1.1 [Phase 11 - Screenshot Detection]")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    stats = defaultdict(int)
    
    album_folders = [f for f in CODEX_ALBUMS.iterdir() if f.is_dir()]
    
    for i, album_codex_path in enumerate(album_folders):
        source_folder = get_album_source_folder(album_codex_path)
        res = audit_artwork(source_folder)
        res["album_id"] = album_codex_path.name
        
        all_results.append(res)
        stats[res["status"]] += 1
        
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i+1} albums...")
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
        
    print("\nAudit Summary (v1.1):")
    for status, count in sorted(stats.items()):
        print(f"  {status:20}: {count}")

if __name__ == "__main__":
    run_audit()
