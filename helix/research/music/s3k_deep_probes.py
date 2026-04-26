"""
s3k_deep_probes.py — Four deeper S3K attribution probes
========================================================

Test 4: Chord progression Jaccard similarity
    progression_fingerprint is a sequence of chord tokens.
    Jaccard on token sets (ignoring order) and n-gram overlap (respecting
    local order) between each S3K track and each composer's fingerprint.
    This feature cannot be altered by a sequencer without changing the music.

Test 5: Nagao vs Hikichi disambiguation
    Mode-survival test showed 16 Mixolydian uncredited tracks point to Nagao
    but distance called them Hikichi. This test uses only features where
    Nagao and Hikichi diverge most — isolating compositional signal from
    sequencing signal. Outputs a per-track Nagao/Hikichi probability.

Test 6: DCP seam behavior by composer
    pre_seam_density_spike and seam_sharpness measure how the track
    compresses toward its loop point — the DCP collapse proxy.
    Groups tracks by seam behavior (sharp/soft/none) and checks whether
    this clusters by composer. Also: emergence_index vs disappearance_index
    (what voices appear/vanish around the seam).

Test 7: Feature importance — which features drive Hikichi dominance
    For each confirmed track (known non-Hikichi), compute how much each
    feature contributes to the incorrect Hikichi call. High-contribution
    features on wrong-labeled tracks = sequencer-contaminated features.
    Produces a ranked list of features by arranger contamination level.

Run: python domains/music/experiments/s3k_deep_probes.py
"""
from __future__ import annotations
import json
import math
import os
from collections import defaultdict

ARTIFACTS_DIR = "domains/music/artifacts/analysis"
FINGERPRINTS_FILE = "domains/music/artifacts/analysis/s3k_composer_fingerprints.json"

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

# Confirmed non-Hikichi tracks for feature importance test
# Format: (key_suffix, true_composer)
CONFIRMED_NON_HIKICHI = [
    ("05_marble_garden_zone_act_1", "Miyoko Takaoka"),
    ("06_marble_garden_zone_act_2", "Miyoko Takaoka"),
    ("07_carnival_night_zone_act_1", "MJ/Buxer"),
    ("08_carnival_night_zone_act_2", "MJ/Buxer"),
    ("09_icecap_zone_act_1", "Brad Buxer"),
    ("10_icecap_zone_act_2", "Brad Buxer"),
    ("11_launch_base_zone_act_1", "MJ/Buxer"),
    ("12_launch_base_zone_act_2", "MJ/Buxer"),
    ("13_sub_boss_s3", "MJ/Buxer"),
    ("14_staff_roll_s3", "Brad Buxer"),
    ("40_gumball_machine", "Jun Senoue"),
    ("41_magnetic_orbs", "Jun Senoue"),
    ("42_slot_machine", "Jun Senoue"),
    ("43_blue_spheres", "Yoshiaki Kashima"),
]

CONFIRMED_HIKICHI = [
    ("15_mushroom_hill_zone_act_1", "Masanori Hikichi"),
    ("16_mushroom_hill_zone_act_2", "Masanori Hikichi"),
    ("27_boss_theme", "Masanori Hikichi"),
]


def load_fingerprints():
    with open(FINGERPRINTS_FILE) as f:
        d = json.load(f)
    return {c["composer"]: c for c in d["composers"]}


def load_s3k_artifacts():
    tracks = {}
    for fname in sorted(os.listdir(ARTIFACTS_DIR)):
        if "sonic_3_knuckles" not in fname:
            continue
        if fname.startswith("s3k") or fname.startswith("track_"):
            continue
        fpath = os.path.join(ARTIFACTS_DIR, fname)
        with open(fpath) as f:
            d = json.load(f)
        sym = d.get("analysis", {}).get("symbolic") or {}
        if not sym or not sym.get("scale_mode"):
            continue
        eid = d.get("entity_id", fname)
        key = eid.split(".")[-1]
        if key in tracks:
            continue  # deduplicate — keep first (numbered version)
        tracks[key] = {"sym": sym, "dcp": d.get("analysis", {}).get("dcp") or {}}
    return tracks


