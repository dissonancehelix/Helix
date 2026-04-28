"""
music_profile_analysis.py
=========================
Deep structural analysis of Spotify favorites library.
Produces all deliverables into outputs/music_profile_analysis/

Run: python domains/music/model/probes/music_profile_analysis.py
"""
import json, csv, os, sys, warnings
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
JSON_PATH   = Path("domains/music/data/derived/music/metadata/spotify.json")
OUT_DIR     = Path("domains/music/model/outputs/music_profile_analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Audio feature columns available ──────────────────────────────────────────
AUDIO_COLS = [
    "Danceability","Energy","Loudness","Speechiness",
    "Acousticness","Instrumentalness","Liveness","Valence","Tempo"
]
NORM_COLS = [  # will be z-scored for clustering / PCA
    "Danceability","Energy","Speechiness",
    "Acousticness","Instrumentalness","Liveness","Valence",
    "Tempo_norm"   # tempo normalized 0-1 within dataset
]

# ═══════════════════════════════════════════════════════════════════════════
# 1. LOAD & FLATTEN
# ═══════════════════════════════════════════════════════════════════════════
print("Loading JSON…")
with open(JSON_PATH, encoding="utf-8") as f:
    raw = json.load(f)

df = pd.DataFrame(raw)
print(f"  {len(df)} tracks, {len(df.columns)} fields")
print(f"  Fields: {list(df.columns)}")

# Coerce all audio feature columns to numeric (some records may have string/null values)
for col in AUDIO_COLS + ["Key", "Mode", "Time Signature", "Popularity"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Parse dates
df["Added At"] = pd.to_datetime(df["Added At"], utc=True, errors="coerce")
df["Release Date"] = pd.to_datetime(df["Release Date"], errors="coerce")
df["add_year"] = df["Added At"].dt.year
df["release_year"] = df["Release Date"].dt.year
df["add_lag_years"] = df["add_year"] - df["release_year"]   # discovery lag

# Normalise tempo to [0,1]
df["Tempo_norm"] = (df["Tempo"] - df["Tempo"].min()) / (df["Tempo"].max() - df["Tempo"].min())

# Primary artist (first listed)
df["Primary Artist"] = df["Artist Name(s)"].str.split(",").str[0].str.strip()

# Mode label
df["Mode Label"] = df["Mode"].map({1: "major", 0: "minor"})

# Duration in minutes
df["Duration_min"] = df["Duration (ms)"] / 60000

# ═══════════════════════════════════════════════════════════════════════════
# 2. PCA — latent dimensions
# ═══════════════════════════════════════════════════════════════════════════
print("Running PCA…")
feat_df = df[NORM_COLS].dropna()
valid_idx = feat_df.index

scaler = StandardScaler()
X = scaler.fit_transform(feat_df)

pca = PCA(n_components=8, random_state=42)
pcs = pca.fit_transform(X)

pc_df = pd.DataFrame(pcs, index=valid_idx, columns=[f"PC{i+1}" for i in range(8)])
df = df.join(pc_df)

explained = pca.explained_variance_ratio_
print(f"  Variance explained by 8 PCs: {explained.sum()*100:.1f}%")

# PC loadings → dimension labels
loadings = pd.DataFrame(
    pca.components_,
    columns=NORM_COLS,
    index=[f"PC{i+1}" for i in range(8)]
)

# ═══════════════════════════════════════════════════════════════════════════
# 3. CLUSTERING (K-Means, k=7 after silhouette sweep)
# ═══════════════════════════════════════════════════════════════════════════
print("Clustering…")
pc_data = df[["PC1","PC2","PC3","PC4","PC5"]].dropna()
sil_scores = {}
for k in range(4, 13):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(pc_data)
    sil_scores[k] = silhouette_score(pc_data, labels)

best_k = max(sil_scores, key=sil_scores.get)
print(f"  Best k by silhouette: {best_k} ({sil_scores[best_k]:.3f})")

km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
df.loc[pc_data.index, "Cluster"] = km_final.fit_predict(pc_data)
df["Cluster"] = df["Cluster"].fillna(-1).astype(int)

# ── Cluster centroids in audio-feature space ─────────────────────────────
cluster_profiles = df.groupby("Cluster")[AUDIO_COLS].mean().round(3)

# ── Name clusters from their centroids ───────────────────────────────────
def name_cluster(row):
    e, d, v, a, ins, sp = (row["Energy"], row["Danceability"], row["Valence"],
                            row["Acousticness"], row["Instrumentalness"], row["Speechiness"])
    if ins > 0.5:
        if e > 0.6: return "Groove Engine (Instrumental)"
        return "Floating Instrumental / Ambient"
    if d > 0.70 and e > 0.65:
        if v > 0.55: return "High-Charge Dance / Pop"
        return "Dark Drive / Groove Engine"
    if e < 0.45 and v < 0.45:
        return "Suspended / Melancholic"
    if a > 0.35:
        if v > 0.50: return "Warm Acoustic / Folk-Adjacent"
        return "Quiet / Intimate Acoustic"
    if e > 0.70 and v < 0.40:
        return "Charged Tension / Cathartic"
    if v > 0.65 and e > 0.55:
        return "Bright / Authored Pop"
    if sp > 0.10:
        return "Lyric-Forward / Textural Rap"
    return "Mid-Field / Eclectic Core"

cluster_names = {i: name_cluster(cluster_profiles.loc[i])
                 for i in cluster_profiles.index if i >= 0}
df["Cluster Name"] = df["Cluster"].map(cluster_names).fillna("Unassigned")

# ═══════════════════════════════════════════════════════════════════════════
# 4. ARTIST FINGERPRINT-WITH-RANGE
# ═══════════════════════════════════════════════════════════════════════════
print("Computing artist fingerprint-with-range…")
# min 3 tracks per artist
artist_counts = df["Primary Artist"].value_counts()
eligible = artist_counts[artist_counts >= 3].index

fingerprint_rows = []
library_centroid = df[AUDIO_COLS].mean()

for artist in eligible:
    sub = df[df["Primary Artist"] == artist][AUDIO_COLS].dropna()
    if len(sub) < 3:
        continue
    centroid = sub.mean()
    # distinctiveness: distance from library centroid (normalised)
    dist_from_lib = np.linalg.norm(
        (centroid - library_centroid) / (df[AUDIO_COLS].std() + 1e-9)
    )
    # internal range: mean std across features
    internal_range = sub.std().mean()
    fingerprint_score = 0.5 * dist_from_lib + 0.5 * internal_range
    fingerprint_rows.append({
        "Artist": artist,
        "Tracks": len(sub),
        "Distinctiveness": round(dist_from_lib, 3),
        "Internal Range": round(internal_range, 3),
        "Fingerprint Score": round(fingerprint_score, 3),
        **{f"mean_{c}": round(centroid[c], 3) for c in AUDIO_COLS}
    })

fp_df = pd.DataFrame(fingerprint_rows).sort_values("Fingerprint Score", ascending=False)

# ═══════════════════════════════════════════════════════════════════════════
# 5. CONTRADICTION FAMILIES
# ═══════════════════════════════════════════════════════════════════════════
print("Computing contradictions…")
contra = pd.DataFrame(index=df.index)
contra["major_low_valence"]     = (df["Mode"]==1) & (df["Valence"] < 0.35)
contra["danceable_dark"]        = (df["Danceability"] > 0.65) & (df["Valence"] < 0.35)
contra["energetic_melancholic"] = (df["Energy"] > 0.70) & (df["Valence"] < 0.35)
contra["instrumental_bright"]   = (df["Instrumentalness"] > 0.40) & (df["Valence"] > 0.65)
contra["acoustic_intense"]      = (df["Acousticness"] > 0.40) & (df["Energy"] > 0.70)
contra["fast_low_energy"]       = (df["Tempo"] > 130) & (df["Energy"] < 0.45)
contra["slow_high_energy"]      = (df["Tempo"] < 90) & (df["Energy"] > 0.70)

df = df.join(contra)
contra_counts = contra.sum().sort_values(ascending=False)

# ═══════════════════════════════════════════════════════════════════════════
# 6. CURRENT CORE vs DISCOVERY FOSSIL
# ═══════════════════════════════════════════════════════════════════════════
print("Core vs fossil split…")
# "Current core" = added in last 3 years or recency heuristic
# "Discovery fossil" = added early AND release predates add by many years
df["era_bucket"] = pd.cut(
    df["add_year"],
    bins=[2000, 2015, 2019, 2022, 2026],
    labels=["early (≤2015)", "mid (2016-2019)", "late (2020-2022)", "recent (2023+)"]
)

# Fossil = lag > 5 years AND added before 2018
fossil_mask = (df["add_lag_years"] > 5) & (df["add_year"] < 2018)
core_mask   = (df["add_year"] >= 2021)

df["temporal_class"] = "mid-era"
df.loc[fossil_mask, "temporal_class"] = "discovery-fossil"
df.loc[core_mask,   "temporal_class"] = "current-core"

core_profile  = df[core_mask][AUDIO_COLS].mean().round(3)
fossil_profile = df[fossil_mask][AUDIO_COLS].mean().round(3)

# ═══════════════════════════════════════════════════════════════════════════
# 7. OUTLIER DETECTION
# ═══════════════════════════════════════════════════════════════════════════
print("Finding outliers…")
# Distance from library centroid in PCA space
pca_centroid = df[["PC1","PC2","PC3"]].dropna().mean()
df["pca_dist"] = np.linalg.norm(
    df[["PC1","PC2","PC3"]].sub(pca_centroid),
    axis=1
)
outliers = df.nlargest(30, "pca_dist")[
    ["Track Name","Primary Artist","pca_dist","Danceability","Energy","Valence",
     "Acousticness","Instrumentalness","Tempo","Cluster Name"]
].round(3)

# ═══════════════════════════════════════════════════════════════════════════
# 8. PLOTS
# ═══════════════════════════════════════════════════════════════════════════
print("Generating plots…")
palette = cm.get_cmap("tab10", best_k)

# ── Plot 1: PCA cluster map ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 8))
plot_df = df.dropna(subset=["PC1","PC2","Cluster"])
for cid in sorted(plot_df["Cluster"].unique()):
    m = plot_df["Cluster"] == cid
    ax.scatter(plot_df.loc[m,"PC1"], plot_df.loc[m,"PC2"],
               c=[palette(int(cid))], label=f"{cid}: {cluster_names.get(int(cid),'?')}",
               alpha=0.55, s=18, linewidths=0)
ax.set_xlabel(f"PC1 ({explained[0]*100:.1f}% var)", fontsize=10)
ax.set_ylabel(f"PC2 ({explained[1]*100:.1f}% var)", fontsize=10)
ax.set_title("Library Cluster Map — PC1 vs PC2", fontsize=13)
ax.legend(fontsize=7, loc="upper right")
plt.tight_layout()
fig.savefig(OUT_DIR / "01_cluster_map.png", dpi=150)
plt.close()

# ── Plot 2: Silhouette sweep ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
ks = sorted(sil_scores)
ax.plot(ks, [sil_scores[k] for k in ks], "o-", color="#4c72b0")
ax.axvline(best_k, color="crimson", linestyle="--", label=f"Best k={best_k}")
ax.set_xlabel("Number of clusters k"); ax.set_ylabel("Silhouette score")
ax.set_title("Cluster quality sweep")
ax.legend(); plt.tight_layout()
fig.savefig(OUT_DIR / "02_silhouette_sweep.png", dpi=150)
plt.close()

# ── Plot 3: PCA loadings heatmap ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(loadings.values[:5], cmap="RdBu_r", vmin=-0.7, vmax=0.7, aspect="auto")
ax.set_xticks(range(len(NORM_COLS))); ax.set_xticklabels(NORM_COLS, rotation=40, ha="right", fontsize=9)
ax.set_yticks(range(5)); ax.set_yticklabels(
    [f"PC{i+1} ({explained[i]*100:.1f}%)" for i in range(5)], fontsize=9)
plt.colorbar(im, ax=ax)
ax.set_title("PCA Factor Loadings (top 5 components)", fontsize=12)
plt.tight_layout()
fig.savefig(OUT_DIR / "03_pca_loadings.png", dpi=150)
plt.close()

# ── Plot 4: Tempo × Energy scatter coloured by Valence ───────────────────
fig, ax = plt.subplots(figsize=(10, 7))
sc = ax.scatter(df["Tempo"], df["Energy"], c=df["Valence"],
                cmap="coolwarm_r", alpha=0.45, s=14, linewidths=0)
plt.colorbar(sc, ax=ax, label="Valence (low=dark, high=bright)")
ax.set_xlabel("Tempo (BPM)"); ax.set_ylabel("Energy")
ax.set_title("Tempo × Energy, coloured by Valence")
plt.tight_layout()
fig.savefig(OUT_DIR / "04_tempo_energy_valence.png", dpi=150)
plt.close()

# ── Plot 5: Add-year histogram ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4))
df["add_year"].dropna().astype(int).hist(bins=range(2012, 2027), ax=ax, color="#4c72b0", edgecolor="white")
ax.set_xlabel("Year added to library"); ax.set_ylabel("Track count")
ax.set_title("Library growth by year added")
plt.tight_layout()
fig.savefig(OUT_DIR / "05_add_year_histogram.png", dpi=150)
plt.close()

print("Plots saved.")

# ═══════════════════════════════════════════════════════════════════════════
# 9. CSV EXPORTS
# ═══════════════════════════════════════════════════════════════════════════
print("Writing CSVs…")
keep_cols = ["Track Name","Primary Artist","Album Name","Release Date","add_year",
             "Popularity","Danceability","Energy","Loudness","Speechiness",
             "Acousticness","Instrumentalness","Liveness","Valence","Tempo",
             "Mode Label","Duration_min","Genres","temporal_class","Cluster","Cluster Name","pca_dist"]
df[[c for c in keep_cols if c in df.columns]].to_csv(OUT_DIR / "tracks_flat.csv", index=False)

(df[["Track Name","Primary Artist","Cluster","Cluster Name"]]
 .dropna(subset=["Cluster"])
 .to_csv(OUT_DIR / "cluster_assignments.csv", index=False))

fp_df.to_csv(OUT_DIR / "artist_fingerprint_range.csv", index=False)
outliers.to_csv(OUT_DIR / "outliers.csv", index=False)

contra_export = df[["Track Name","Primary Artist"] + list(contra.columns)].copy()
contra_export["contradiction_flags"] = contra.apply(
    lambda r: "|".join(c for c in contra.columns if r[c]), axis=1)
contra_export[contra_export["contradiction_flags"] != ""].to_csv(
    OUT_DIR / "contradictions.csv", index=False)

print("CSVs written.")

# ═══════════════════════════════════════════════════════════════════════════
# 10. BUILD REPORT DATA
# ═══════════════════════════════════════════════════════════════════════════

# Top latent dimensions — describe each PC
def describe_pc(i):
    row = loadings.loc[f"PC{i+1}"]
    top_pos = row.nlargest(2).index.tolist()
    top_neg = row.nsmallest(2).index.tolist()
    return f"+{top_pos} / −{top_neg}"

dim_descriptions = {
    "PC1": ("Groove-Engine Charge", "High: energetic+danceable dance/groove. Low: quiet acoustic or ambient."),
    "PC2": ("Vocal Texture vs Instrumentalness", "High: speech-forward/vocal. Low: instrumental."),
    "PC3": ("Mood Polarity", "High: bright+valent. Low: dark/melancholic."),
    "PC4": ("Acoustic Warmth", "High: acoustic, low energy. Low: synthetic/loud."),
    "PC5": ("Liveness / Rawness", "High: live-sounding, low production polish."),
    "PC6": ("Tempo Axis", "High: fast. Low: slow/drag tempo."),
    "PC7": ("Danceability vs Energy decoupling", "Captures tracks that are danceable-but-calm or energetic-but-stiff."),
    "PC8": ("Residual / Niche texture", "Idiosyncratic variance not captured above."),
}

# Cluster summary
cluster_summary = []
for cid, name in cluster_names.items():
    sub = df[df["Cluster"]==cid]
    top_artists = sub["Primary Artist"].value_counts().head(5).index.tolist()
    row = cluster_profiles.loc[cid]
    cluster_summary.append({
        "id": int(cid),
        "name": name,
        "size": len(sub),
        "pct": round(100*len(sub)/len(df), 1),
        "energy": round(row["Energy"], 2),
        "danceability": round(row["Danceability"], 2),
        "valence": round(row["Valence"], 2),
        "acousticness": round(row["Acousticness"], 2),
        "instrumentalness": round(row["Instrumentalness"], 2),
        "tempo": round(row["Tempo"], 1),
        "top_artists": top_artists,
    })

# Core vs fossil comparison
core_vs_fossil = {
    "current_core_count": int(core_mask.sum()),
    "discovery_fossil_count": int(fossil_mask.sum()),
    "core_profile": core_profile.to_dict(),
    "fossil_profile": fossil_profile.to_dict(),
    "key_shift": {
        col: round(core_profile[col] - fossil_profile[col], 3)
        for col in AUDIO_COLS
    }
}

# Contradiction summary
contra_summary = {k: int(v) for k, v in contra_counts.items()}

# Top fingerprint artists
top_fp = fp_df.head(20)[["Artist","Tracks","Distinctiveness","Internal Range","Fingerprint Score"]].to_dict("records")

# ═══════════════════════════════════════════════════════════════════════════
# 11. WRITE JSON SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
summary = {
    "generated_at": datetime.now().isoformat(),
    "library_size": len(df),
    "fields_available": list(raw[0].keys()),
    "pca": {
        "n_components": 8,
        "variance_explained_pct": [round(e*100, 2) for e in explained],
        "dimensions": {
            f"PC{i+1}": {
                "variance_pct": round(explained[i]*100, 2),
                "label": dim_descriptions[f"PC{i+1}"][0],
                "description": dim_descriptions[f"PC{i+1}"][1],
                "top_positive_loadings": loadings.loc[f"PC{i+1}"].nlargest(3).to_dict(),
                "top_negative_loadings": loadings.loc[f"PC{i+1}"].nsmallest(3).to_dict(),
            }
            for i in range(8)
        }
    },
    "clustering": {
        "best_k": best_k,
        "silhouette_score": round(sil_scores[best_k], 3),
        "clusters": cluster_summary,
    },
    "core_vs_fossil": core_vs_fossil,
    "contradictions": contra_summary,
    "top_fingerprint_artists": top_fp,
    "top_outliers": outliers[["Track Name","Primary Artist","pca_dist"]].head(15).to_dict("records"),
}

with open(OUT_DIR / "music_profile_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, default=str)

print("JSON summary written.")

# ═══════════════════════════════════════════════════════════════════════════
# Print key stats inline so I can read them
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("CLUSTER SUMMARY")
print("="*70)
for c in cluster_summary:
    print(f"  [{c['id']}] {c['name']}")
    print(f"       n={c['size']} ({c['pct']}%)  E={c['energy']} D={c['danceability']} V={c['valence']} I={c['instrumentalness']}")
    print(f"       Top artists: {', '.join(c['top_artists'])}")
    print()

print("="*70)
print("TOP 15 FINGERPRINT-WITH-RANGE ARTISTS")
print("="*70)
print(fp_df[["Artist","Tracks","Distinctiveness","Internal Range","Fingerprint Score"]].head(15).to_string(index=False))

print("\n" + "="*70)
print("CONTRADICTION FAMILY SIZES")
print("="*70)
for k, v in contra_counts.items():
    print(f"  {k}: {v} tracks ({round(100*v/len(df),1)}%)")

print("\n" + "="*70)
print("CORE vs FOSSIL SHIFT (core - fossil)")
print("="*70)
for col, delta in core_vs_fossil["key_shift"].items():
    direction = "↑" if delta > 0.02 else ("↓" if delta < -0.02 else "~")
    print(f"  {col:20s} {direction}  {delta:+.3f}")

print("\n" + "="*70)
print("TOP 10 OUTLIERS (furthest from library centre)")
print("="*70)
print(outliers[["Track Name","Primary Artist","Cluster Name","pca_dist"]].head(10).to_string(index=False))

print(f"\nAll outputs written to: {OUT_DIR.resolve()}")

