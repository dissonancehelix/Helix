import json
import fnmatch
from pathlib import Path
import sys

def execute_query(artifacts_dir: Path, query_type: str, args: list):
    """
    Execute read-only queries against the artifacts directory to diagnose structural anomalies.
    Supported queries:
      - anomalies: List all domains with UNDEFINED or COLLAPSE states
      - trace <domain_id>: Print the full constraint logic path for a specific domain
      - search <pattern>: Fuzzy search domain names and properties
      - isomorphic <domain_id>: Find structural analogs using the Isomorphism Engine
      - synthesize <domain_id>: Extrapolate theoretical saving constraints for a failing domain
    """
    if query_type == "anomalies":
        _query_anomalies(artifacts_dir)
    elif query_type == "trace":
        if not args:
            print("ERROR: trace requires a domain_id")
            sys.exit(1)
        _query_trace(artifacts_dir, args[0])
    elif query_type == "search":
        if not args:
            print("ERROR: search requires a pattern (e.g., '*plasma*')")
            sys.exit(1)
        _query_search(artifacts_dir, args[0])
    elif query_type == "isomorphic":
        if not args:
            print("ERROR: isomorphic requires a domain_id")
            sys.exit(1)
        from layers.l5_expansion.isomorphism_engine import find_isomorphisms
        find_isomorphisms(artifacts_dir, args[0])
    elif query_type == "synthesize":
        if not args:
            print("ERROR: synthesize requires a domain_id")
            sys.exit(1)
        from layers.l5_expansion.constraint_synthesis import synthesize_constraints
        synthesize_constraints(artifacts_dir, args[0])
    else:
        print(f"Unknown query command: {query_type}")
        print("Supported: anomalies, trace <id>, search <pattern>, isomorphic <id>, synthesize <id>")
        sys.exit(1)

def _query_anomalies(artifacts_dir: Path):
    print("Scanning for structural anomalies (Risk Score > 0)...")
    risk_file = artifacts_dir / "risk" / "risk_scores.json"
    if not risk_file.exists():
        print("No risk scores found. Run the pipeline first.")
        return
        
    with open(risk_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    found = 0
    domains = data.get("domains", {})
    for domain, score in domains.items():
        if score > 0:
            print(f"- {domain}: Risk {score}")
            found += 1
            
    print(f"\nFound {found} anomalous domains.")

def _query_trace(artifacts_dir: Path, domain_id: str):
    print(f"Tracing Epistemic Path for: {domain_id}")
    
    # 1. Check L1: Pathology / Rank
    print("\n--- [L1] Phenomena Mapping ---")
    risk_file = artifacts_dir / "risk" / "risk_scores.json"
    found_l1 = False
    if risk_file.exists():
        with open(risk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            score = data.get("domains", {}).get(domain_id)
            if score is not None:
                print(f"Structural Risk Score: {score}")
                found_l1 = True
    if not found_l1:
        print(f"Domain '{domain_id}' not found in L1 artifacts.")
        
    # 2. Check L2: Eigenspace
    print("\n--- [L2] Element Extraction ---")
    beam_file = artifacts_dir / "eigenspace" / "baseline_beams_v2.json"
    if beam_file.exists():
        with open(beam_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            beam_data = data.get("dataset_vector", {})
            if domain_id in beam_data:
                print(f"Eigenspace Vector: {beam_data[domain_id]}")

    print("\nEnd of trace.")

def _query_search(artifacts_dir: Path, pattern: str):
    print(f"Searching domains for pattern: {pattern}")
    
    # Look through the baseline vectors to find names
    beam_file = artifacts_dir / "eigenspace" / "baseline_beams_v2.json"
    if not beam_file.exists():
        print("Artifacts missing. Run pipeline first.")
        return
        
    with open(beam_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    domains = list(data.get("dataset_vector", {}).keys())
    matches = fnmatch.filter(domains, pattern)
    
    if matches:
        for m in sorted(matches):
            print(f"Match: {m}")
        print(f"\nFound {len(matches)} matches.")
    else:
        print("No domains matched the pattern.")
