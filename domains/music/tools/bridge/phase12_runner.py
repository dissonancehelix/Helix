"""
phase12_runner.py — Execute Phase 12: Conservative Alias Graph and Resolution.

Usage:
  python -m domains.music.tools.bridge.phase12_runner
"""
import json
import time
from pathlib import Path
from datetime import datetime, timezone

from domains.music.tools.bridge.alias_graph import AliasGraph, seed_from_codex
from domains.music.tools.bridge.metadata_adapter import MetadataAdapter
from domains.music.tools.bridge.candidate_engine import CandidateGenerationEngine
from domains.music.tools.bridge.review_queue import ReviewQueue

def run_phase12():
    print("=== Helix Music Phase 12: Conservative Alias Graph and Resolution ===")
    
    # 1. Initialize core graph and seed from codex
    graph = AliasGraph()
    n_seeded = seed_from_codex(graph)
    print(f"[*] Seeded {n_seeded} entities from existing codex.")
    
    # 2. Initialize adapters and engines
    meta = MetadataAdapter()
    engine = CandidateGenerationEngine(meta, graph)
    queue = ReviewQueue()
    
    if not meta.is_available():
        print("[!] external-tags.db unavailable. Skipping full library scan.")
        return

    # 3. Step A: Group library by release/album
    print("[*] Loading library from external-tags.db...")
    lib = meta.library()
    by_album = engine._group_by_album(lib)
    print(f"[*] Found {len(by_album)} unique releases in library.")

    # 4. Step B: Generate candidates (limit to sample for safety in initial run)
    print("[*] Generating candidates for curated library...")
    all_candidates = []
    processed_count = 0
    accepted_count = 0
    review_count = 0
    rejected_count = 0
    
    # We sample a few famous franchises to demonstrate logic
    limit = 100
    for album_name, tracks in list(by_album.items())[:limit]:
        processed_count += 1
        candidates = engine.generate_for_album(album_name, tracks)
        
        for c in candidates:
            all_candidates.append(c)
            if c.tier == "TIER_A":
                if graph.materialize_candidate(c):
                    accepted_count += 1
            elif c.tier in ("TIER_B", "TIER_C"):
                queue.add(c)
                review_count += 1
            else:
                rejected_count += 1

    # 5. Save results
    print(f"[*] Done. Processed {processed_count} albums.")
    print(f"[*] Result: {accepted_count} Auto-Accepted, {review_count} in Review Queue, {rejected_count} Rejected.")
    
    graph.save()
    queue.save()
    
    # 6. Generate reports
    _generate_phase12_reports(all_candidates, n_seeded, accepted_count, review_count)

def _generate_phase12_reports(candidates, seeded, accepted, review):
    reports_dir = Path(__file__).resolve().parents[3] / "reports" / "music" / "bridge"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Summary JSON
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entities_seeded": seeded,
        "albums_processed": len(candidates),
        "auto_accepted_links": accepted,
        "review_queue_count": review,
        "policy": "Phase 12 Conservative (Missing Better Than Wrong)"
    }
    
    with open(reports_dir / "phase12_executive_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    # Full candidate report (samples)
    sample_report = [c.to_dict() for c in candidates[:50]]
    with open(reports_dir / "phase12_candidate_report.json", "w") as f:
        json.dump(sample_report, f, indent=2)

    print(f"[*] Phase 12 reports generated in {reports_dir}")

if __name__ == "__main__":
    run_phase12()

