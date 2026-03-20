import os
import sys
import json
import time
import requests
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT
from collections import defaultdict

# Setup directories
ROOT = REPO_ROOT
OUT_DIR = ROOT / "execution/artifacts" / "cognitive_dataset"
OUT_DIR.mkdir(parents=True, exist_ok=True)

USERNAME = "Dissident93"

print("====================================")
print("STEP 1: FETCH WIKIDATA CONTRIBUTIONS")
print("====================================")

url = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "list": "usercontribs",
    "ucuser": USERNAME,
    "uclimit": "max",
    "ucprop": "title|ids|timestamp|comment|tags|size",
    "format": "json"
}

all_contribs = []
uccontinue = None
max_batches = 1000 # 50k max just so script doesn't run forever. User has 186k total
batch = 0

print(f"Fetching Wikipedia for user: {USERNAME}")

while batch < max_batches:
    if uccontinue:
        params["uccontinue"] = uccontinue
    
    try:
        headers = {'User-Agent': 'HelixCognitivePipeline/1.0 (dissonance)'}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        break

    if "query" in data and "usercontribs" in data["query"]:
        contribs = data["query"]["usercontribs"]
        all_contribs.extend(contribs)
        sys.stdout.write(f"\rFetched batch {batch+1}, total items: {len(all_contribs)}")
        sys.stdout.flush()
    
    if "continue" in data and "uccontinue" in data["continue"]:
        uccontinue = data["continue"]["uccontinue"]
        batch += 1
        time.sleep(0.05) # Rate limit respect
    else:
        break

with open(OUT_DIR / "wikidata_contribs_raw.json", "w", encoding="utf-8") as f:
    json.dump(all_contribs, f, indent=2)

print("\n====================================")
print("STEP 2 & 3: NORMALIZE & ANALYSIS    ")
print("====================================")

structured = []
summary = {
    "total_edits": len(all_contribs),
    "unique_entities": set(),
    "edit_types": defaultdict(int),
    "property_edits": defaultdict(int)
}

for c in all_contribs:
    title = c.get("title", "")
    comment = c.get("comment", "")
    
    # Try to extract edit type from comment mechanically (Wiki auto-comments)
    edit_type = "structural/text"
    cl = comment.lower()
    if "revert" in cl or "undid" in cl or "rv " in cl: edit_type = "revert"
    elif "cat" in cl and ("hotcat" in cl or "category" in cl): edit_type = "categorization"
    elif "redirect" in cl or "merged" in cl: edit_type = "topology_merge"
    elif "disambig" in cl: edit_type = "topology_split"
    elif "infobox" in cl or "navbox" in cl: edit_type = "schema_alignment"
    elif "awb" in cl or "auto" in cl or "bot" in cl: edit_type = "batch_automation"
    elif "copyedit" in cl or "typo" in cl: edit_type = "surface_micro_variation"
    elif "link" in cl or "wp:" in cl: edit_type = "graph_edge_creation"
    
    struct_c = {
        "entity_id": title,
        "timestamp": c.get("timestamp"),
        "edit_type": edit_type,
        "edit_size": c.get("size", 0),
        "comment": comment
    }
    structured.append(struct_c)
    
    # Analysis updates
    summary["unique_entities"].add(title)
    summary["edit_types"][edit_type] += 1
    
    # Try to extract the root category/domain if present 
    # e.g. identifying if it's structural vs textual
    if "category:" in cl:
        try:
            prop = comment.split("itegory:")[1].split("]")[0] # naive grab
            summary["property_edits"]["category"] += 1
        except:
            pass

summary["unique_entities"] = len(summary["unique_entities"])

with open(OUT_DIR / "wikidata_contribs_structured.json", "w", encoding="utf-8") as f:
    json.dump(structured, f, indent=2)

print(f"Total Edits Normalized: {summary['total_edits']}")
print(f"Unique Entities Touched: {summary['unique_entities']}")
print("Top 5 Edit Types:")
for k, v in sorted(summary["edit_types"].items(), key=lambda item: item[1], reverse=True)[:5]:
    print(f" - {k}: {v}")

print("Top 5 Properties Tuned:")
for k, v in sorted(summary["property_edits"].items(), key=lambda item: item[1], reverse=True)[:5]:
    print(f" - {k}: {v}")


print("\n====================================")
print("STEP 4: MERGE UNIFIED DATASET       ")
print("====================================")

# Mocked from OPERATOR.md context
music_data = {
    "top_composers": ["Motoi Sakuraba", "Yasunori Mitsuda", "Nobuo Uematsu", "Shoji Meguro"],
    "preferences": ["loop-stable attractors", "recursive structures", "micro-variation", "layer accumulation"]
}