def euclidean_dist(a, b, features):
    s = 0.0
    n = 0
    for feat, scale in features:
        av, bv = a.get(feat), b.get(feat)
        if av is None or bv is None:
            continue
        if isinstance(av, str) or isinstance(bv, str):
            continue
        try:
            s += ((float(av) - float(bv)) / scale) ** 2
            n += 1
        except (ValueError, TypeError):
            pass
    return math.sqrt(s), n


def feature_contribution(a, b, features):
    """Return per-feature squared contribution (unnormalized)."""
    contribs = {}
    for feat, scale in features:
        av, bv = a.get(feat), b.get(feat)
        if av is None or bv is None:
            contribs[feat] = None
            continue
        try:
            contribs[feat] = ((float(av) - float(bv)) / scale) ** 2
        except (ValueError, TypeError):
            contribs[feat] = None
    return contribs


# ---------------------------------------------------------------------------
# Test 4 — Chord progression Jaccard similarity
# ---------------------------------------------------------------------------

def progression_tokens(fingerprint_str):
    """Split progression_fingerprint into chord tokens."""
    if not fingerprint_str:
        return set(), []
    tokens = fingerprint_str.split("-")
    return set(tokens), tokens


def jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0


def ngram_overlap(tokens_a, tokens_b, n=2):
    """Fraction of n-grams in a that appear in b."""
    if len(tokens_a) < n or len(tokens_b) < n:
        return 0.0
    grams_a = set(tuple(tokens_a[i:i+n]) for i in range(len(tokens_a)-n+1))
    grams_b = set(tuple(tokens_b[i:i+n]) for i in range(len(tokens_b)-n+1))
    if not grams_a:
        return 0.0
    return len(grams_a & grams_b) / len(grams_a)


def test4_chord_jaccard(tracks, fingerprints):
    print("=" * 70)
    print("TEST 4 — Chord Progression Jaccard Similarity")
    print("=" * 70)
    print("progression_fingerprint: chord token sequence — cannot be altered by sequencer.")
    print("Jaccard = unordered token overlap. Bigram = ordered local overlap.\n")

    # Build composer chord profiles
    comp_tokens = {}
    for composer, fp in fingerprints.items():
        pf = fp.get("progression_fingerprint", "")
        tset, tlist = progression_tokens(pf)
        comp_tokens[composer] = (tset, tlist)

    print(f"{'Composer':<25} {'Chord tokens (first 6)'}")
    print("-" * 60)
    for composer, (tset, tlist) in comp_tokens.items():
        print(f"  {composer:<23} {tlist[:6]}")

    print()

    # Per-track Jaccard ranking
    winner_tally_jacc = defaultdict(list)
    winner_tally_bigram = defaultdict(list)

    print(f"{'Track':<42} {'Jaccard winner':<25} {'J':>5}  {'Bigram winner':<25} {'B':>5}")
    print("-" * 110)

    for key, data in sorted(tracks.items()):
        sym = data["sym"]
        pf = sym.get("progression_fingerprint", "")
        tset, tlist = progression_tokens(pf)

        jacc_scores = []
        bigram_scores = []
        for composer, (cset, clist) in comp_tokens.items():
            j = jaccard(tset, cset)
            b = ngram_overlap(tlist, clist, n=2)
            jacc_scores.append((j, composer))
            bigram_scores.append((b, composer))

        jacc_scores.sort(reverse=True)
        bigram_scores.sort(reverse=True)

        jw = jacc_scores[0][1] if jacc_scores else "?"
        jv = jacc_scores[0][0] if jacc_scores else 0
        bw = bigram_scores[0][1] if bigram_scores else "?"
        bv = bigram_scores[0][0] if bigram_scores else 0

        winner_tally_jacc[jw].append(key)
        winner_tally_bigram[bw].append(key)

        label = key.replace("_", " ").title()
        print(f"  {label:<40} {jw:<25} {jv:5.3f}  {bw:<25} {bv:5.3f}")

    print(f"\n--- Jaccard winner tally ---")
    for composer, tlist in sorted(winner_tally_jacc.items(), key=lambda x: -len(x[1])):
        print(f"  {composer}: {len(tlist)}")

    print(f"\n--- Bigram winner tally ---")
    for composer, tlist in sorted(winner_tally_bigram.items(), key=lambda x: -len(x[1])):
        print(f"  {composer}: {len(tlist)}")

    # Cross-check: where Jaccard, Bigram, AND Distance (mode-filtered) all agree
    print(f"\n--- Tracks where Jaccard and Bigram agree on same non-Hikichi composer ---")
    for key, data in sorted(tracks.items()):
        sym = data["sym"]
        pf = sym.get("progression_fingerprint", "")
        tset, tlist = progression_tokens(pf)
        jacc_scores = sorted(((jaccard(tset, cs), c) for c, (cs, cl) in comp_tokens.items()), reverse=True)
        bigram_scores = sorted(((ngram_overlap(tlist, cl, 2), c) for c, (cs, cl) in comp_tokens.items()), reverse=True)
        jw = jacc_scores[0][1]
        bw = bigram_scores[0][1]
        if jw == bw and jw != "Masanori Hikichi":
            label = key.replace("_", " ").title()
            print(f"  {label:<40} → {jw}  (J={jacc_scores[0][0]:.3f}, B={bigram_scores[0][0]:.3f})")

    return winner_tally_jacc


