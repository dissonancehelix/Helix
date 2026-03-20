import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

class ComposerAttributionEngine:
    """
    Ranks composer candidates for tracks based on stylistic similarity.
    Focuses on SMPS composers for Sonic 3 & Knuckles.
    """
    
    def __init__(self, signals_path: str, attributions_path: str):
        self.df = pd.read_parquet(signals_path)
        with open(attributions_path, 'r') as f:
            self.known = json.load(f)
            
        # Features for similarity
        self.feature_cols = [
            "mean_algorithm", "algo_entropy", "pcm_weight", "rhythm_entropy",
            "algo_0_ratio", "algo_1_ratio", "algo_2_ratio", "algo_3_ratio",
            "algo_4_ratio", "algo_5_ratio", "algo_6_ratio", "algo_7_ratio"
        ]

    def build_composer_references(self) -> Dict[str, np.ndarray]:
        """
        Creates a 'mean vector' for each known composer.
        """
        refs = {}
        for game, tracks in self.known.items():
            for track, composer in tracks.items():
                target_df = self.df[self.df['track'] == track]
                if not target_df.empty:
                    vec = target_df[self.feature_cols].values[0]
                    if composer not in refs:
                        refs[composer] = []
                    refs[composer].append(vec)
        
        # Average vectors per composer
        final_refs = {c: np.mean(vlist, axis=0) for c, vlist in refs.items()}
        return final_refs

    def analyze_track_similarity(self, track_name: str, references: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        target_df = self.df[self.df['df' == track_name]] if track_name in self.df['track'].values else self.df[self.df['track'].str.contains(track_name)]
        
        if target_df.empty: return []
        
        vec = target_df[self.feature_cols].values[0].reshape(1, -1)
        rankings = []
        
        for composer, ref_vec in references.items():
            sim = cosine_similarity(vec, ref_vec.reshape(1, -1))[0][0]
            rankings.append({"composer": composer, "similarity": float(sim)})
            
        return sorted(rankings, key=lambda x: x['similarity'], reverse=True)

    def generate_report(self, output_path: str):
        references = self.build_composer_references()
        all_rankings = []
        
        # Analyze all tracks in Sonic 3 & Knuckles
        s3k_tracks = self.df[self.df['engine'] == 'SMPS']['track'].values
        
        lines = ["# Sonic 3 & Knuckles: Composer Style Similarity Analysis", ""]
        lines.append("| Track | Top Candidate | Similarity | 2nd Candidate | Similarity |")
        lines.append("|-------|---------------|------------|---------------|------------|")
        
        for track in s3k_tracks:
            ranks = self.analyze_track_similarity(track, references)
            if len(ranks) >= 2:
                lines.append(f"| {track} | {ranks[0]['composer']} | {ranks[0]['similarity']:.3f} | {ranks[1]['composer']} | {ranks[1]['similarity']:.3f} |")
                
        with open(output_path, 'w') as f:
            f.write("\n".join(lines))
        print(f"Report generated: {output_path}")

if __name__ == "__main__":
    SIGNALS = "/home/dissonance/Helix/artifacts/music_lab/composer_style_signals/unified_style_signals.parquet"
    KNOWN = "/home/dissonance/Helix/labs/music_lab/metadata/known_attributions.json"
    REPORT = "/home/dissonance/Helix/reports/sonic3_style_similarity.md"
    
    engine = ComposerAttributionEngine(SIGNALS, KNOWN)
    engine.generate_report(REPORT)
