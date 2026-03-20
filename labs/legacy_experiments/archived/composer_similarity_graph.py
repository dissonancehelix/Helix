"""
composer_similarity_graph — Helix Music Lab
===========================================
Generates a similarity graph of composers based on style vector distance.
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from domains.music.config import COMPOSER_PROFILES_PATH, ARTIFACTS
from domains.music.similarity.composer_similarity import ComposerProfiler
import networkx as nx

def run(threshold: float = 0.8, **kwargs):
    print("--- Running composer_similarity_graph experiment ---")
    
    profiler = ComposerProfiler()
    if not Path(COMPOSER_PROFILES_PATH).exists():
        print("Error: No composer profiles found. Run composer_style_space first.")
        return
        
    profiler.load(COMPOSER_PROFILES_PATH)
    
    # 1. Build Similarity Matrix
    G = nx.Graph()
    composers = profiler.list_composers()
    for i, c1 in enumerate(composers):
        G.add_node(c1)
        for c2 in composers[i+1:]:
            sim = profiler.cosine_similarity(c1, c2)
            if sim >= threshold:
                G.add_edge(c1, c2, weight=float(sim))
    
    # 2. Store graph in artifacts
    output_path = ARTIFACTS / "music_lab" / "composer_similarity.graphml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, str(output_path))
    
    print(f"Stored similarity graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges in {output_path}")
    print("--- composer_similarity_graph complete ---")

if __name__ == "__main__":
    run()
