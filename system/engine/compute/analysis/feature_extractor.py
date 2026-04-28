import json
import os
import numpy as np

class FeatureExtractor:
    """
    Converts experiment outputs into comparable feature vectors.
    """
    
    @staticmethod
    def extract_from_artifact(artifact_dir: str) -> dict:
        results_path = os.path.join(artifact_dir, "results.json")
        if not os.path.exists(results_path):
            return {}
            
        try:
            with open(results_path, "r") as f:
                data = json.load(f)
        except Exception:
            return {}
            
        features = {}

        # Guard: results.json may be a list in legacy artifacts
        if not isinstance(data, dict):
            return features

        # Extract basic statistics from numeric results
        numeric_values = []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (int, float)):
                    features[f"val_{k}"] = float(v)
                    numeric_values.append(v)
                elif isinstance(v, list) and all(isinstance(x, (int, float)) for x in v):
                    features[f"mean_{k}"] = float(np.mean(v)) if v else 0.0
                    features[f"var_{k}"] = float(np.var(v)) if v else 0.0
                    features[f"max_{k}"] = float(np.max(v)) if v else 0.0
                    numeric_values.extend(v)
        
        if numeric_values:
            features["global_mean"] = float(np.mean(numeric_values))
            features["global_variance"] = float(np.var(numeric_values))
            features["global_max"] = float(np.max(numeric_values))
            features["entropy"] = float(FeatureExtractor._estimate_entropy(numeric_values))
            
        # Spatial features (Godot)
        if isinstance(data, dict) and data.get("substrate") == "godot_spatial":
            features["is_spatial"] = 1.0
            if "agent_count" in data:
                features["density"] = float(data["agent_count"]) # proxy
            if "spatial_sync" in data:
                features["sync_index"] = float(data["spatial_sync"])
                
        # Save feature vector
        FeatureExtractor._save_features(artifact_dir, features)
        
        return features

    @staticmethod
    def _estimate_entropy(values):
        if not values: return 0
        counts = np.histogram(values, bins=10)[0]
        probs = counts / np.sum(counts)
        probs = probs[probs > 0]
        return -np.sum(probs * np.log2(probs))

    @staticmethod
    def _save_features(artifact_dir, features):
        path = os.path.join(artifact_dir, "feature_vector.json")
        with open(path, "w") as f:
            json.dump(features, f, indent=4)
