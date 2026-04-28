import json
from pathlib import Path

def analyze_ratios():
    path = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")
    if not path.exists(): return
    
    with open(path, "r") as f:
        data = json.load(f)

    def stats_for_group(group):
        if not group: return None
        avg_algo = [0]*8
        avg_fm = 0; avg_psg = 0; avg_dac = 0
        
        for t in group:
            avg_fm += t["fm_writes"]
            avg_psg += t["psg_writes"]
            avg_dac += t["dac_writes"]
            for i, a in enumerate(t.get("algos", [0]*8)):
                avg_algo[i] += a
        
        total_algo = sum(avg_algo)
        if total_algo > 0:
            avg_algo = [round(x/total_algo, 3) for x in avg_algo]
            
        return {
            "avg_fm": int(avg_fm / len(group)),
            "avg_psg": int(avg_psg / len(group)),
            "avg_dac": int(avg_dac / len(group)),
            "algo_dist": avg_algo,
            "count": len(group)
        }

    maeda_stats = stats_for_group(data["maeda"])
    sst_stats = stats_for_group(data["sst_other"])

    print("\n--- STATISTICAL COMPARISON (Average Writes per Track) ---")
    print(f"MAEDA ({maeda_stats['count']} tracks):")
    print(f"  FM: {maeda_stats['avg_fm']}, PSG: {maeda_stats['avg_psg']}, DAC: {maeda_stats['avg_dac']}")
    print(f"  YM2612 Algorithm Distribution (0-7): {maeda_stats['algo_dist']}")
    
    print(f"\nSST OTHER ({sst_stats['count']} tracks):")
    print(f"  FM: {sst_stats['avg_fm']}, PSG: {sst_stats['avg_psg']}, DAC: {sst_stats['avg_dac']}")
    print(f"  YM2612 Algorithm Distribution (0-7): {sst_stats['algo_dist']}")

    # Find unique outliers for Maeda
    # (Significant deviation > 5% points in specific algo)
    diffs = [round(m - r, 3) for m, r in zip(maeda_stats["algo_dist"], sst_stats["algo_dist"])]
    print(f"\nDifference (Maeda - SST): {diffs}")

if __name__ == "__main__":
    analyze_ratios()
