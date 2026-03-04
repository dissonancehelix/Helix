import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from scipy.stats import ortho_group

def get_transforms(seed):
    return {
        "T_scale": lambda X: StandardScaler().fit_transform(X),
        "T_minmax": lambda X: MinMaxScaler().fit_transform(X),
        "T_noise": lambda X: X + np.random.normal(0, 0.02, X.shape),
        "T_dropout": lambda X: X * (np.random.rand(*X.shape) > 0.1),
        "T_rotate": lambda X: X @ ortho_group.rvs(dim=X.shape[1], random_state=seed)
    }