# ---------------------------------------------------------------------------
# Test 5 — Nagao vs Hikichi disambiguation
# ---------------------------------------------------------------------------

def test5_nagao_hikichi(tracks, fingerprints):
    print("\n" + "=" * 70)
    print("TEST 5 — Nagao vs Hikichi Disambiguation")
    print("=" * 70)
    print("Mode-survival showed 16 Mixolydian uncredited tracks → Nagao.")
    print("Distance called them Hikichi. Now: use only features where")
    print("Nagao and Hikichi actually diverge most.\n")

    nagao = fingerprints["Masayuki Nagao"]
    hikichi = fingerprints["Masanori Hikichi"]

    # Compute per-feature Nagao-Hikichi gap (normalized)
    gaps = []
    for feat, scale in DIST_FEATURES:
        nv = nagao.get(feat)
        hv = hikichi.get(feat)
        if nv is None or hv is None:
            continue
        try:
            gap = abs(float(nv) - float(hv)) / scale
            gaps.append((gap, feat, scale, float(nv), float(hv)))
        except (ValueError, TypeError):
            pass
    gaps.sort(reverse=True)

    print("Feature gaps Nagao vs Hikichi (normalized, descending):")
    print(f"  {'Feature':<35} {'Nagao':>8} {'Hikichi':>8} {'gap':>6}")
    discriminating = []
    for gap, feat, scale, nv, hv in gaps:
        print(f"  {feat:<35} {nv:8.4f} {hv:8.4f} {gap:6.3f}")
        if gap > 0.3:  # only features with meaningful separation
            discriminating.append((feat, scale))

    print(f"\nDiscriminating features (gap > 0.3): {[f for f,s in discriminating]}")

    # Run 2-way Nagao vs Hikichi distance using only discriminating features
    print(f"\n--- Per-track Nagao vs Hikichi (discriminating features only) ---")
    print(f"{'Track':<44} {'Mode':<12} {'d_Nagao':>8} {'d_Hikichi':>9} {'Winner':<15} {'Gap':>6}")
    print("-" * 100)

    nagao_wins = []
    hikichi_wins = []

    for key, data in sorted(tracks.items()):
        sym = data["sym"]
        mode = sym.get("scale_mode", "?")
        dn, _ = euclidean_dist(sym, nagao, discriminating)
        dh, _ = euclidean_dist(sym, hikichi, discriminating)
        winner = "Nagao" if dn < dh else "Hikichi"
        gap = abs(dn - dh)
        label = key.replace("_", " ").title()

        if winner == "Nagao":
            nagao_wins.append((key, mode, dn, dh, gap))
        else:
            hikichi_wins.append((key, mode, dn, dh, gap))

        # Only show uncredited tracks
        confirmed_keys = {k for k, _ in CONFIRMED_NON_HIKICHI + CONFIRMED_HIKICHI}
        if key not in confirmed_keys:
            print(f"  {label:<42} {mode:<12} {dn:8.3f} {dh:9.3f} {winner:<15} {gap:6.3f}")

    print(f"\nNagao wins (uncredited): {len(nagao_wins)}")
    print(f"Hikichi wins (uncredited): {len(hikichi_wins)}")

    print(f"\n--- Nagao wins summary (all uncredited) ---")
    for key, mode, dn, dh, gap in sorted(nagao_wins, key=lambda x: -x[4]):
        label = key.replace("_", " ").title()
        print(f"  {label:<42} mode={mode:<12} gap={gap:.3f}")

    # Sanity check: confirmed Hikichi tracks
    print(f"\n--- Sanity check on confirmed Hikichi tracks ---")
    for key, true_comp in CONFIRMED_HIKICHI:
        data = tracks.get(key)
        if not data:
            continue
        sym = data["sym"]
        dn, _ = euclidean_dist(sym, nagao, discriminating)
        dh, _ = euclidean_dist(sym, hikichi, discriminating)
        winner = "Nagao" if dn < dh else "Hikichi"
        label = key.replace("_", " ").title()
        correct = "✓" if winner == "Hikichi" else "✗"
        print(f"  {correct} {label:<40} → {winner}  (d_N={dn:.3f}, d_H={dh:.3f})")


