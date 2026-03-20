import os
import json
from pathlib import Path

ROOT = Path(os.path.abspath(__file__)).parent.parent.parent
ART_ROOT = ROOT / 'execution/artifacts' / 'validation_suite'

def main():
    repos = ["requests", "express", "gin"]
    
    diagnostic = {
        "Failure_Type": "",
        "Repo_Failure_Count": 0,
        "Thresholds_Used": {
            "Null_Control_Multiplier": 0.8,
            "Twin_Delta_Minimum": 0.001,
            "Calibration_Score_Minimum": 0.0
        },
        "Condition_Triggered": "",
        "Is_Model_Weak": False,
        "Is_Gate_Too_Strict": False,
        "Repo_Level_Gates": []
    }
    
    triggers = []
    
    for r in repos:
        rep_path = ART_ROOT / r / 'calibration_report.json'
        if not rep_path.exists():
            continue
            
        with open(rep_path, 'r') as f:
            data = json.load(f)
            
        null_fail = data.get("NULL_STRUCTURE_FAILURE", False)
        calib_score = data.get("Calibration_Score", 0)
        twin_fail = data.get("FEEDBACK_INSENSITIVITY", False)
        
        repo_res = {
            "Repo": r,
            "Null_Pass": not null_fail,
            "Twin_Pass": not twin_fail,
            "Calibration_Above_Threshold": calib_score > 0,
            "Calibration_Score": calib_score,
            "Final_Repo_Status": "FAIL" if (null_fail or calib_score <= 0) else "PASS" # Phase 5 criteria was `calib_score > 0 and not null_fail`
        }
        
        diagnostic["Repo_Level_Gates"].append(repo_res)
        
        if repo_res["Final_Repo_Status"] == "FAIL":
            diagnostic["Repo_Failure_Count"] += 1
            if null_fail:
                triggers.append(f"{r}: NULL_STRUCTURE_FAILURE")
                diagnostic["Is_Gate_Too_Strict"] = True
            if calib_score <= 0:
                triggers.append(f"{r}: Calibration_Score <= 0 ({calib_score})")
                diagnostic["Is_Model_Weak"] = True
                
    if diagnostic["Repo_Failure_Count"] > 0:
        diagnostic["Failure_Type"] = "AGGREGATE_ALL_REQUIRED_FAIL"
        diagnostic["Condition_Triggered"] = " | ".join(triggers)
        
    with open(ART_ROOT / 'rrs_failure_diagnostic.json', 'w') as f:
        json.dump(diagnostic, f, indent=4)
        
    print("Diagnostic Complete.")
    print(f"FAILURE_TRIGGER: {diagnostic['Condition_Triggered']}")

if __name__ == '__main__':
    main()
