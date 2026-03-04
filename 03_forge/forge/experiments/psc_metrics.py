import numpy as np
from sklearn.neighbors import NearestNeighbors

def compute_knn_overlap(X1, X2, k=20):
    nn1 = NearestNeighbors(n_neighbors=k+1).fit(X1)
    nn2 = NearestNeighbors(n_neighbors=k+1).fit(X2)
    
    indices1 = nn1.kneighbors(X1, return_distance=False)[:, 1:]
    indices2 = nn2.kneighbors(X2, return_distance=False)[:, 1:]
    
    overlaps = []
    for i in range(len(X1)):
        set1 = set(indices1[i])
        set2 = set(indices2[i])
        overlaps.append(len(set1.intersection(set2)) / k)
    return float(np.mean(overlaps))

def resolve_sign_ambiguity(V_base, V_new):
    signs = np.sign(np.sum(V_base * V_new, axis=1))
    return V_new * signs[:, np.newaxis]
