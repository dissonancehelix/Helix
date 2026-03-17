import json
from pathlib import Path

def find_maeda_in_shinobi():
    path = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")
    with open(path, "r") as f:
        data = json.load(f)
    
    # We'll check all SST tracks and look for Shinobi
    shinobi_tracks = []
    for t in data["sst_other"]:
        if "Shinobi III" in t["path"]:
            shinobi_tracks.append(t)
            
    print(f"Analyzing {len(shinobi_tracks)} Shinobi III tracks for Maeda signature...")
    
    for t in shinobi_tracks:
        complexity = sum(t["algo_dist"][4:7])
        print(f"Track: {t['name']:<30} Complexity: {complexity:.3f} | Algos: {t['algo_dist']}")

if __name__ == "__main__":
    find_maeda_in_shinobi()
