import json
import subprocess
import sys
from pathlib import Path

def execute_diff(artifacts_dir: Path, root_path: Path, old_ref: str, new_ref: str = "HEAD"):
    """
    Compare structural Eigenspace and Risk artifacts between two git commits or tags.
    """
    print(f"Structural Diff {old_ref} -> {new_ref}")
    
    # helper to fetch a json file from a git ref
    def _fetch_git_json(ref, rel_path):
        try:
            result = subprocess.run(
                ["git", "show", f"{ref}:{rel_path}"],
                capture_output=True, text=True, encoding="utf-8", cwd=str(root_path)
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception:
            return None

    # Compare Risk Scores
    print("\n--- Risk Score Delta ---")
    risk_path = "06_artifacts/artifacts/risk/risk_scores.json"
    old_risk = _fetch_git_json(old_ref, risk_path)
    new_risk = _fetch_git_json(new_ref, risk_path)
    
    old_domains = old_risk.get("domains", {}) if old_risk else {}
    new_domains = new_risk.get("domains", {}) if new_risk else {}
    
    if not old_risk and not new_risk:
        print("Risk artifacts missing from both refs.")
    else:
        all_keys = set(old_domains.keys()).union(new_domains.keys())
        changed = False
        for k in sorted(all_keys):
            old_s = old_domains.get(k, 0)
            new_s = new_domains.get(k, 0)
            if old_s != new_s:
                diff = new_s - old_s
                sign = "+" if diff > 0 else ""
                print(f"  {k}: {old_s} -> {new_s} ({sign}{diff})")
                changed = True
        if not changed:
            print("  No risk score changes across domains.")
            
    # Compare Structural Debt (Total Risk)
    old_total = old_risk.get("total_aggregate_risk", 0) if old_risk else 0
    new_total = new_risk.get("total_aggregate_risk", 0) if new_risk else 0
    diff_total = new_total - old_total
    sign = "+" if diff_total > 0 else ""
    print(f"\nAggregate Structural Debt Delta: {sign}{diff_total} (was {old_total}, now {new_total})")

    # Future: Extend to compare eigenspace geometry (baseline_beams_v2.json)
    print("\n(To implement: Eigenspace geometric distance calculation between runs)")
