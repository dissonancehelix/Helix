import json
from pathlib import Path

def generate_graph(domain_id: str, artifacts_dir: Path, out_dir: Path):
    """
    Generates a Mermaid.js diagram tracing the Epistemic path for a given domain
    from L1 Phenomenon through L4 Operator.
    """
    print(f"Generating Epistemic Graph for: {domain_id}")
    
    # Simple struct to hold traces we find
    trace = {
        "status": "UNKNOWN",
        "risk": 0,
        "beam": None,
        "kernel": None
    }
    
    # 1. Check L1 Risk
    risk_file = artifacts_dir / "risk" / "risk_scores.json"
    if risk_file.exists():
        with open(risk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if domain_id in data.get("domains", {}):
                trace["risk"] = data["domains"][domain_id]
                trace["status"] = "SURVIVED L1" if trace["risk"] == 0 else "COLLAPSED (L1)"
                
    # 2. Check L2 Beams
    beam_file = artifacts_dir / "eigenspace" / "baseline_beams_v2.json"
    if beam_file.exists():
        with open(beam_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if domain_id in data.get("dataset_vector", {}):
                trace["beam"] = data["dataset_vector"][domain_id]
                trace["status"] = "COMPRESSED L2" if trace["status"] != "COLLAPSED (L1)" else trace["status"]

    out_file = out_dir / f"{domain_id}_graph.md"
    
    mermaid = ["```mermaid", "graph TD"]
    mermaid.append(f"  classDef default fill:#1E1E1E,stroke:#333,stroke-width:2px,color:#fff;")
    mermaid.append(f"  classDef collapsed fill:#8b0000,stroke:#f00,stroke-width:2px,color:#fff;")
    mermaid.append(f"  classDef success fill:#006400,stroke:#0f0,stroke-width:2px,color:#fff;")
    
    mermaid.append(f"  A[Domain: {domain_id}] --> B(L1 Phenomena Trace)")
    
    if trace["status"] == "COLLAPSED (L1)":
        mermaid.append(f"  B -->|Risk: {trace['risk']}| C[COLLAPSED]")
        mermaid.append(f"  class C collapsed;")
    elif trace["status"] == "UNKNOWN":
        mermaid.append(f"  B --> C[NOT FOUND IN PIPELINE]")
    else:
        mermaid.append(f"  B -->|Risk: 0| D(L2 Eigenspace Vectors)")
        if trace["beam"]:
            mermaid.append(f"  D -->|Mapped| E[C1-C4 Coordinates: {trace['beam']}]")
            mermaid.append(f"  E --> F(L4 Operator Collapse Check)")
            mermaid.append(f"  F --> G[VALIDATED COMPRESSION]")
            mermaid.append(f"  class G success;")
        else:
            mermaid.append(f"  D --> E[L2 MAPPING FAILED]")
            mermaid.append(f"  class E collapsed;")
            
    mermaid.append("```")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(mermaid) + "\n")
        
    print(f"Graph generated at {out_file}")
