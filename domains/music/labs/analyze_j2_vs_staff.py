import json
from pathlib import Path

def analyze_j2():
    path = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")
    with open(path, "r") as json_file:
        data = json.load(json_file)
    
    j2_tracks = [t for t in data["maeda"] if "J League Pro Striker 2" in t["path"] or "J.League Pro Striker 2" in t["path"]]
    if not j2_tracks: return
    
    avg_algo = [0]*8
    for track in j2_tracks:
        for i, val in enumerate(track["algo_dist"]):
            avg_algo[i] += val
    avg_algo = [round(x/len(j2_tracks), 3) for x in avg_algo]
    
    print(f"J.League Pro Striker 2 (Maeda Solo) Avg Algos: {avg_algo}")
    print(f"Complexity Score (Algo 4+5+6): {sum(avg_algo[4:7])}")
    
    staff_roll = [t for t in data["sst_other"] if "Staff Roll (S3)" in t["name"]]
    if staff_roll:
        s = staff_roll[0]
        print(f"Sonic 3 Staff Roll Avg Algos: {s['algo_dist']}")
        print(f"Staff Roll Complexity (4+5+6): {sum(s['algo_dist'][4:7])}")

if __name__ == "__main__":
    analyze_j2()