# ---------------------------------------------------------------------------
# Test 6 — DCP seam behavior by composer
# ---------------------------------------------------------------------------

def test6_seam_dcp(tracks, fingerprints):
    print("\n" + "=" * 70)
    print("TEST 6 — DCP Seam Behavior by Composer")
    print("=" * 70)
    print("pre_seam_density_spike: note density surge before loop point.")
    print("seam_sharpness: how abruptly the loop collapses.")
    print("emergence_index: voices that appear near seam.")
    print("disappearance_index: voices that vanish near seam.\n")

    # Classify seam types
    def seam_type(spike, sharp):
        if spike > 5.0 or sharp > 5.0:
            return "SHARP"
        elif spike > 2.0 or sharp > 1.0:
            return "MODERATE"
        elif spike > 0.5:
            return "SOFT"
        else:
            return "NONE"

    # Build seam profile
    seam_rows = []
    for key, data in sorted(tracks.items()):
        sym = data["sym"]
        spike = sym.get("pre_seam_density_spike") or 0.0
        sharp = sym.get("seam_sharpness") or 0.0
        emerge = sym.get("emergence_index") or 0.0
        disappear = sym.get("disappearance_index") or 0.0
        has_loop = sym.get("has_loop_seam", False)
        stype = seam_type(spike, sharp)
        seam_rows.append((key, spike, sharp, emerge, disappear, stype, has_loop))

    # Print distribution
    from collections import Counter
    type_counts = Counter(r[5] for r in seam_rows)
    print(f"Seam type distribution: {dict(type_counts)}")
    print()

    # Print all tracks grouped by seam type
    for stype in ["SHARP", "MODERATE", "SOFT", "NONE"]:
        group = [r for r in seam_rows if r[5] == stype]
        if not group:
            continue
        print(f"--- {stype} ({len(group)} tracks) ---")
        for key, spike, sharp, emerge, disappear, st, has_loop in sorted(group, key=lambda x: -x[1]):
            label = key.replace("_", " ").title()
            print(f"  {label:<42} spike={spike:5.2f}  sharp={sharp:5.2f}  emerge={emerge:6.3f}  disappear={disappear:6.3f}")
        print()

    # Composer seam fingerprints: what seam types do confirmed composers produce?
    print("--- Composer seam type from confirmed tracks ---")
    confirmed_all = CONFIRMED_NON_HIKICHI + CONFIRMED_HIKICHI
    comp_seam = defaultdict(list)
    for key, comp in confirmed_all:
        data = tracks.get(key)
        if not data:
            continue
        sym = data["sym"]
        spike = sym.get("pre_seam_density_spike") or 0.0
        sharp = sym.get("seam_sharpness") or 0.0
        emerge = sym.get("emergence_index") or 0.0
        stype = seam_type(spike, sharp)
        comp_seam[comp].append((key, spike, sharp, emerge, stype))

    for comp, items in sorted(comp_seam.items()):
        avg_spike = sum(x[1] for x in items) / len(items)
        avg_sharp = sum(x[2] for x in items) / len(items)
        avg_emerge = sum(x[3] for x in items) / len(items)
        type_dist = Counter(x[4] for x in items)
        print(f"  {comp:<25} avg_spike={avg_spike:.2f}  avg_sharp={avg_sharp:.2f}  avg_emerge={avg_emerge:.3f}  types={dict(type_dist)}")

    # Outlier: Competition Menu has spike=14 — inspect
    print(f"\n--- Outlier: Competition Menu (Final) ---")
    data = tracks.get("32_competition_menu")
    if data:
        sym = data["sym"]
        print(f"  spike={sym.get('pre_seam_density_spike'):.3f}")
        print(f"  sharpness={sym.get('seam_sharpness'):.3f}")
        print(f"  loop_point_s={sym.get('loop_point_s')}")
        print(f"  mode={sym.get('scale_mode')}  mode_confidence={sym.get('mode_confidence'):.2f}")
        print(f"  note_density={sym.get('note_density'):.2f}")
        print("  Note: This is the S3 M.J. version Competition Menu (absent from Origins)")
        print("  The extreme spike may reflect the MJ team's sample-heavy approach to loop structure.")

    # Disappearance index extremes — tracks where everything drops at loop
    print(f"\n--- Tracks with extreme disappearance_index (voices vanish at seam) ---")
    vanish = sorted(seam_rows, key=lambda x: x[4])[:8]
    for key, spike, sharp, emerge, disappear, stype, loop in vanish:
        label = key.replace("_", " ").title()
        print(f"  {label:<42} disappear={disappear:6.3f}  spike={spike:.2f}")


