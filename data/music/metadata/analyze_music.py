"""
Helix Music Cognition Analysis
================================
Analyzes Spotify favorites + Last.fm scrobble history to extract
structural patterns for cognitive mapping.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(r"C:\Users\dissonance\Desktop\Helix docs")

def num(track, key, default=0):
    v = track.get(key, default)
    if isinstance(v, (int, float)):
        return float(v)
    return default

def load_spotify():
    with open(DATA_DIR / "spotify favorites.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_lastfm():
    with open(DATA_DIR / "lastfmstats-dissident93.json", "r", encoding="utf-8") as f:
        return json.load(f)

def analyze():
    spotify = load_spotify()
    lastfm = load_lastfm()
    scrobbles = lastfm["scrobbles"]

    print(f"=== DATASET OVERVIEW ===")
    print(f"Spotify favorites: {len(spotify)} tracks")
    print(f"Last.fm scrobbles: {len(scrobbles)}")

    # --- Top Artists by Scrobble Count ---
    artist_counts = Counter(s["artist"] for s in scrobbles)
    print(f"\n=== TOP 50 ARTISTS (by scrobble count) ===")
    for artist, count in artist_counts.most_common(50):
        print(f"  {count:>5}  {artist}")

    # --- Top Tracks by Scrobble Count ---
    track_counts = Counter(f"{s['artist']} — {s['track']}" for s in scrobbles)
    print(f"\n=== TOP 50 TRACKS (by scrobble count) ===")
    for track, count in track_counts.most_common(50):
        print(f"  {count:>4}  {track}")

    # --- Spotify Audio Feature Distributions ---
    features = ["Danceability", "Energy", "Speechiness", "Acousticness",
                 "Instrumentalness", "Liveness", "Valence", "Tempo"]
    print(f"\n=== SPOTIFY AUDIO FEATURE STATS (n={len(spotify)}) ===")
    for feat in features:
        vals = []
        for t in spotify:
            v = t.get(feat)
            if v is not None and isinstance(v, (int, float)):
                vals.append(float(v))
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        mn = min(vals)
        mx = max(vals)
        # Median
        sv = sorted(vals)
        med = sv[len(sv)//2]
        print(f"  {feat:20s}  avg={avg:.3f}  med={med:.3f}  min={mn:.3f}  max={mx:.3f}")

    # --- Genre Distribution from Spotify ---
    genre_counts = Counter()
    for t in spotify:
        genres = t.get("Genres", "")
        if genres:
            for g in genres.split(","):
                genre_counts[g.strip()] += 1
    print(f"\n=== TOP 40 GENRES (Spotify tags) ===")
    for genre, count in genre_counts.most_common(40):
        print(f"  {count:>4}  {genre}")

    # --- Tempo Distribution ---
    tempos = [t["Tempo"] for t in spotify if t.get("Tempo")]
    tempo_buckets = Counter()
    for t in tempos:
        bucket = int(t // 10) * 10
        tempo_buckets[bucket] += 1
    print(f"\n=== TEMPO DISTRIBUTION (10 BPM buckets) ===")
    for bucket in sorted(tempo_buckets.keys()):
        bar = "█" * (tempo_buckets[bucket] // 3)
        print(f"  {bucket:>3}-{bucket+9:<3} BPM: {tempo_buckets[bucket]:>4}  {bar}")

    # --- Energy vs Danceability Quadrants ---
    high_e_high_d = sum(1 for t in spotify if t.get("Energy",0) > 0.7 and t.get("Danceability",0) > 0.7)
    high_e_low_d = sum(1 for t in spotify if t.get("Energy",0) > 0.7 and t.get("Danceability",0) <= 0.7)
    low_e_high_d = sum(1 for t in spotify if t.get("Energy",0) <= 0.7 and t.get("Danceability",0) > 0.7)
    low_e_low_d = sum(1 for t in spotify if t.get("Energy",0) <= 0.7 and t.get("Danceability",0) <= 0.7)
    print(f"\n=== ENERGY x DANCEABILITY QUADRANTS ===")
    print(f"  High Energy + High Dance: {high_e_high_d}")
    print(f"  High Energy + Low Dance:  {high_e_low_d}")
    print(f"  Low Energy  + High Dance: {low_e_high_d}")
    print(f"  Low Energy  + Low Dance:  {low_e_low_d}")

    # --- Instrumentalness Distribution ---
    inst_vals = [t["Instrumentalness"] for t in spotify if "Instrumentalness" in t]
    high_inst = sum(1 for v in inst_vals if v > 0.5)
    mid_inst = sum(1 for v in inst_vals if 0.1 < v <= 0.5)
    low_inst = sum(1 for v in inst_vals if v <= 0.1)
    print(f"\n=== INSTRUMENTALNESS DISTRIBUTION ===")
    print(f"  High (>0.5):  {high_inst}  ({100*high_inst/len(inst_vals):.1f}%)")
    print(f"  Mid (0.1-0.5): {mid_inst}  ({100*mid_inst/len(inst_vals):.1f}%)")
    print(f"  Low (<0.1):   {low_inst}  ({100*low_inst/len(inst_vals):.1f}%)")

    # --- Valence (mood) Distribution ---
    val_vals = [t["Valence"] for t in spotify if "Valence" in t]
    dark = sum(1 for v in val_vals if v < 0.3)
    neutral = sum(1 for v in val_vals if 0.3 <= v <= 0.6)
    bright = sum(1 for v in val_vals if v > 0.6)
    print(f"\n=== VALENCE (MOOD) DISTRIBUTION ===")
    print(f"  Dark (<0.3):    {dark}  ({100*dark/len(val_vals):.1f}%)")
    print(f"  Neutral (0.3-0.6): {neutral}  ({100*neutral/len(val_vals):.1f}%)")
    print(f"  Bright (>0.6):  {bright}  ({100*bright/len(val_vals):.1f}%)")

    # --- Scrobble Timeline (yearly) ---
    year_counts = Counter()
    for s in scrobbles:
        ts = s.get("date", 0)
        if ts:
            yr = datetime.fromtimestamp(ts / 1000).year
            year_counts[yr] += 1
    print(f"\n=== SCROBBLE TIMELINE (by year) ===")
    for yr in sorted(year_counts.keys()):
        bar = "█" * (year_counts[yr] // 500)
        print(f"  {yr}: {year_counts[yr]:>6}  {bar}")

    # --- Artist Diversity per Year ---
    year_artists = defaultdict(set)
    for s in scrobbles:
        ts = s.get("date", 0)
        if ts:
            yr = datetime.fromtimestamp(ts / 1000).year
            year_artists[yr].add(s["artist"])
    print(f"\n=== ARTIST DIVERSITY (unique artists per year) ===")
    for yr in sorted(year_artists.keys()):
        print(f"  {yr}: {len(year_artists[yr]):>5} unique artists")

    # --- Key / Mode Distribution ---
    key_names = {0:"C",1:"C#",2:"D",3:"Eb",4:"E",5:"F",6:"F#",7:"G",8:"Ab",9:"A",10:"Bb",11:"B"}
    key_counts = Counter()
    mode_counts = Counter()
    for t in spotify:
        if "Key" in t and t["Key"] is not None:
            key_counts[key_names.get(t["Key"], "?")] += 1
        if "Mode" in t:
            mode_counts["Major" if t["Mode"] == 1 else "Minor"] += 1
    print(f"\n=== KEY DISTRIBUTION ===")
    for k, c in key_counts.most_common():
        print(f"  {k:>3}: {c}")
    print(f"\n=== MODE DISTRIBUTION ===")
    for m, c in mode_counts.most_common():
        print(f"  {m}: {c}")

    # --- Extreme Tracks ---
    print(f"\n=== EXTREME TRACKS ===")
    print("  Lowest Energy:")
    for t in sorted(spotify, key=lambda x: x.get("Energy",1))[:5]:
        print(f"    {t['Energy']:.3f}  {t['Artist Name(s)']} — {t['Track Name']}")
    print("  Highest Energy:")
    for t in sorted(spotify, key=lambda x: x.get("Energy",0), reverse=True)[:5]:
        print(f"    {t['Energy']:.3f}  {t['Artist Name(s)']} — {t['Track Name']}")
    print("  Lowest Valence (Darkest):")
    for t in sorted(spotify, key=lambda x: x.get("Valence",1))[:5]:
        print(f"    {t['Valence']:.3f}  {t['Artist Name(s)']} — {t['Track Name']}")
    print("  Highest Instrumentalness:")
    for t in sorted(spotify, key=lambda x: x.get("Instrumentalness",0), reverse=True)[:5]:
        print(f"    {t['Instrumentalness']:.3f}  {t['Artist Name(s)']} — {t['Track Name']}")
    print("  Longest Duration:")
    for t in sorted(spotify, key=lambda x: x.get("Duration (ms)",0), reverse=True)[:5]:
        dur_min = t["Duration (ms)"] / 60000
        print(f"    {dur_min:.1f}min  {t['Artist Name(s)']} — {t['Track Name']}")
    print("  Shortest Duration:")
    for t in sorted(spotify, key=lambda x: x.get("Duration (ms)",999999))[:5]:
        dur_sec = t["Duration (ms)"] / 1000
        print(f"    {dur_sec:.0f}s  {t['Artist Name(s)']} — {t['Track Name']}")

if __name__ == "__main__":
    analyze()
