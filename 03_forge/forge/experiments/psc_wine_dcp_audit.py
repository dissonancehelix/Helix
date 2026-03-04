import numpy as np
import pandas as pd
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from forge.experiments.dcp_logger import DcpLogger
import json
from pathlib import Path

"""
HELIX — WINE DCP AUDIT
Objective: Apply Decision-Compression Principle (DCP) to the Wine dataset GUBA components.

We test whether the 'Behaviorally Anchored' components in Wine are 
structurally compressed (low k_eff) or rely on high-dimensional curvature.
"""

class WineDCPAudit:
    def __init__(self, seed=42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.logger = DcpLogger("wine_dcp_audit")
        
        # Load and scale data
        data = load_wine()
        self.X = StandardScaler().fit_transform(data.data)
        self.y = data.target
        self.feature_names = data.feature_names

    def calculate_k_eff(self, model, x, eps=1e-3):
        """
        Calculates k_eff for a trained classifier's decision at point x.
        Using prediction probabilities as the q(x) function.
        """
        # We use the probability of the most likely class as our q(x)
        probs = model.predict_proba(x.reshape(1, -1))[0]
        qx = np.max(probs)
        
        grad = np.zeros_like(x)
        for i in range(len(x)):
            orig = x[i]
            x[i] = orig + eps
            qp_probs = model.predict_proba(x.reshape(1, -1))[0]
            qp = np.max(qp_probs)
            x[i] = orig
            grad[i] = np.abs(qp - qx) / eps
            
        sum_grad = np.sum(grad)
        if sum_grad < 1e-15:
            return 1.0
        sum_grad_sq = np.sum(grad**2)
        return float((sum_grad**2) / sum_grad_sq)

    def run_audit(self):
        print("--- HELIX WINE DCP AUDIT: START ---")
        
        # 1. PCA to find components
        pca = PCA()
        X_pca = pca.fit_transform(self.X)
        
        # 2. Train a base model on PCA space
        clf = RandomForestClassifier(n_estimators=100, random_state=self.seed)
        clf.fit(X_pca, self.y)
        
        # 3. Identify GUBA candidates (indices of components)
        # From previous RBIS runs, we know components 3-6 often fail PSC but hold signal.
        # We'll audit all components to find the 'compression' signature.
        
        n_components = X_pca.shape[1]
        
        for i in range(n_components):
            # Create a path along the i-th component axis
            # Move from -2.0 to 2.0 standard deviations
            mean_sample = np.mean(X_pca, axis=0)
            
            k_effs = []
            for val in np.linspace(-2.0, 2.0, 20):
                test_point = mean_sample.copy()
                test_point[i] = val
                k_eff = self.calculate_k_eff(clf, test_point)
                k_effs.append(k_eff)
            
            avg_k = np.mean(k_effs)
            min_k = np.min(k_effs)
            
            # Classification
            is_compressed = avg_k < (n_components / 2.0)
            status = "COMPRESSED" if is_compressed else "DISTRIBUTED"
            
            self.logger.log_row(
                component=i,
                variance_ratio=float(pca.explained_variance_ratio_[i]),
                avg_k_eff=float(avg_k),
                min_k_eff=float(min_k),
                status=status
            )
            
            print(f"Comp {i}: Var={pca.explained_variance_ratio_[i]:.4f}, Avg k_eff={avg_k:.2f} -> {status}")

        self.logger.save_report(
            summary_metrics={"total_components": n_components},
            config={"dataset": "wine", "model": "RandomForest"}
        )
        return True

if __name__ == "__main__":
    audit = WineDCPAudit()
    audit.run_audit()
