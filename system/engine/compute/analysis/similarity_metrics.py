import numpy as np

class SimilarityMetrics:
    """
    Computes similarity between high-dimensional feature vectors.
    """
    
    @staticmethod
    def cosine_similarity(v1: dict, v2: dict) -> float:
        # Get common keys
        keys = sorted(list(set(v1.keys()) & set(v2.keys())))
        if not keys:
            return 0.0
            
        a = np.array([v1[k] for k in keys])
        b = np.array([v2[k] for k in keys])
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def euclidean_distance(v1: dict, v2: dict) -> float:
        keys = sorted(list(set(v1.keys()) & set(v2.keys())))
        if not keys:
            return 1.0 # Max distance
            
        a = np.array([v1[k] for k in keys])
        b = np.array([v2[k] for k in keys])
        
        return float(np.linalg.norm(a - b))