# ---------------------------------------------------------------------------
# Test 7 — Feature importance / arranger contamination
# ---------------------------------------------------------------------------

def test7_feature_importance(tracks, fingerprints):
    print("\n" + "=" * 70)
    print("TEST 7 — Feature Importance: Arranger Contamination Ranking")
    print("=" * 70)
    print("For each confirmed non-Hikichi track, measure how much each feature")
    print("contributes to the (incorrect) Hikichi call.")
    print("High contamination = feature is driven by Hikichi's sequencing, not composition.\n")

    hikichi = fingerprints["Masanori Hikichi"]

    # Per-feature contamination accumulator
    feat_contamination = defaultdict(list)
    feat_pull_hikichi = defaultdict(list)  # how much feature PULLS toward Hikichi vs true composer

    for key, true_comp in CONFIRMED_NON_HIKICHI:
        data = tracks.get(key)
        if not data:
            continue
        sym = data["sym"]

        # True composer fingerprint
        true_fp = fingerprints.get(true_comp)

        # Contribution of each feature to Hikichi distance
        hik_contribs = feature_contribution(sym, hikichi, DIST_FEATURES)
        for feat, c in hik_contribs.items():
            if c is not None:
                feat_contamination[feat].append(c)

        # If true composer is in pool, compare Hikichi vs true composer per feature
        if true_fp:
            hik_contribs = feature_contribution(sym, hikichi, DIST_FEATURES)
            true_contribs = feature_contribution(sym, true_fp, DIST_FEATURES)
            for feat, scale in DIST_FEATURES:
                hc = hik_contribs.get(feat)
                tc = true_contribs.get(feat)
                if hc is not None and tc is not None:
                    # Positive = this feature pulls MORE toward Hikichi than truth
                    # (meaning Hikichi is CLOSER on this feature — contamination)
                    pull = tc - hc  # if positive, Hikichi is closer (tc > hc)
                    feat_pull_hikichi[feat].append(pull)

    # Rank by how often a feature pulls toward Hikichi over true composer
    print("Feature contamination ranking (how much each feature pulls toward Hikichi")
    print("on confirmed non-Hikichi tracks):\n")
    print(f"  {'Feature':<35} {'avg Hikichi pull':>18} {'% tracks Hikichi closer':>24}")
    print("-" * 80)

    ranked = []
    for feat, scale in DIST_FEATURES:
        pulls = feat_pull_hikichi[feat]
        if not pulls:
            continue
        avg_pull = sum(pulls) / len(pulls)
        pct_closer = 100 * sum(1 for p in pulls if p > 0) / len(pulls)
        ranked.append((avg_pull, pct_closer, feat))

    ranked.sort(reverse=True)
    for avg_pull, pct, feat in ranked:
        contaminated = "← CONTAMINATED" if pct > 60 and avg_pull > 0 else ""
        print(f"  {feat:<35} {avg_pull:>18.4f} {pct:>23.0f}%  {contaminated}")

    # Now recompute 9-way comparison WITHOUT contaminated features
    contaminated_feats = {feat for avg_pull, pct, feat in ranked if pct > 60 and avg_pull > 0}
    clean_features = [(f, s) for f, s in DIST_FEATURES if f not in contaminated_feats]

    print(f"\nRemoving {len(contaminated_feats)} contaminated features: {contaminated_feats}")
    print(f"Remaining clean features: {[f for f,s in clean_features]}\n")

    print("--- 9-way comparison using CLEAN features only (uncredited tracks) ---")
    print(f"{'Track':<44} {'Clean winner':<25} {'d':>5} {'gap':>5}  {'Full winner'}")
    print("-" * 100)

    confirmed_keys = {k for k, _ in CONFIRMED_NON_HIKICHI + CONFIRMED_HIKICHI}

    changes = 0
    total = 0
    for key, data in sorted(tracks.items()):
        if key in confirmed_keys:
            continue
        sym = data["sym"]

        # Full distance winner
        full_scores = sorted((euclidean_dist(sym, fp, DIST_FEATURES)[0], c)
                              for c, fp in fingerprints.items())
        full_winner = full_scores[0][1]

        # Clean distance winner
        clean_scores = sorted((euclidean_dist(sym, fp, clean_features)[0], c)
                               for c, fp in fingerprints.items())
        clean_winner = clean_scores[0][1]
        clean_d = clean_scores[0][0]
        clean_gap = clean_scores[1][0] - clean_d if len(clean_scores) > 1 else 0

        label = key.replace("_", " ").title()
        changed = "← CHANGED" if clean_winner != full_winner else ""
        if clean_winner != full_winner:
            changes += 1
        total += 1
        print(f"  {label:<42} {clean_winner:<25} {clean_d:5.2f} {clean_gap:5.2f}  {full_winner} {changed}")

    print(f"\nAttribution changed after removing contaminated features: {changes}/{total} tracks")

    # Summary table: what the clean analysis says about Sega Sound Team tracks
    print(f"\n--- Clean attribution tally ---")
    clean_tally = defaultdict(list)
    for key, data in sorted(tracks.items()):
        if key in confirmed_keys:
            continue
        sym = data["sym"]
        clean_scores = sorted((euclidean_dist(sym, fp, clean_features)[0], c)
                               for c, fp in fingerprints.items())
        clean_tally[clean_scores[0][1]].append(key)

    for composer, tlist in sorted(clean_tally.items(), key=lambda x: -len(x[1])):
        print(f"  {composer}: {len(tlist)} tracks")
        for t in tlist[:5]:
            print(f"    {t.replace('_', ' ').title()}")
        if len(tlist) > 5:
            print(f"    ... +{len(tlist)-5} more")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading fingerprints and artifacts...")
    fingerprints = load_fingerprints()
    tracks = load_s3k_artifacts()
    print(f"  {len(fingerprints)} composers  |  {len(tracks)} S3K tracks\n")

    test4_chord_jaccard(tracks, fingerprints)
    test5_nagao_hikichi(tracks, fingerprints)
    test6_seam_dcp(tracks, fingerprints)
    test7_feature_importance(tracks, fingerprints)

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
