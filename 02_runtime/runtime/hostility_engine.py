import numpy as np
import json
from pathlib import Path
from sklearn.preprocessing import StandardScaler, MinMaxScaler, normalize
from sklearn.metrics import accuracy_score

class HostilityEngine:
    def __init__(self, random_state=42):
        self.rng = np.random.RandomState(random_state)
        
    def _apply_scaling(self, X):
        return [
            StandardScaler().fit_transform(X),
            MinMaxScaler().fit_transform(X),
            normalize(X, norm='l2')
        ]
        
    def _apply_rotation(self, X, trials=5):
        rotations = []
        d = X.shape[1]
        for _ in range(trials):
            # Generate random orthogonal matrix via QR decomposition
            H = self.rng.randn(d, d)
            Q, R = np.linalg.qr(H)
            rotations.append(X @ Q)
        return rotations
        
    def _apply_dropout(self, X, rates=[0.1, 0.2]):
        dropouts = []
        for rate in rates:
            mask = self.rng.binomial(1, 1-rate, size=X.shape)
            dropouts.append(X * mask)
        return dropouts
        
    def _apply_noise(self, X, scales=[0.05, 0.10]):
        noises = []
        for scale in scales:
            noise = self.rng.normal(0, scale, size=X.shape)
            noises.append(X + noise)
        return noises
        
    def _apply_shuffle(self, X):
        X_shuffled = X.copy()
        for i in range(X.shape[1]):
            self.rng.shuffle(X_shuffled[:, i])
        return X_shuffled

    def testModelStability(self, model, X, y):
        base_pred = model.predict(X)
        base_acc = accuracy_score(y, base_pred)
        
        # Test scales
        scale_accs = [accuracy_score(y, model.predict(Xs)) for Xs in self._apply_scaling(X)]
        # Test rotations
        rot_accs = [accuracy_score(y, model.predict(Xr)) for Xr in self._apply_rotation(X)]
        # Test dropout
        drop_accs = [accuracy_score(y, model.predict(Xd)) for Xd in self._apply_dropout(X)]
        # Test noise
        noise_accs = [accuracy_score(y, model.predict(Xn)) for Xn in self._apply_noise(X)]
        # Test null
        null_acc = accuracy_score(y, model.predict(self._apply_shuffle(X)))
        
        all_accs = scale_accs + rot_accs + drop_accs + noise_accs
        
        # Calculate metrics
        pss = np.mean(all_accs) / base_acc if base_acc > 0 else 0  # Projection Stability Score
        bas = np.min(all_accs) / base_acc if base_acc > 0 else 0   # Bound Adversarial Survival
        csi = max(0, 1.0 - np.std(all_accs))                       # Constraint Satisfaction Index
        
        # Fragility gradient: (base - worst) / base
        fragility_gradient = (base_acc - np.min(all_accs)) / base_acc if base_acc > 0 else 0
        
        # Null delta
        null_delta = base_acc - null_acc
        
        # Bootstrap CI (simple percentile of our trials)
        bootstrap_ci = [np.percentile(all_accs, 5), np.percentile(all_accs, 95)]
        
        return {
            "PSS": float(pss),
            "BAS": float(bas),
            "CSI": float(csi),
            "fragility_gradient": float(fragility_gradient),
            "null_delta": float(null_delta),
            "bootstrap_ci": [float(bootstrap_ci[0]), float(bootstrap_ci[1])]
        }

    def generate_report(self, dest_dir: Path, metrics: dict):
        dest_dir.mkdir(parents=True, exist_ok=True)
        report_path = dest_dir / "hostility_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)
        return report_path
