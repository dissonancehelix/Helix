import networkx as nx
import numpy as np

def generate_random_graph(n: int, p: float, seed: int = None):
    """Erdos-Renyi random graph."""
    G = nx.erdos_renyi_graph(n, p, seed=seed)
    return nx.to_numpy_array(G)

def generate_small_world(n: int, k: int, p: float, seed: int = None):
    """Watts-Strogatz small-world graph."""
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    return nx.to_numpy_array(G)

def generate_scale_free(n: int, m: int, seed: int = None):
    """Barabasi-Albert scale-free graph."""
    G = nx.barabasi_albert_graph(n, m, seed=seed)
    return nx.to_numpy_array(G)

def get_network_metrics(adj):
    G = nx.from_numpy_array(adj)
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": nx.density(G),
        "clustering": nx.average_clustering(G)
    }