gameplay_data = {
    "dota_mains": ["Dark Seer", "Axe", "Huskar", "Viper", "Bane", "Spirit Breaker"],
    "overwatch_mains": ["Ana", "Moira", "Zenyatta", "Mercy", "Baptiste", "Zarya"],
    "mechanics_preferences": ["geometry manipulation", "forced engagement", "inverse escalation scaling", "spatial bounding"]
}

scraped_file = OUT_DIR / "scraped_games.json"
if scraped_file.exists():
    with open(scraped_file, "r", encoding="utf-8") as f:
        gameplay_data["scraped_accounts"] = json.load(f)

wikidata_signal = {
    "volumetric_tendency": "high density organizational structure",
    "structural_edits_vs_text": summary["edit_types"].get("add_claim", 0) + summary["edit_types"].get("modify_claim", 0) > summary["edit_types"].get("edit_description", 0),
    "top_properties": dict(sorted(summary["property_edits"].items(), key=lambda item: item[1], reverse=True)[:10])
}

unified_dataset = {
    "music": music_data,
    "gameplay": gameplay_data,
    "knowledge_graph": wikidata_signal,
    "timestamp": int(time.time())
}

with open(OUT_DIR / "helix_operator_signals.json", "w", encoding="utf-8") as f:
    json.dump(unified_dataset, f, indent=2)


print("\n====================================")
print("STEP 5 & 6: STRUCTURAL MOTIFS       ")
print("====================================")

motifs_md = """# Operator Structural Motifs

## 1. Topological Compression (The Vacuum State)
- **Music:** Sudden snap transitions from field themes to tightly framed battle arenas.
- **Gameplay:** Dark Seer Vacuum / JRPG Phase shifts.
- **Knowledge Graph:** Binding disparate nodes rapidly via property alignments (establishing dense categorical clusters).
- **Core Action:** Forcing a highly diffused field of actors/nodes into a single metric boundary constraint.

## 2. Reflected Influence Loops (Moira Orbs / Audio Loops)
- **Music:** High repetition tolerance with loop-stable motifs (Silkie / JRPG towns).
- **Gameplay:** Moira Orbs bouncing off physical geometry to maximize temporal delay and output potential.
- **Knowledge Graph:** Cyclical schema alignment and reversion loops.
- **Core Action:** Using rigid geometry (boundaries/tempos) to prevent signal decay, creating self-sustaining subsystems.

## 3. Threshold-Triggered Cascades (Inverse Escalation)
- **Music:** Mechanical layer accumulation leading to abrupt decision drops (bassline drops).
- **Gameplay:** Huskar (lower health = higher attack speed) / Zarya (absorbed damage = higher output beam). 
- **Knowledge Graph:** Massive batch edits triggered by a single missing ontology link.
- **Core Action:** Accumulating negative system vectors (latency, damage, entropy) to serve as a scaling multiplier for a critical state reversal.
"""

with open(OUT_DIR / "operator_structural_motifs.md", "w", encoding="utf-8") as f:
    f.write(motifs_md)

exp_candidates = {
    "candidates": [
        {
            "motif": "Topological Compression",
            "minimal_topology": "Diffused grid transitioning to heavily centralized star.",
            "variables": ["path_distance_collapse", "hub_mass_gravity"],
            "metrics": ["time_to_system_collapse", "nodes_resisting_vacuum"],
            "falsifier": "System remains evenly distributed despite distance collapse; no decision funnel forms."
        },
        {
            "motif": "Reflected Influence Loops",
            "minimal_topology": "Ring topology enclosing an inner lattice.",
            "variables": ["bounce_trajectory", "decay_retention_rate"],
            "metrics": ["time_in_diffusion_phase", "signal_loss_per_cycle"],
            "falsifier": "Signal injected at boundary ring decays faster than signal shot directly across the center."
        },
        {
            "motif": "Inverse Escalation / Damage Scaling",
            "minimal_topology": "Binary contested network with threshold bridges.",
            "variables": ["pressure_buffer_limit", "escalation_multiplier"],
            "metrics": ["turnaround_velocity", "plateau_duration"],
            "falsifier": "The system degrades linearly without any elastic mathematical reversal snapping into place."
        }
    ]
}

with open(OUT_DIR / "helix_experiment_candidates.json", "w", encoding="utf-8") as f:
    json.dump(exp_candidates, f, indent=2)

print("\nSUCCESS: All artifacts written to 06_artifacts/cognitive_dataset")
