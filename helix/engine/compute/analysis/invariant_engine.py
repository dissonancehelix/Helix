import os
import json
from pathlib import Path
from core.analysis.feature_extractor import FeatureExtractor
from core.analysis.similarity_metrics import SimilarityMetrics
from core.analysis.pattern_store import PatternStore

class InvariantEngine:
    """
    Analyzes experiment artifacts to discover structural regularities.
    """
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        self.artifacts_dir = artifacts_dir
        self.similarity_threshold = 0.95

    def analyze_new_artifact(self, artifact_dir: str):
        """
        Main entry point for the discovery loop.
        """
        features = FeatureExtractor.extract_from_artifact(artifact_dir)
        if not features:
            return None
            
        print(f"[invariant_engine] Analyzing artifact for recurring patterns: {artifact_dir}")
        
        # Discover candidates by comparing with history
        candidates = self.discover_candidates(features, artifact_dir)
        
        for name, data in candidates.items():
            PatternStore.save_invariant(name, data)
            
        return candidates

    def discover_candidates(self, current_features, current_dir):
        """
        Compare current experiment with all previous ones.
        """
        candidates = {}
        all_artifacts = self._get_historical_artifacts()
        
        matches = []
        for other_dir in all_artifacts:
            if other_dir == current_dir:
                continue
            
            # Load historical features
            feat_path = os.path.join(other_dir, "feature_vector.json")
            if not os.path.exists(feat_path):
                # Try to extract on the fly if missing (lazy update)
                other_features = FeatureExtractor.extract_from_artifact(other_dir)
            else:
                with open(feat_path, "r") as f:
                    other_features = json.load(f)
            
            if not other_features:
                continue
                
            sim = SimilarityMetrics.cosine_similarity(current_features, other_features)
            if sim > self.similarity_threshold:
                matches.append({
                    "path": other_dir,
                    "similarity": sim,
                    "features": other_features
                })
        
        if len(matches) >= 2: # Threshold for 'recurring'
            # Heuristic naming for discovery
            target_name = os.path.basename(current_dir).split("_0")[0]
            candidate_name = f"invariant_{target_name}"
            
            domains = set()
            for m in matches:
                domains.add(m["path"].split("/")[1] if "/" in m["path"] else "unknown")
            
            candidates[candidate_name] = {
                "name": candidate_name,
                "occurrences": len(matches) + 1,
                "similarity_mean": sum(m["similarity"] for m in matches) / len(matches),
                "supporting_artifacts": [current_dir] + [m["path"] for m in matches],
                "confidence": min(0.99, 0.5 + (0.1 * len(matches))),
                "status": "candidate"
            }
            
        return candidates

    def _get_historical_artifacts(self):
        root = Path(self.artifacts_dir)
        if not root.exists():
            return []
        return [str(p) for p in root.iterdir() if p.is_dir()]
