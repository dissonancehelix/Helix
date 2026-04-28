"""
s3k_three_tests.py — Three-pronged S3K attribution probe
=========================================================

Test 1: Full 9-way comparison
    Euclidean distance across all 9 calibrated composers vs every S3K track.
    Previous run was 4-way (Ogawa/Sawada/Maeda/Hikichi). Now adds
    Setsumaru, Nagao, Kashima, Takaoka, Senoue.

Test 2: Takaoka bonus stage hypothesis
    Takaoka confirmed Marble Garden Zone. She claimed a bonus stage that went
    unused. Forum noted Marble Garden and Magnetic Orbs (Glowing Spheres) share
    "simulated rhythm guitar" and "jazz-funk scale" — only two tracks with that
    technique. Direct feature comparison: MGZ Act 1 (confirmed Takaoka) vs
    all three bonus stages.

Test 3: Mode-survival test
    The arranger bias operates at the sequencing layer. Scale mode and
    primary interval relationships are harder for a sequencer to alter.
    Group uncredited S3K tracks by detected mode and compare against composer
    mode profiles. Tests whether mode-level analysis bypasses the Hikichi
    sequencing fingerprint that dominated the 4-way comparison.

Run: python domains/music/model/experiments/s3k_three_tests.py
"""
from __future__ import annotations
import json
import math
import os
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ARTIFACTS_DIR = "domains/music/model/artifacts/analysis"
FINGERPRINTS_FILE = "domains/music/model/artifacts/analysis/s3k_composer_fingerprints.json"

# ---------------------------------------------------------------------------
# Features used for Euclidean distance (present in both artifact symbolic
# section and composer fingerprint pool)
# ---------------------------------------------------------------------------
DIST_FEATURES = [
    ("pitch_entropy",           0.5),
    ("chromatic_intrusion_rate",0.10),
    ("rhythmic_entropy",        0.5),
    ("off_beat_ratio",          0.20),
    ("motif_recurrence",        0.10),
    ("sustained_ratio",         0.10),
    ("register_separation",     10.0),
    ("groove_score",            0.20),
    ("bass_rhythmic_regularity",0.20),
    ("melody_bass_independence",0.20),
    ("harmonic_tension_score",  0.20),
    ("prevalence_of_tritones",  0.05),
    ("vertical_dissonance",     0.05),
]

# Additional symbolic features present in artifact but not in fingerprint pool
# (used for supplemental mode-survival test)
EXTRA_FEATURES = [
    "note_density", "avg_phrase_length", "phrase_regularity", "scale_mode"
]

# ---------------------------------------------------------------------------
# Known credits (for labelling output and skipping confirmed tracks)
# ---------------------------------------------------------------------------
CONFIRMED = {
    "05_marble_garden_zone_act_1": "Miyoko Takaoka",
    "06_marble_garden_zone_act_2": "Miyoko Takaoka",
    "07_carnival_night_zone_act_1": "MJ/Buxer",
    "08_carnival_night_zone_act_2": "MJ/Buxer",
    "09_icecap_zone_act_1": "Brad Buxer",
    "10_icecap_zone_act_2": "Brad Buxer",
    "11_launch_base_zone_act_1": "MJ/Buxer",
    "12_launch_base_zone_act_2": "MJ/Buxer",
    "13_sub_boss_s3": "MJ/Buxer",
    "14_staff_roll_s3": "Brad Buxer",
    "27_boss_act_2": "Masanori Hikichi",
    "40_gumball_machine": "Jun Senoue",
    "41_magnetic_orbs": "Jun Senoue",
    "42_slot_machine": "Jun Senoue",
    "43_blue_spheres": "Yoshiaki Kashima",
    "15_mushroom_hill_zone_act_1": "Hikichi (~)",
    "16_mushroom_hill_zone_act_2": "Hikichi (~)",
}

