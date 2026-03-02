import json
from pathlib import Path

def find_isomorphisms(artifacts_dir: Path, target_domain: str, top_k: int = 5):
    """
    Computes structural distance between datasets across L2 eigenspace artifacts
    to identify formal analogs (Isomorphism).
    """
    beam_file = artifacts_dir / "eigenspace" / "baseline_beams_v2.json"
    if not beam_file.exists():
        print("Artifacts missing. Run pipeline first.")
        return

    with open(beam_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    dataset_vector = data.get("dataset_vector", {})
    if target_domain not in dataset_vector:
        print(f"Domain '{target_domain}' not found in L2 artifacts.")
        return
        
    target_vec = dataset_vector[target_domain]
    
    print(f"--- Epistemic Isomorphism Report ---")
    print(f"Target: {target_domain}")
    print(f"Signature Vector: {target_vec}\n")
    
    # Calculate simple Manhattan distance between discrete vectors
    distances = []
    for domain, vec in dataset_vector.items():
        if domain == target_domain:
            continue
            
        # Ensure vectors are same length
        if len(vec) != len(target_vec):
            continue
            
        dist = sum(abs(a - b) for a, b in zip(vec, target_vec))
        distances.append((dist, domain, vec))
        
    # Sort by distance (lowest is most similar)
    distances.sort(key=lambda x: x[0])
    
    print(f"Top {top_k} Structural Analogs:")
    matches = 0
    for dist, domain, vec in distances[:top_k]:
        # Convert distance to a rough similarity percentage (heuristic based on typical vector magnitude)
        max_possible_dist = len(vec) * 2  # Assuming values mostly -1 to 1
        sim_pct = max(0, 100 - (dist / max_possible_dist * 100))
        
        match_level = "HIGH" if sim_pct >= 85 else ("MEDIUM" if sim_pct >= 60 else "LOW")
        print(f"{matches+1}. {domain}")
        print(f"   Similarity: {sim_pct:.1f}% [{match_level} Match]")
        print(f"   Signature:  {vec}\n")
        matches += 1
