"""
phase12_5_runner.py — Execute Phase 12.5: Audit, Gate, and Selective Materialization.
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, "C:/Users/dissonance/Desktop/Helix")

from domains.music.bridge.alias_graph import AliasGraph, Candidate, Evidence, Contradiction
from domains.music.bridge.candidate_engine import AcceptancePolicy
from domains.music.bridge.audit_engine import AcceptanceAudit
from domains.music.bridge.materialization_gate import materialize_safe_candidates
from domains.music.bridge.review_queue import ReviewQueue

def run_phase12_5():
    print("=== Helix Music Phase 12.5: Acceptance Audit and Materialization Gate ===")
    
    # 1. Load Candidates (Hazardous sample)
    report_path = Path("C:/Users/dissonance/Desktop/Helix/domains/music/bridge/reports/phase12_candidate_report.json")
    with open(report_path, "r") as f:
        data = json.load(f)
        
    candidates = []
    for d in data:
        ev = Evidence(**d.pop("evidence"))
        co = Contradiction(**d.pop("contradictions"))
        c = Candidate(evidence=ev, contradictions=co, **d)
        candidates.append(c)

    # 2. Re-Evaluate Tiering with New Thresholds (Phase 12.5 improvement)
    print("[*] Re-evaluating candidates with tightened thresholds...")
    for c in candidates:
        AcceptancePolicy.evaluate(c)

    # 3. Perform Acceptance Audit
    print("[*] Performing acceptance audit...")
    audit = AcceptanceAudit(candidates)
    audit.perform_audit()
    metrics = audit.generate_report()
    
    # 4. Apply Materialization Gate
    print("[*] Applying materialization gate...")
    graph = AliasGraph()
    graph.load()
    materialized_count = materialize_safe_candidates(candidates, graph, metrics)
    
    # 5. Populate Review Queue with Upgraded Logic
    queue = ReviewQueue()
    for c in candidates:
        queue.add(c)
    
    # 6. Save State
    graph.save()
    queue.save()
    
    # 7. Generate Executive Summary
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "12.5 Audit Controlled",
        "audited_count": len(candidates),
        "tier_a_precision": metrics["tier_precision"].get("TIER_A", 0.0),
        "selective_materializations": materialized_count,
        "review_queue_size": queue.candidate_count,
        "policy": "Audited Gating Active"
    }
    
    summary_path = Path("C:/Users/dissonance/Desktop/Helix/domains/music/bridge/reports/phase12_5_executive_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"[*] Phase 12.5 complete. Materialized: {materialized_count} | Quality Gate: OK.")

if __name__ == "__main__":
    run_phase12_5()
