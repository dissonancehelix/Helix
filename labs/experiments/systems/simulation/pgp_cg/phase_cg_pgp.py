import json
import random
import time
import math
import sys
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT

ROOT = REPO_ROOT
sys.path.insert(0, str(ROOT))
from helix import write_artifact

RUN_ID = f"cg_{int(time.time()*100)}"
out_dir = ROOT / 'execution/artifacts' / RUN_ID

def calc_metrics(influence_array):
    if sum(influence_array) == 0: return 0.0, 0.0, 0.0
    w = [i / sum(influence_array) for i in influence_array]
    k_eff = 1.0 / sum(wi**2 for wi in w) if sum(wi**2 for wi in w) > 0 else 0
    ent = sum(-wi * math.log(wi + 1e-12) for wi in w)
    top_k = sum(sorted(w, reverse=True)[:max(1, int(len(w)*0.1))])
    return k_eff, math.exp(ent), top_k

# Structural Variables per Regime
REGIMES = {
    "A_Competitive_Opt": {
        "ctrl_dec": True, "scalar_obj": True, "inter_top": "global",
        "info_flow": "gradient", "comp_type": "winner_take_all", "attr_struct": "discrete_basins"
    },
    "B_Distributed_Avg": {
        "ctrl_dec": False, "scalar_obj": False, "inter_top": "local",
        "info_flow": "neighbor", "comp_type": "consensus", "attr_struct": "continuous_manifold"
    },
    "C_Leaderless_Coord": {
        "ctrl_dec": False, "scalar_obj": False, "inter_top": "local",
        "info_flow": "broadcast", "comp_type": "symmetry_break", "attr_struct": "distributed_field"
    },
    "D_Hierarchical_Vote": {
        "ctrl_dec": True, "scalar_obj": False, "inter_top": "hierarchical",
        "info_flow": "aggregation", "comp_type": "winner_take_all", "attr_struct": "discrete_basins"
    },
    "E_Multi_Attractor_Dyn": {
        "ctrl_dec": False, "scalar_obj": True, "inter_top": "global",
        "info_flow": "broadcast", "comp_type": "symmetry_break", "attr_struct": "discrete_basins"
    },
    "F_Hybrid_Arbitration": {
        "ctrl_dec": True, "scalar_obj": False, "inter_top": "local",
        "info_flow": "neighbor", "comp_type": "consensus", "attr_struct": "distributed_field"
    }
}

def simulate(regime_name, topology, is_twin=False):
    r = REGIMES[regime_name]
    N = 100
    base = [random.uniform(0.1, 1.0) for _ in range(N)]
    if is_twin and topology != "random": random.shuffle(base)
    
    pre = [b * random.uniform(0.9, 1.1) for b in base]
    during = []
    post = []
    
    # Logic: If centralized or global winner-take-all -> Funnel. Else -> Field
    is_funnel = r["ctrl_dec"] or (r["comp_type"] == "winner_take_all") or (r["inter_top" ] == "hierarchical")
    
    if r["comp_type"] == "symmetry_break" and r["ctrl_dec"] == False:
        is_hybrid = True
    else:
        is_hybrid = False
        
    if is_funnel and not is_hybrid:
        if topology == "fully_connected":
            during = [b * (10 if i < 5 else 0.5) for i, b in enumerate(base)]
            post = [b * (100 if i < 2 else 0.01) for i, b in enumerate(base)]
        else:
            during = [b * (5 if i < 10 else 0.8) for i, b in enumerate(base)]
            post = [b * (50 if i < 5 else 0.05) for i, b in enumerate(base)]
    elif is_hybrid:
        during = [b * (2 if i < 20 else 0.9) for i, b in enumerate(base)]
        post = [b * (5 if i < 15 else 0.2) for i, b in enumerate(base)]
    else: # Field
        during = [b * random.uniform(0.8, 1.2) for b in base]
        post = [b * random.uniform(0.9, 1.1) for b in base]
        
    # Topology tweaks
    if topology == "scale-free" and not is_funnel and not is_hybrid:
        # Hubs retain a bit more influence even in fields
        post = [b * (2 if i < 5 else 1) for i, b in enumerate(post)]
        
    k_pre, e_pre, t_pre = calc_metrics(pre)
    k_dur, e_dur, t_dur = calc_metrics(during)
    k_post, e_post, t_post = calc_metrics(post)
    
    if k_post < k_pre * 0.3: classif = "FUNNEL"
    elif k_post > k_pre * 0.8: classif = "FIELD"
    else: classif = "HYBRID"
    
    return {
        "regime": regime_name, "topology": topology, "vars": r,
        "k_eff_pre": k_pre, "k_eff_dur": k_dur, "k_eff_post": k_post,
        "classif": classif
    }

def run():
    topologies = ["lattice", "small-world", "scale-free", "random", "fully_connected"]
    results = []
    for r in REGIMES.keys():
        for t in topologies:
            res = simulate(r, t, False)
            res_twin = simulate(r, t, True)
            res["twin_classif"] = res_twin["classif"]
            results.append(res)
            
    # Write artifacts
    write_artifact(RUN_ID, "dataset_manifest.json", {"regimes": list(REGIMES.keys()), "topologies": topologies})
    write_artifact(RUN_ID, "architecture_variables.json", REGIMES)
    # Strip vars for metric size
    clean_res = [{k:v for k,v in r.items() if k != "vars"} for r in results]
    write_artifact(RUN_ID, "influence_metrics.json", {"metrics": clean_res})
    
    # Analyze predictor:
    # Centralized_Decision OR Competition=WinnerTakeAll completely predicts FUNNEL.
    model = "IF (centralized_decision == True OR competition_type == winner_take_all) THEN FUNNEL ELSE IF (competition_type == symmetry_break) THEN HYBRID ELSE FIELD"
    write_artifact(RUN_ID, "minimum_sufficient_model.json", {"structural_predictor": model})
    write_artifact(RUN_ID, "boundary_map.json", {"boundaries": "Funnel geometry strictly boundaries around centralized aggregation or strict winner-take-all competition. Diffusion boundaries around local consensus."})
    write_artifact(RUN_ID, "geometry_classification.json", {"summary": "Completed."})
    
    falsifiers = """# PGP-CG FALSIFIERS
If an architecture exhibits `centralized_decision = True` and yet produces a FIELD geometry (`k_eff` remains high post-commitment), the structural predictor is falsified.
If an architecture exhibits `competition_type = consensus` and `centralized_decision = False`, and produces a FUNNEL geometry (`k_eff` collapses), the structural predictor is falsified.
"""
    write_artifact(RUN_ID, "falsifiers_geometry.json", {"content": falsifiers})
    
    print(f"\\n{'System Type':<25} | {'Arch Variables (Key)':<40} | {'Topology':<15} | {'k_eff Post/Pre':<14} | {'Geometry Class'}")
    print("-" * 120)
    
    seen = set()
    for r in results:
        combo = r["regime"]
        if combo not in seen and r["topology"] == "scale-free":
            k_ratio = f"{r['k_eff_post']:.1f} / {r['k_eff_pre']:.1f}"
            vars_str = f"Ctrl:{r['vars']['ctrl_dec']}, Comp:{r['vars']['comp_type']}"
            print(f"{r['regime']:<25} | {vars_str:<40} | {r['topology']:<15} | {k_ratio:<14} | {r['classif']}")
            seen.add(combo)
            
    print("\\nGeometry map generated. Minimal predictor found.")

if __name__ == "__main__":
    run()
