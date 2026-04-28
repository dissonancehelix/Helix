"""
Motif Discovery Pipeline (Phase 12)
=====================================
Detects recurring melodic motifs across symbolic scores,
clusters them, and assigns them to ArtistStyleVectors.
"""

import json
from pathlib import Path
from collections import defaultdict
import numpy as np
try:
    from sklearn.cluster import DBSCAN
except ImportError:
    pass

class MotifDiscoverer:
    def __init__(self, window_sizes=(3, 4, 5, 6, 7, 8, 9, 10, 11, 12)):
        self.window_sizes = window_sizes
        self.motifs = {}
        self.cluster_labels = []
        self.relationships = []
        self.lineages = []
        
    def _encode_sequence(self, pitches, durations):
        # Step 3 — canonical motif encoding
        # Interval sequence
        intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
        # Rhythmic ratio sequence
        # Avoid division by zero
        ratios = [round(durations[i+1] / (durations[i] + 1e-9), 2) for i in range(len(durations)-1)]
        return tuple(intervals), tuple(ratios)

    def extract_candidates(self, score) -> dict:
        """Step 2 — sliding window extraction"""
        candidates = defaultdict(list)
        # Using a simplified single melody line for now
        # Assuming score has access to linear pitch/duration lists
        if not hasattr(score, "pitches") or not hasattr(score, "durations"):
            return {}
            
        pitches = score.pitches
        durations = score.durations
        
        for w in self.window_sizes:
            for i in range(len(pitches) - w + 1):
                p_win = pitches[i:i+w]
                d_win = durations[i:i+w]
                intervals, ratios = self._encode_sequence(p_win, d_win)
                candidates[(intervals, ratios)].append(i) # save positions
                
        return candidates

    def similarity_detection_and_clustering(self, all_candidates: dict):
        """Step 4 & 5 — similarity detection and clustering"""
        # For simplicity in this architectural stub, we rely on exact hashing (already done via dict keys)
        # and simple thresholding. In a real system, DTW/edit distance + DBSCAN is used.
        keys = list(all_candidates.keys())
        # Placeholder for DBSCAN: group motifs that appear > N times
        clusters = {}
        motif_id_counter = 0
        for k in keys:
            if len(all_candidates[k]) >= 3: # Min support
                motif_id = f"motif_{motif_id_counter}"
                motif_id_counter += 1
                clusters[motif_id] = {
                    "interval_pattern": list(k[0]),
                    "rhythmic_pattern": list(k[1]),
                    "occurrence_frequency": len(all_candidates[k]),
                    "positions": all_candidates[k]
                }
        return clusters

    def detect_relationships(self, clusters: dict):
        """Step 3 — Detect motif evolutionary relationships and lineages."""
        # Simple simulated detection pass for demonstration
        motif_ids = list(clusters.keys())
        relationship_id_counter = 0
        lineage_id_counter = 0

        # Detect pairs of similar motifs for relationships
        for i, m1 in enumerate(motif_ids):
            for j, m2 in enumerate(motif_ids):
                if i >= j: continue
                # Simulated threshold check
                # In real code: check interval similarity, rhythmic similarity, DTW, edit distance
                p1 = clusters[m1]["interval_pattern"]
                p2 = clusters[m2]["interval_pattern"]
                # Arbitrary simple similarity proxy: same first interval or same sum
                if len(p1) > 0 and len(p2) > 0 and (p1[0] == p2[0] or sum(p1) == sum(p2)):
                    rel = {
                        "relationship_id": f"rel_{relationship_id_counter}",
                        "source_motif": m1,
                        "target_motif": m2,
                        "relationship_type": "variation", # rhythmic_shift, interval_shift, etc.
                        "similarity_score": 0.85,
                        "transformation_description": "Detected partial interval match"
                    }
                    self.relationships.append(rel)
                    relationship_id_counter += 1

                    lineage = {
                        "lineage_id": f"lineage_{lineage_id_counter}",
                        "motif_sequence": [m1, m2],
                        "lineage_length": 2,
                        "occurrence_count": clusters[m1]["occurrence_frequency"] + clusters[m2]["occurrence_frequency"]
                    }
                    self.lineages.append(lineage)
                    lineage_id_counter += 1

    def generate_artist_profile(self, clustered_motifs, track_owner_map):
        """Step 7 — artist motif profile"""
        artist_profiles = defaultdict(lambda: defaultdict(int))
        for motif_id, data in clustered_motifs.items():
            # In real system, map from positions back to tracks and then to artists
            # artist_profiles[artist_id][motif_id] += 1
            pass
        return dict(artist_profiles)

def run_motif_discovery(symbolic_scores: list, artifact_dir: str | None = None) -> dict:
    discoverer = MotifDiscoverer()
    all_candidates = defaultdict(list)
    for score in symbolic_scores:
        candidates = discoverer.extract_candidates(score)
        for k, v in candidates.items():
            all_candidates[k].extend(v)
            
    clusters = discoverer.similarity_detection_and_clustering(all_candidates)
    discoverer.detect_relationships(clusters)

    if artifact_dir:
        out_dir = Path(artifact_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "motif_relationships.json", "w") as f:
            json.dump(discoverer.relationships, f, indent=2)
        with open(out_dir / "motif_lineages.json", "w") as f:
            json.dump(discoverer.lineages, f, indent=2)

    return {
        "clusters": clusters,
        "relationships": discoverer.relationships,
        "lineages": discoverer.lineages
    }
