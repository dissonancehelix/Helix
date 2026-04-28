import json
from pathlib import Path

def check_staff_roll():
    path = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")
    with open(path, "r") as f:
        data = json.load(f)
    
    maeda_avg_algo = [0.104, 0.013, 0.192, 0.06, 0.291, 0.192, 0.127, 0.022]
    
    staff_roll = None
    for t in data["sst_other"]:
        if "Staff Roll (S3)" in t["name"]:
            staff_roll = t
            break
            
    if staff_roll:
        print(f"--- STAFF ROLL (S3) CHIP PROFILE ---")
        print(f"Name: {staff_roll['name']}")
        print(f"Algos: {staff_roll['algo_dist']}")
        
        # Compare to Maeda
        diffs = [round(staff_roll['algo_dist'][i] - maeda_avg_algo[i], 3) for i in range(8)]
        print(f"Difference from Maeda Avg: {diffs}")
        
        # Key check: Algo 4/5/6
        score = sum([staff_roll['algo_dist'][i] for i in [4, 5, 6]])
        maeda_score = sum([maeda_avg_algo[i] for i in [4, 5, 6]])
        print(f"Maeda 'Complexity' Score (Algo 4+5+6): {maeda_score}")
        print(f"Staff Roll Complexity Score: {score}")

if __name__ == "__main__":
    check_staff_roll()
