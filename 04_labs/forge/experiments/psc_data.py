import numpy as np

def generate_synthetic_embedding(n=1000, d=50, intrinsic_rank=5, noise_lvl=0.1):
    U = np.random.randn(n, intrinsic_rank)
    V = np.random.randn(intrinsic_rank, d)
    X = U @ V
    noise = np.random.normal(0, noise_lvl, (n, d))
    return X + noise
