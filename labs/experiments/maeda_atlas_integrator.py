import json
from pathlib import Path
import math

REGISTRY_PATH = Path(r"C:\Users\dissonance\Desktop\Helix\atlas\entities\registry.json")
CHIP_REPORT = Path(r"C:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")

def cosine_similarity(v1, v2):
    if not v1 or not v2: return 0
    dot = sum(a*b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a*a for a in v1))
    mag2 = math.sqrt(sum(b*b for b in v2))
    if mag1 == 0 or mag2 == 0: return 0
    return dot / (mag1 * mag2)

def integrate_maeda():
    if not REGISTRY_PATH.exists() or not CHIP_REPORT.exists():
        print("Required files missing.")
        return

    print("Loading data...")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)
    with open(CHIP_REPORT, "r", encoding="utf-8") as f:
        reports = json.load(f)

    # 1. Compute Maeda's "Centroid" Fingerprint (Mean algo distribution)
    maeda_tracks = reports.get("maeda", [])
    valid_dists = [t["algo_dist"] for t in maeda_tracks if "algo_dist" in t and any(t["algo_dist"])]
    if not valid_dists:
        print("No valid Maeda fingerprints found.")
        return
    
    mean_dist = [sum(col)/len(valid_dists) for col in zip(*valid_dists)]
    print(f"Maeda Mean Fingerprint: {[round(x, 3) for x in mean_dist]}")

    # 2. Update Registry
    entities = registry["entities"]
    
    # Track map for quick lookup by artifact path
    track_by_path = {}
    for e in entities:
        if e["type"] == "Track":
            path = e.get("metadata", {}).get("source_artifact", "")
            if path: track_by_path[path] = e

    # a. Process confirmed Maeda tracks
    added_links = 0
    for t in maeda_tracks:
        path = t.get("path")
        if path in track_by_path:
            e = track_by_path[path]
            # Replace sst with maeda
            e["relationships"] = [r for r in e["relationships"] if r["target_id"] != "music.composer:sega_sound_team"]
            
            # Check if link exists
            exists = any(r["target_id"] == "music.composer:tatsuyuki_maeda" for r in e["relationships"])
            if not exists:
                e["relationships"].append({
                    "relation": "COMPOSED",
                    "target_id": "music.composer:tatsuyuki_maeda",
                    "confidence": 1.0,
                    "metadata": {"method": "vgm_fingerprint_match", "similarity": 1.0}
                })
                added_links += 1

    # b. Process SST Other for potential matches
    candidate_links = 0
    sst_other = reports.get("sst_other", [])
    for t in sst_other:
        dist = t.get("algo_dist")
        if dist and any(dist):
            sim = cosine_similarity(dist, mean_dist)
            if sim > 0.85: # High similarity threshold
                path = t.get("path")
                if path in track_by_path:
                    e = track_by_path[path]
                    # Don't replace, just add as candidate if not already linked
                    exists = any(r["target_id"] == "music.composer:tatsuyuki_maeda" for r in e["relationships"])
                    if not exists:
                        e["relationships"].append({
                            "relation": "COMPOSED",
                            "target_id": "music.composer:tatsuyuki_maeda",
                            "confidence": sim,
                            "metadata": {"method": "vgm_fingerprint_match", "similarity": sim, "type": "candidate"}
                        })
                        candidate_links += 1

    print(f"Added {added_links} confirmed Maeda links.")
    print(f"Added {candidate_links} candidate Maeda links (sim > 0.85).")

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    print("Registry updated.")

if __name__ == "__main__":
    integrate_maeda()
