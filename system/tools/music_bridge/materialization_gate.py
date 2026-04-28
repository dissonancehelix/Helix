"""
materialization_gate.py — Phase 12.5: Formal Materialization Policy and Gate.

This module determines if a candidate is safe to persist in the permanent Alias Graph
based on its audited precision class and tier.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from .alias_graph import Candidate, AliasGraph

ROOT = Path(__file__).resolve().parents[3]
GATE_POLICY_PATH = ROOT / "reports" / "music" / "bridge" / "materialization_gate_policy.json"

class MaterializationGate:
    """Gatekeeper for promoting candidates to permanent graph truth."""
    
    def __init__(self, audit_results: dict):
        self.audit_results = audit_results
        self.policy = {
            "release": "SAFE_IF_TIER_A",
            "artist": "SAFE_IF_TIER_A",
            "curated_subset": "SAFE_IF_TIER_A_AND_OVERLAP_80",
            "folder_recovery": "REVIEW_ONLY"
        }

    def is_safe(self, candidate: Candidate) -> bool:
        """Apply the gate policy to a candidate."""
        
        # 1. Tier D is always rejected
        if candidate.tier == "TIER_D":
            return False
            
        category = "release"
        if "folder recovery" in candidate.provenance.lower():
            category = "folder_recovery"
        elif candidate.match_category == "CURATED_SUBSET_MATCH":
            category = "curated_subset"
            
        policy_mode = self.policy.get(category, "REVIEW_ONLY")
        
        # 2. Hard Blocks
        if policy_mode == "REVIEW_ONLY":
            return False
            
        # 3. Mode Evaluation
        if policy_mode == "SAFE_IF_TIER_A":
            return candidate.tier == "TIER_A"
            
        if policy_mode == "SAFE_IF_TIER_A_AND_OVERLAP_80":
            return candidate.tier == "TIER_A" and candidate.evidence.track_count_overlap >= 0.8
            
        return False

    def save_policy(self):
        GATE_POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(GATE_POLICY_PATH, "w") as f:
            json.dump({
                "mode": "Phase 12.5 Audit Controlled",
                "gate_policy": self.policy,
                "audit_basis": self.audit_results
            }, f, indent=2)

def materialize_safe_candidates(candidates: List[Candidate], graph: AliasGraph, audit_results: dict):
    """
    Perform selective materialization only for candidates that pass the gate.
    """
    gate = MaterializationGate(audit_results)
    gate.save_policy()
    
    materialized_count = 0
    for c in candidates:
        if gate.is_safe(c):
            if graph.materialize_candidate(c):
                materialized_count += 1
                
    return materialized_count

