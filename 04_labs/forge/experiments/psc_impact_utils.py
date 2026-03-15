import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def compute_psc_per_component(X_raw, k=None, seed=42):
    if k is None:
        k = X_raw.shape[1]
    
    pca_base = PCA(n_components=k, random_state=seed).fit(X_raw)
    base_components = pca_base.components_
    base_var_shares = pca_base.explained_variance_ratio_
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    pca_scaled = PCA(n_components=k, random_state=seed).fit(X_scaled)
    scaled_components = pca_scaled.components_
    scaled_var_shares = pca_scaled.explained_variance_ratio_
    
    pss_scores = []
    
    for i in range(k):
        alignment = abs(np.dot(base_components[i], scaled_components[i]))
        drift = abs(base_var_shares[i] - scaled_var_shares[i])
        pss = alignment * (1.0 - drift)
        pss_scores.append(float(pss))
        
    return pss_scores

def generate_synthetic_rank_dataset(n=1000, d=10, intrinsic_rank=3, noise_lvl=0.05):
    U = np.random.randn(n, intrinsic_rank)
    V = np.random.randn(intrinsic_rank, d)
    X_low_rank = U @ V
    
    X_random = np.random.randn(n, 2)
    X = np.hstack([X_low_rank, X_random])
    
    y = (U[:, 0] + U[:, 1] > 0).astype(int)
    
    return X, y
