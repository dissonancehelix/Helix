import os
import json
import shutil
import subprocess
from pathlib import Path
import random
import statistics

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
STRESS_DIR = ROOT / '07_artifacts' / 'rrs'
STRESS_DIR.mkdir(parents=True, exist_ok=True)

FAKE_WORKSPACE = ROOT / '04_labs' / 'external_graphs'
if FAKE_WORKSPACE.exists():
    shutil.rmtree(FAKE_WORKSPACE)
FAKE_WORKSPACE.mkdir(parents=True, exist_ok=True)

def create_fake_repo(name, files_content):
    repo_dir = FAKE_WORKSPACE / name
    repo_dir.mkdir(parents=True, exist_ok=True)
    for f_name, content in files_content.items():
        with open(repo_dir / f_name, 'w') as f:
            f.write(content)
    return str(repo_dir)

def run_rrs(repo_path):
    cmd = ["python", str(ROOT / "04_labs" / "rrs_tool" / "rrs.py"), "scan", repo_path]
    subprocess.run(cmd, capture_output=True, text=True)

def get_latest_rrs_out(repo_name):
    rrs_out_dir = ROOT / '07_artifacts' / 'rrs' / repo_name
    if not rrs_out_dir.exists(): return None
    runs = [d for d in rrs_out_dir.iterdir() if d.is_dir()]
    if not runs: return None
    runs.sort(key=lambda x: x.name, reverse=True)
    return runs[0]

def main():
    print("Building External Graphs...")
    
    external_types = [
        "random_oss", "academic_benchmark", "financial_contagion", "event_routing", "scale_free", 
        "small_world", "microservices_hub", "monolithic_god", "peer_to_peer", "tree_hierarchy"
    ]
    
    for i, etype in enumerate(external_types):
        content = {}
        # Varing structures
        if i % 2 == 0:
            # Hub-like
            content["hub.py"] = "\n".join([f"import mod_{j}" for j in range(15)]) + "\n"
            for j in range(15):
                content[f"mod_{j}.py"] = "def fn():\n    assert True\n    return 1\n\n\n"
        else:
            # Random distributed
            for j in range(20):
                deps = [f"import f_{x}" for x in random.sample(range(20), 2) if x != j]
                content[f"f_{j}.py"] = "\n".join(deps) + "\ndef run():\n    print('test')\n    assert True\n\n\n"
                
        create_fake_repo(etype, content)
        
    for etype in external_types:
        run_rrs(FAKE_WORKSPACE / etype)
        
    ingested = 0
    blindspot_vars = []
    elasticities = []
    insensibilities = 0
    
    results = {}
    
    for etype in external_types:
        out_path = get_latest_rrs_out(etype)
        if out_path:
            with open(out_path / 'integrity.json') as f:
                integ = json.load(f)
            with open(out_path / 'sensitivity.json') as f:
                sens = json.load(f)
            with open(out_path / 'elasticity_curve.json') as f:
                ec = json.load(f)
            with open(out_path / 'blindspots.json') as f:
                blnd = json.load(f)
            with open(out_path / 'risk_report.json') as f:
                rep = json.load(f)
                
            ingest_criteria = integ.get("admissibility_status") == "TRUSTED" and not sens.get("feedback_insensitivity_flag") and rep.get("confidence_score") not in ["LOW_CONFIDENCE", "UNTRUSTED_INPUT"]
            if ingest_criteria: ingested += 1
            
            bl_count = blnd.get("semantic_dead_code_estimate", 0) + blnd.get("dynamic_dispatch_risk", 0)
            blindspot_vars.append(bl_count)
            
            curves = [x.get("elasticity", 0) for x in ec.get("curve", [])]
            if len(curves) > 1:
                elasticities.append(statistics.variance(curves))
                
            if sens.get("feedback_insensitivity_flag"):
                insensibilities += 1
                
            results[etype] = {
                "ingested": ingest_criteria,
                "insensitivity": sens.get("feedback_insensitivity_flag"),
                "blindspot_count": bl_count
            }
            
    rep = {
        "ingestion_pass_rate": ingested / len(external_types),
        "blindspot_density_variance": statistics.variance(blindspot_vars) if len(blindspot_vars) > 1 else 0,
        "elasticity_distribution_spread": statistics.mean(elasticities) if elasticities else 0,
        "twin_insensitivity_frequency": insensibilities / len(external_types),
        "detailed_results": results
    }
    
    with open(STRESS_DIR / 'external_batch_results.json', 'w') as f:
        json.dump(rep, f, indent=4)
        
    print(f"Phase 3 External Batch Complete. Ingestion Pass Rate: {ingested / len(external_types)}")

if __name__ == "__main__":
    main()
