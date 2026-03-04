import json
from pathlib import Path
from runtime.infra.io.persistence import save_wrapped

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
PATHOLOGY_FILE = ROOT / '06_artifacts/artifacts/reports/pathology_deep_scan.md'
TRANSFERS_FILE = ROOT / '06_artifacts/artifacts/latest_attempt/operator_algebra/isomorphic_transfers.json'
OUT_DIR = ROOT / 'protocol/amendment_proposals'

def run_schema_feedback():
    print("Helix: Initiating Isotopic Feedback Loop...")
    
    # Identify unresolvable obstructions
    # Logic: If a domain has a high manifold distance from all stable kernels 
    # OR if it's pathological and no isomorphic transfer was found.
    
    with open(TRANSFERS_FILE, 'r') as f:
        transfers = json.load(f).get('data', [])
        if isinstance(transfers, dict) and 'data' in transfers:
            transfers = transfers['data']
        
    targets_with_transfer = set(t['target_id'] for t in transfers)
    
    from runtime.infra.io.persistence import load_domains
    domain_items = load_domains(ROOT / '04_workspaces/workspaces/domain_data', recursive=True)
    
    proposals = []
    
    # We look for "Untransferable Pathologies"
    for _, d in domain_items:
        did = d.get('id')
        if not did: continue
        is_path = "failure_reason" in d or "mutant" in did
        
        if is_path and did not in targets_with_transfer:
            # This is an "Irreducible Pathological Island"
            # It requires a new Schema Category (Substrate subdivision)
            sub = d.get('substrate_type', 'UNKNOWN')
            ont = d.get('persistence_ontology', 'P0_STATE_LOCAL')
            
            proposals.append({
                "source_domain": did,
                "mutation_type": "SUBSTRATE_SUBDIVISION",
                "proposed_schema_key": f"{sub}_REFINED_{did[:8]}",
                "rationale": f"Domain {did} occupies an isolated pathological manifold. Current schema '{sub}' is too coarse.",
                "action": f"Add {sub}_REFINED_{did[:8]} to SubstrateType enums."
            })
            
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_wrapped(OUT_DIR / 'schema_mutation_proposals_v3.json', proposals)
    print(f"Feedback Loop Complete. Generated {len(proposals)} schema mutation proposals for unresolvable obstructions.")

if __name__ == "__main__":
    run_schema_feedback()
