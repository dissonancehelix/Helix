import numpy as np
from scipy.stats import entropy as scipy_entropy

class FeatureExtractor:
    """
    Extracts structural and statistical features from experiment outputs.
    """
    @staticmethod
    def compute_stats(timeseries):
        # timeseries: (steps, n) or (steps,)
        data = np.array(timeseries)
        return {
            "mean": float(np.mean(data)),
            "variance": float(np.var(data)),
            "max": float(np.max(data)),
            "min": float(np.min(data))
        }

    @staticmethod
    def convergence_time(timeseries, threshold=0.01, window=10):
        """
        Estimates steps until the derivative stays below threshold.
        """
        data = np.array(timeseries)
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        
        diffs = np.abs(np.diff(data))
        for i in range(len(diffs) - window):
            if np.all(diffs[i:i+window] < threshold):
                return int(i)
        return len(data)

    @staticmethod
    def shannon_entropy(data, bins=10):
        hist, _ = np.histogram(data, bins=bins, density=True)
        return float(scipy_entropy(hist + 1e-9))

    @staticmethod
    def extract_all(results_dict):
        features = {}
        for key, value in results_dict.items():
            if isinstance(value, (list, np.ndarray)):
                features[f"{key}_stats"] = FeatureExtractor.compute_stats(value)
                features[f"{key}_entropy"] = FeatureExtractor.shannon_entropy(value)
        return features
