import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class InvariantMetrics:
    """
    Utilities for cross-experiment comparison and invariant scoring.
    """
    @staticmethod
    def feature_similarity(feat1, feat2):
        """
        Cosine similarity between two feature vectors.
        """
        v1 = np.array(list(feat1.values())).reshape(1, -1)
        v2 = np.array(list(feat2.values())).reshape(1, -1)
        return float(cosine_similarity(v1, v2)[0, 0])

    @staticmethod
    def correlation_profile(ts1, ts2):
        """
        Computes the correlation between two time series.
        """
        a = np.array(ts1).flatten()
        b = np.array(ts2).flatten()
        
        # Trim to same length
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]
        
        return float(np.corrcoef(a, b)[0, 1])

    @staticmethod
    def persistence_score(occurrences):
        """
        Heuristic for how 'invariant' a pattern is based on frequency.
        """
        return float(1.0 - np.exp(-0.5 * occurrences))
