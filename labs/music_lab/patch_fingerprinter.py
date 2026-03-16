import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from pathlib import Path
import json

class PatchFingerprinter:
    """
    Clusters patches across the entire corpus to identify shared instrument 'templates'.
    """
    def __init__(self, patches_dir: str):
        self.patches_dir = Path(patches_dir)
        
    def build_patch_clusters(self, n_clusters: int = 20):
        print(f"Building patch clusters from {self.patches_dir}...")
        
        all_patches = []
        for p_file in self.patches_dir.glob("*_patches.parquet"):
            df = pd.read_parquet(p_file)
            if not df.empty:
                # Column names represent register offsets. Ensure they are strings.
                df.columns = [str(c) for c in df.columns]
                all_patches.append(df)
        
        if not all_patches:
            return None
            
        full_df = pd.concat(all_patches).fillna(0)
        
        # We only cluster on the synthesis registers (30-B6)
        # Filter for standard YM2612 registers
        feature_cols = [c for c in full_df.columns if c.isdigit() and 48 <= int(c) <= 182] # 0x30 to 0xB6
        
        X = full_df[feature_cols].values
        
        print(f"Clustering {len(X)} patch instances...")
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42)
        full_df['cluster_id'] = kmeans.fit_predict(X)
        
        # Save cluster definitions (centers)
        centers = kmeans.cluster_centers_
        cluster_defs = {}
        for i, center in enumerate(centers):
            cluster_defs[i] = {feature_cols[j]: float(center[j]) for j in range(len(feature_cols))}
            
        return full_df, cluster_defs

def run_patch_clustering():
    PATCHES_DIR = "/home/dissonance/Helix/artifacts/music_lab/patches"
    OUTPUT_PATH = "/home/dissonance/Helix/artifacts/music_lab/patches/patch_clusters.json"
    
    fp = PatchFingerprinter(PATCHES_DIR)
    results = fp.build_patch_clusters()
    if results:
        df, cluster_defs = results
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(cluster_defs, f, indent=2)
        print(f"Discovered {len(cluster_defs)} instrument templates.")
        
if __name__ == "__main__":
    run_patch_clustering()
