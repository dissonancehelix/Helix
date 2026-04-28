"""
audit_engine.py — Phase 12.5: Acceptance Audit Framework.

This engine measures the precision and recall risks of candidate matches.
It distinguishes between correct, ambiguous, and incorrect links by category.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from domains.music.tools.bridge.alias_graph import Candidate, Evidence, Contradiction

ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = ROOT / "reports" / "music" / "bridge"

@dataclass
class AuditRecord:
    """Audit judgment for a single candidate."""
    candidate_local_id: str
    candidate_external_id: str
    tier: str
    category: str  # "artist" | "release" | "curated_subset" | "folder_recovery"
    
    # Judgment
    status: str    # "correct" | "partially_correct" | "ambiguous" | "incorrect" | "insufficient_evidence"
    failure_pattern: Optional[str] = None # "generic_title" | "overreach" | "contradiction_escape" | etc.
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return self.__dict__

class AcceptanceAudit:
    """Framework to evaluate and label candidate quality."""
    
    def __init__(self, candidates: List[Candidate]):
        self.candidates = candidates
        self.audit_trail: List[AuditRecord] = []

    def perform_audit(self):
        """Perform simulated audit judgment based on known hazard patterns."""
        for c in self.candidates:
            category = "release"
            if "folder recovery" in c.provenance.lower():
                category = "folder_recovery"
            elif c.match_category == "CURATED_SUBSET_MATCH":
                category = "curated_subset"
            
            judgment = self._judge(c)
            record = AuditRecord(
                candidate_local_id=c.local_id,
                candidate_external_id=c.external_id,
                tier=c.tier,
                category=category,
                status=judgment["status"],
                failure_pattern=judgment.get("pattern"),
                notes=judgment.get("notes", "")
            )
            self.audit_trail.append(record)

    def _judge(self, c: Candidate) -> dict:
        """Mock auditor logic — identifies hazardous patterns in the synthetic data."""
        
        # Pattern 1: Generic Title Hazard
        if c.local_id.lower() in ("selection", "best of", "unknown"):
            return {
                "status": "incorrect", 
                "pattern": "generic_title_collision",
                "notes": "Title alone carries no authority for generic terms."
            }
            
        # Pattern 2: Folder Recovery Hazard (Generic folder names)
        if "folder recovery" in c.provenance.lower() and c.local_id.lower() in ("disk 1", "cd 1", "music"):
             return {
                "status": "incorrect", 
                "pattern": "folder_name_false_authority",
                "notes": "Folder-based recovery was too broad for generic numbering."
            }
            
        # Pattern 3: Curated Subset Overreach
        if c.match_category == "CURATED_SUBSET_MATCH" and c.evidence.track_count_overlap < 0.2:
            return {
                "status": "ambiguous", 
                "pattern": "curated_subset_overreach",
                "notes": "Insufficient track overlap (< 20%) to confirm identity."
            }
            
        # Pattern 4: Contradiction Escaped (Logic Failure)
        if c.contradictions.any() and c.tier == "TIER_A":
            return {
                "status": "incorrect", 
                "pattern": "contradiction_gate_failure",
                "notes": "Contradiction gate was explicitly triggered but TIER_A was assigned."
            }
            
        # Pattern 5: Positive Match
        if c.local_id == "Sonic the Hedgehog 3":
            return {"status": "correct"}
            
        return {"status": "insufficient_evidence"}

    def generate_report(self) -> dict:
        """Calculate metrics by category and tier."""
        metrics = {
            "global_precision": 0.0,
            "tier_precision": {},
            "category_precision": {},
            "patterns": {}
        }
        
        # Calculate counts
        correct = len([r for r in self.audit_trail if r.status == "correct"])
        total = len(self.audit_trail)
        if total > 0:
            metrics["global_precision"] = correct / total
            
        # Tiered precision
        tiers = set(r.tier for r in self.audit_trail)
        for tier in tiers:
            sample = [r for r in self.audit_trail if r.tier == tier]
            t_correct = len([r for r in sample if r.status == "correct"])
            metrics["tier_precision"][tier] = t_correct / len(sample) if sample else 0
            
        # Category precision
        cats = set(r.category for r in self.audit_trail)
        for cat in cats:
            sample = [r for r in self.audit_trail if r.category == cat]
            c_correct = len([r for r in sample if r.status == "correct"])
            metrics["category_precision"][cat] = c_correct / len(sample) if sample else 0
            
        # Pattern counts
        patterns = [r.failure_pattern for r in self.audit_trail if r.failure_pattern]
        for p in set(patterns):
            metrics["patterns"][p] = patterns.count(p)
            
        return metrics

def run_acceptance_audit():
    print("=== Helix Music Phase 12.5: Acceptance Audit Execution ===")
    
    # 1. Load candidates from Phase 12
    report_path = REPORTS_DIR / "phase12_candidate_report.json"
    if not report_path.exists():
        print("[!] No candidate report found. Run generate_audit_candidates.py first.")
        return
        
    with open(report_path, "r") as f:
        data = json.load(f)
        
    # Reconstruct Candidate objects
    candidates = []
    for d in data:
        ev = Evidence(**d.pop("evidence"))
        co = Contradiction(**d.pop("contradictions"))
        c = Candidate(evidence=ev, contradictions=co, **d)
        candidates.append(c)
        
    # 2. Run Audit
    audit = AcceptanceAudit(candidates)
    audit.perform_audit()
    
    # 3. Save Results
    results_dir = REPORTS_DIR / "audit"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    metrics = audit.generate_report()
    with open(results_dir / "tier_precision_report.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(results_dir / "acceptance_audit_report.json", "w") as f:
        json.dump([r.to_dict() for r in audit.audit_trail], f, indent=2)
        
    print(f"[*] Audit complete. Observed Precision (Tier A): {metrics['tier_precision'].get('TIER_A', 0.0):.1%}")
    print(f"[*] patterns discovered: {list(metrics['patterns'].keys())}")
    
if __name__ == "__main__":
    run_acceptance_audit()

