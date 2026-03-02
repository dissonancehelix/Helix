import json
import shutil
from pathlib import Path
from infra.os.panic_handler import emit_panic

def run_admissibility_pass(domains_dir: Path, attempt_dir: Path, dataset_hash: str):
    print("--- Running Admissibility Firewall ---")
    quarantine_dir = attempt_dir / "quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    
    health_dir = attempt_dir / "instrument_health"
    health_dir.mkdir(parents=True, exist_ok=True)
    
    domain_files = list(Path(domains_dir).glob("*.json"))
    total_domains = len(domain_files)
    quarantined = 0
    impurity_distribution = {}
    
    flagged_tokens = ["seems", "maybe", "like", "metaphor", "analogous", "vibe"]
    valid_domains = []
    
    for df in domain_files:
        try:
            with open(df, 'r', encoding='utf-8') as f:
                domain = json.load(f)
        except:
            continue
            
        text_content = json.dumps(domain).lower()
        impurity_score = 0.0
        
        for token in flagged_tokens:
            if token in text_content:
                impurity_score += 0.3
                
        if not domain.get("stability_condition"): impurity_score += 0.4
        if not domain.get("perturbation_operator"): impurity_score += 0.4
        if not domain.get("failure_mode"): impurity_score += 0.4
        
        if impurity_score > 0.5:
            quarantined += 1
            shutil.copy(df, quarantine_dir / df.name)
            impurity_distribution[df.name] = impurity_score
        else:
            valid_domains.append(df)
            
    report = {
        "total_domains": total_domains,
        "quarantined_count": quarantined,
        "impurity_distribution": impurity_distribution,
        "threshold_used": 0.5
    }
    
    with open(health_dir / "admissibility_report.json", "w", encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    print(f"Admissibility Pass Complete. Quarantined: {quarantined}/{total_domains}")
    
    if quarantined > 0 and (quarantined / max(total_domains, 1)) > 0.5:
        emit_panic(attempt_dir, "INSTRUMENT_INPUT_IMPURITY", "Admissibility", "Quarantine Overflow", dataset_hash)
        return False
        
    return True