BONUS_STAGE_IDS = ["40_gumball_machine", "41_magnetic_orbs", "42_slot_machine"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_fingerprints():
    with open(FINGERPRINTS_FILE) as f:
        d = json.load(f)
    return {c["composer"]: c for c in d["composers"]}


def load_s3k_artifacts():
    tracks = {}
    for fname in sorted(os.listdir(ARTIFACTS_DIR)):
        if "sonic_3_knuckles" not in fname:
            continue
        fpath = os.path.join(ARTIFACTS_DIR, fname)
        with open(fpath) as f:
            d = json.load(f)
        sym = d.get("analysis", {}).get("symbolic", {})
        if not sym or sym.get("error"):
            continue
        # derive short key from entity_id
        eid = d.get("entity_id", fname)
        key = eid.split(".")[-1]  # e.g. 01_angel_island_zone_act_1
        tracks[key] = sym
    return tracks


def euclidean_dist(a_dict, b_dict, features):
    total = 0.0
    used = 0
    for feat, scale in features:
        av = a_dict.get(feat)
        bv = b_dict.get(feat)
        if av is None or bv is None:
            continue
        if isinstance(av, str) or isinstance(bv, str):
            continue
        if math.isnan(float(av)) or math.isnan(float(bv)):
            continue
        total += ((float(av) - float(bv)) / scale) ** 2
        used += 1
    return math.sqrt(total) if used > 0 else float("inf"), used


def rank_composers(track_sym, fingerprints, features):
    scores = []
    for composer, fp in fingerprints.items():
        d, n = euclidean_dist(track_sym, fp, features)
        scores.append((d, composer, n))
    scores.sort()
    return scores


def pretty_label(key):
    return key.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Test 1 — Full 9-way comparison
# ---------------------------------------------------------------------------

def test1_nine_way(tracks, fingerprints):
    print("=" * 70)
    print("TEST 1 — Full 9-way Composer Comparison")
    print("=" * 70)

    winner_tally = defaultdict(list)
    rows = []

    for key, sym in sorted(tracks.items()):
        credit = CONFIRMED.get(key)
        label = pretty_label(key)
        scores = rank_composers(sym, fingerprints, DIST_FEATURES)
        if not scores:
            continue
        best_d, best_composer, _ = scores[0]
        second_d = scores[1][0] if len(scores) > 1 else float("inf")
        margin = second_d - best_d
        winner_tally[best_composer].append(key)
        rows.append((key, label, best_composer, best_d, margin, second_d, scores[1][1] if len(scores) > 1 else "?", credit))

    # Print table
    print(f"\n{'Track':<42} {'Winner':<22} {'d':>5} {'gap':>5} {'2nd':>5} {'Known'}")
    print("-" * 95)
    for key, label, winner, d, gap, d2, c2, credit in rows:
        known = f"[{credit}]" if credit else ""
        flag = "!" if credit and credit.split("/")[0].split("(")[0].strip() not in winner else ""
        print(f"{label:<42} {winner:<22} {d:5.2f} {gap:5.2f} {d2:5.2f}  {known} {flag}")

    print(f"\n--- Winner tally ---")
    for composer, track_list in sorted(winner_tally.items(), key=lambda x: -len(x[1])):
        print(f"  {composer}: {len(track_list)} tracks")
        for t in track_list:
            print(f"    {pretty_label(t)}")

    return rows, winner_tally


# ---------------------------------------------------------------------------
# Test 2 — Takaoka bonus stage hypothesis
# ---------------------------------------------------------------------------

def test2_takaoka_bonus(tracks, fingerprints):
    print("\n" + "=" * 70)
    print("TEST 2 — Takaoka Bonus Stage Hypothesis")
    print("=" * 70)
    print("Marble Garden Act 1 (confirmed Takaoka) vs 3 bonus stages.")
    print("Takaoka claimed she composed a bonus stage that went unused.")
    print("Forum: MGZ and Magnetic Orbs share 'simulated rhythm guitar' + jazz-funk scale.\n")

    mg_key = "05_marble_garden_zone_act_1"
    mg_sym = tracks.get(mg_key)
    if mg_sym is None:
        print("ERROR: Marble Garden Act 1 not found in artifacts")
        return

    bonus_keys = {
        "Gumball Machine": "40_gumball_machine",
        "Magnetic Orbs (Glowing Spheres)": "41_magnetic_orbs",
        "Slot Machine": "42_slot_machine",
    }

    print(f"{'Feature':<30} {'MG Act1':>10}", end="")
    for name in bonus_keys:
        short = name.split()[0][:10]
        print(f"  {short:>10}", end="")
    print()
    print("-" * 75)

    # Print feature comparison table
    for feat, scale in DIST_FEATURES:
        mg_v = mg_sym.get(feat, "?")
        row = f"{feat:<30} {float(mg_v) if mg_v != '?' else float('nan'):>10.4f}"
        for name, bkey in bonus_keys.items():
            bsym = tracks.get(bkey, {})
            bv = bsym.get(feat, "?")
            row += f"  {float(bv) if bv != '?' else float('nan'):>10.4f}"
        print(row)

    # Mode comparison
    print()
    mg_mode = mg_sym.get("scale_mode", "?")
    print(f"{'scale_mode':<30} {mg_mode:>10}", end="")
    for name, bkey in bonus_keys.items():
        bsym = tracks.get(bkey, {})
        print(f"  {bsym.get('scale_mode','?'):>10}", end="")
    print()

    # Extra features
    for feat in ["note_density", "avg_phrase_length", "phrase_regularity"]:
        mg_v = mg_sym.get(feat, "?")
        row = f"{feat:<30} {float(mg_v) if mg_v != '?' else float('nan'):>10.4f}"
        for name, bkey in bonus_keys.items():
            bsym = tracks.get(bkey, {})
            bv = bsym.get(feat, "?")
            row += f"  {float(bv) if bv != '?' else float('nan'):>10.4f}"
        print(row)

    print()
    print("--- Euclidean distances: Marble Garden Act 1 → each bonus stage ---")
    for name, bkey in bonus_keys.items():
        bsym = tracks.get(bkey, {})
        if not bsym:
            print(f"  {name}: artifact missing")
            continue
        d, n = euclidean_dist(mg_sym, bsym, DIST_FEATURES)
        print(f"  {name:<35} d={d:.3f}  (over {n} features)")

    # Also compare MG Act 1 to Takaoka fingerprint vs Senoue fingerprint
    print()
    print("--- Composer distances for the bonus stages (who wins each?) ---")
    for name, bkey in bonus_keys.items():
        bsym = tracks.get(bkey, {})
        if not bsym:
            continue
        scores = rank_composers(bsym, fingerprints, DIST_FEATURES)
        top3 = scores[:3]
        result = " | ".join(f"{c}={d:.2f}" for d, c, _ in top3)
        print(f"  {name:<35} {result}")


# ---------------------------------------------------------------------------
# Test 3 — Mode-survival test
# ---------------------------------------------------------------------------

def test3_mode_survival(tracks, fingerprints):
    print("\n" + "=" * 70)
    print("TEST 3 — Mode-Survival Test (Arranger Bias Bypass)")
    print("=" * 70)
    print("Scale mode and interval relationships survive sequencing.")
    print("Groups uncredited S3K tracks by mode; checks alignment with composer profiles.\n")

    # Composer mode profiles
    print("Composer mode profiles (dominant mode from calibration corpus):")
    for composer, fp in sorted(fingerprints.items()):
        print(f"  {composer:<25} {fp.get('scale_mode','?')}")

    # Group S3K tracks by mode
    mode_groups = defaultdict(list)
    for key, sym in sorted(tracks.items()):
        mode = sym.get("scale_mode", "Unknown")
        mode_groups[mode].append((key, sym))

    print(f"\nS3K track mode distribution:")
    for mode, group in sorted(mode_groups.items(), key=lambda x: -len(x[1])):
        print(f"  {mode}: {len(group)} tracks")

    # For uncredited tracks, look at mode + distance within mode-matched composers
    print("\n--- Mode-filtered distances (uncredited tracks only) ---")
    print(f"{'Track':<42} {'Mode':<12} {'Mode-match composers':<40} {'Best overall'}")
    print("-" * 110)

    # Build mode → composers map
    mode_to_composers = defaultdict(list)
    for composer, fp in fingerprints.items():
        mode_to_composers[fp.get("scale_mode", "Unknown")].append(composer)

    uncredited_results = []
    for key, sym in sorted(tracks.items()):
        if key in CONFIRMED:
            continue
        mode = sym.get("scale_mode", "?")
        mode_matched = mode_to_composers.get(mode, [])

        all_scores = rank_composers(sym, fingerprints, DIST_FEATURES)
        best_overall = f"{all_scores[0][1]}={all_scores[0][0]:.2f}" if all_scores else "?"

        # Best within mode-matched composers
        mode_scores = [(d, c) for d, c, _ in all_scores if c in mode_matched]
        mode_best = f"{mode_scores[0][1]}={mode_scores[0][0]:.2f}" if mode_scores else "no match"

        label = pretty_label(key)
        print(f"{label:<42} {mode:<12} {mode_best:<40} {best_overall}")
        uncredited_results.append((key, mode, mode_scores, all_scores))

    # Summary: does mode-filtering change the winner?
    print("\n--- Mode-filter effect summary ---")
    same = 0
    different = 0
    for key, mode, mode_scores, all_scores in uncredited_results:
        if not mode_scores or not all_scores:
            continue
        best_mode_winner = mode_scores[0][1]
        best_overall_winner = all_scores[0][1]
        if best_mode_winner == best_overall_winner:
            same += 1
        else:
            different += 1
            print(f"  DIVERGES: {pretty_label(key)}")
            print(f"    Mode ({mode}) suggests: {best_mode_winner}  |  Distance suggests: {best_overall_winner}")

    print(f"\n  Same winner: {same}  |  Different winner: {different}")

    # Mode concentration analysis
    print("\n--- What Nagao's Mixolydian dominance predicts ---")
    print(f"  Nagao claims he 'produced half the music'")
    nagao_mode = fingerprints.get("Masayuki Nagao", {}).get("scale_mode", "?")
    s3k_mixo = [k for k, sym in tracks.items() if sym.get("scale_mode") == nagao_mode and k not in CONFIRMED]
    print(f"  Nagao dominant mode: {nagao_mode}")
    print(f"  S3K uncredited tracks in {nagao_mode}: {len(s3k_mixo)}")
    for k in sorted(s3k_mixo):
        print(f"    {pretty_label(k)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading fingerprints and artifacts...")
    fingerprints = load_fingerprints()
    tracks = load_s3k_artifacts()
    print(f"  {len(fingerprints)} composers  |  {len(tracks)} S3K tracks\n")

    test1_nine_way(tracks, fingerprints)
    test2_takaoka_bonus(tracks, fingerprints)
    test3_mode_survival(tracks, fingerprints)

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()

