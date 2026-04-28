import os
import json
import numpy as np
import networkx as nx
from core.python_suite.networks import graph_models
from core.python_suite.analysis.feature_extractor import FeatureExtractor

def run_consensus(n_nodes=20, p=0.3, steps=100):
    print(f"Running Network Consensus Experiment: N={n_nodes}, p={p}")
    
    # 1. Generate Network
    adj = graph_models.generate_small_world(n_nodes, k=4, p=p)
    
    # 2. Simple Linear Consensus Dynamics
    # x(t+1) = W * x(t)
    # where W is based on adjacency
    Deg = np.diag(np.sum(adj, axis=1))
    L = Deg - adj
    # Discrete time Perron matrix
    eps = 0.1
    W = np.eye(n_nodes) - eps * L
    
    # Initial state
    x = np.random.randn(n_nodes)
    history = [x.copy()]
    
    for _ in range(steps):
        x = W @ x
        history.append(x.copy())
        
    history = np.array(history)
    
    # 3. Analyze
    # Consensus measure: variance of states (should go to 0)
    variances = np.var(history, axis=1)
    
    features = {
        "network_metrics": graph_models.get_network_metrics(adj),
        "final_variance": float(variances[-1]),
        "convergence_step": FeatureExtractor.convergence_time(variances, threshold=1e-5)
    }
    
    # 4. Save Artifact
    artifact_dir = f"artifacts/network_consensus_{int(np.random.rand()*1000)}"
    os.makedirs(artifact_dir, exist_ok=True)
    
    # Parameters
    with open(os.path.join(artifact_dir, "parameters.json"), "w") as f:
        json.dump({"n": n_nodes, "p": p, "steps": steps}, f, indent=2)
        
    # Metadata
    with open(os.path.join(artifact_dir, "metadata.json"), "w") as f:
        json.dump({
            "experiment": "network_consensus",
            "features": features
        }, f, indent=2)
        
    print(f"Consensus experiment complete: {artifact_dir}")
    return artifact_dir

def run(params: dict = None) -> dict:
    """HSL-compatible entry point: RUN experiment:network_consensus engine:python"""
    params = params or {}
    n_nodes = int(params.get("n", 20))
    p       = float(params.get("p", 0.3))
    steps   = int(params.get("steps", 100))
    artifact_dir = run_consensus(n_nodes=n_nodes, p=p, steps=steps)
    return {"artifact_dir": artifact_dir, "status": "ok"}


if __name__ == "__main__":
    run_consensus()
