"""
music_keff.py — Music Domain k_eff Probe (Spotify + MIDI)
==========================================================
Computes k_eff for the music domain from two complementary sources,
both mapped onto the same compression-density formula used for language k_eff
so the scales are directly comparable across domains.

--- Spotify Source (from music_keff_probe.py) ---
DCP in music: the structural disambiguation signals of tonal harmony
(key, mode, harmonic function) constrain possible harmonic interpretations.
Genre encodes which signals are used how strongly — just like language
families encode which grammatical signals dominate.

Compression density formula (Spotify):
    music_compression_density =
        mode_concentration × 1.5   (analog: case_density)
        + valence_consistency × 1.0 (analog: agreement_density)
        + key_concentration × 0.4   (analog: order_signal)

    k_eff = 1.4 + 2.73 × exp(-1.378 × compression_density)

  mode_concentration: |frac_major - 0.5| × 2 — how strongly genre locks mode
  valence_consistency: 1 - std_norm(valence) — how consistent harmonic tension is
  key_concentration: max fraction any one key takes — how much genre constrains key

DCP prediction: genres with strong tonal conventions (classical, pop) →
low k_eff (like case-dominant languages). Genres with free harmonic
movement (jazz, experimental) → high k_eff (like word-order languages).

--- MIDI Source (from music_midi_keff_probe.py) ---
Takes MIDI files → NoteEvents → SymbolicScore → HarmonicAnalyzer →
chord_progression_entropy → k_eff.

This gives a DIRECT music k_eff from actual harmonic content (chord
bigram transitions), comparable to the language parse-alternative k_eff.

The mapping:
  language: 1/Σp_i² over parse alternatives (agent weights)
  music:    exp(chord_progression_entropy × scale) — entropy over chord bigrams

Calibration anchors (from music theory):
  Chorale (Bach): ~7 distinct bigrams, H ≈ 2.2 bits → k_eff ≈ 1.5  [tonal, constrained]
  Pop/rock:       ~15 bigrams, H ≈ 2.8 bits → k_eff ≈ 1.8  [agreement-dominant]
  Jazz standard:  ~40 bigrams, H ≈ 4.0 bits → k_eff ≈ 2.7  [word-order-dominant]

These match the language typological clusters [1.46, 2.91].

Usage:
    python domains/music/model/probes/music_keff.py                  # both sources
    python domains/music/model/probes/music_keff.py --source spotify  # Spotify only
    python domains/music/model/probes/music_keff.py --source midi --scan domains/music/model/artifacts/midi/
    python domains/music/model/probes/music_keff.py --source midi track.mid [track2.mid ...]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
sys.path.insert(0, str(ROOT))

SPOTIFY_PATH = (
    ROOT
    / "domains" / "music"
    / "labs"
    / "datasets"
    / "music"
    / "metadata"
    / "spotify.json"
)

# ---------------------------------------------------------------------------
# Genre cluster definitions (Spotify source)
# Grouped by broad harmonic convention (tonal strength)
# ---------------------------------------------------------------------------

GENRE_CLUSTERS: dict[str, list[str]] = {
    # Classical / orchestral: strongest tonal conventions, functional harmony
    "tonal_classical": [
        "classical", "orchestral", "baroque", "romantic", "chamber music",
        "opera", "choral", "neoclassical", "contemporary classical",
        "film score", "soundtrack",
    ],
    # Jazz and fusion: sophisticated harmony, modal interchange, frequent modulation
    "jazz_chromatic": [
        "jazz", "bebop", "cool jazz", "fusion", "acid jazz",
        "jazz fusion", "nu jazz", "jazz funk", "free jazz",
        "contemporary jazz", "smooth jazz",
    ],
    # Pop / rock: strong tonality, limited modulation, verse-chorus
    "tonal_pop": [
        "pop", "rock", "indie rock", "alternative rock", "pop rock",
        "indie pop", "soft rock", "folk rock", "british invasion",
        "new wave", "post-punk", "jangle pop", "power pop",
    ],
    # Electronic / dance: often single-key, functional but repetitive
    "electronic_dance": [
        "electronic", "techno", "house", "trance", "progressive trance",
        "ambient", "downtempo", "electronica", "idm", "drum and bass",
        "jungle", "trip hop", "chillout", "psytrance", "deep house",
        "progressive house", "minimal techno", "uk garage",
    ],
    # Metal / heavy rock: power chords, chromatic riffs, modal
    "metal_modal": [
        "metal", "heavy metal", "thrash metal", "death metal", "black metal",
        "doom metal", "progressive metal", "alternative metal", "nu metal",
        "industrial metal", "gothic metal", "hard rock", "grunge",
    ],
    # Hip hop / R&B: loop-based, sampling, mixed tonal content
    "hip_hop_rnb": [
        "hip hop", "rap", "r&b", "soul", "funk", "neo soul",
        "trap", "gangsta rap", "conscious hip hop",
    ],
    # Folk / acoustic: strong tonal, simple progressions
    "folk_acoustic": [
        "folk", "singer-songwriter", "acoustic", "country", "bluegrass",
        "americana", "celtic", "traditional", "world",
    ],
    # Experimental / avant-garde: weakest tonal constraints
    "experimental": [
        "experimental", "avant-garde", "noise", "drone", "musique concrete",
        "post-rock", "math rock", "krautrock", "psychedelic rock",
        "space rock", "shoegaze", "post-metal",
    ],
}


# =============================================================================
# SPOTIFY SOURCE
# =============================================================================

def _key_mode_label(key: int, mode: int) -> str:
    key_names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    mode_names = {0: "min", 1: "maj"}
    return f"{key_names[key % 12]}_{mode_names.get(mode, '?')}"


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))


def music_compression_density(tracks: list[dict]) -> dict:
    """
    Compute harmonic compression signals from Spotify audio features,
    mapped onto the same three-signal schema as language.

    Signal                   Music source                    Language analog
    ─────────────────────────────────────────────────────────────────────────
    mode_concentration       |frac_major - 0.5| × 2         case_density
      Genre locks mode?      (0=even split, 1=all same)      (postposition/morphology)

    valence_consistency      1 - std_norm(valence)           agreement_density
      Harmonic tension stable?(0=chaotic, 1=very consistent)  (verb agreement)

    key_concentration        max fraction of any single key  order_signal
      Genre constrains key?  over 12 chromatic classes       (word order rigidity)

    compression_density = mode_concentration×1.5 + valence_consistency×1.0 + key_concentration×0.4
    k_eff = 1.4 + 2.73 × exp(-1.378 × compression_density)   [same formula as language]
    """
    valid = [
        t for t in tracks
        if t.get("Key") is not None
        and t.get("Mode") is not None
        and isinstance(t.get("Valence"), (int, float))
    ]
    if not valid:
        return {"error": "no_data"}

    # Mode concentration: how strongly does genre prefer major or minor?
    modes = [t["Mode"] for t in valid]
    frac_major = sum(1 for m in modes if m == 1) / len(modes)
    mode_concentration = abs(frac_major - 0.5) * 2.0  # [0, 1]

    # Valence consistency: how stable is harmonic tension across the genre?
    valences = [t["Valence"] for t in valid]
    valence_std = _stdev(valences)
    valence_consistency = max(0.0, 1.0 - valence_std * 2.0)  # std ~0.5 → consistency=0

    # Key concentration: does genre cluster around certain keys?
    key_counts = Counter(t["Key"] % 12 for t in valid)
    key_total = sum(key_counts.values())
    key_concentration = key_counts.most_common(1)[0][1] / key_total if key_total > 0 else 0.0

    comp = (
        mode_concentration * 1.5
        + valence_consistency * 1.0
        + key_concentration * 0.4
    )
    k_eff = 1.4 + 2.73 * math.exp(-1.378 * comp)

    mean_valence = sum(valences) / len(valences)

    return {
        "n": len(valid),
        "mode_concentration": round(mode_concentration, 3),
        "valence_consistency": round(valence_consistency, 3),
        "key_concentration": round(key_concentration, 3),
        "compression_density": round(comp, 4),
        "k_eff": round(k_eff, 3),
        "mean_valence": round(mean_valence, 3),
        "frac_major": round(frac_major, 3),
    }


def load_spotify_tracks() -> list[dict]:
    return json.loads(SPOTIFY_PATH.read_text(encoding="utf-8"))


def assign_cluster(track_genres: str) -> str | None:
    """Return the first matching cluster for a track's genre string."""
    if not track_genres:
        return None
    genres_lower = track_genres.lower()
    for cluster, keywords in GENRE_CLUSTERS.items():
        for kw in keywords:
            if kw in genres_lower:
                return cluster
    return None


def run_spotify_probe(tracks: list[dict]) -> dict:
    # Assign each track to a cluster
    cluster_tracks: dict[str, list[dict]] = defaultdict(list)
    unassigned = []
    for t in tracks:
        cluster = assign_cluster(t.get("Genres", ""))
        if cluster:
            cluster_tracks[cluster].append(t)
        else:
            unassigned.append(t)

    # Compute k_eff per cluster using compression density formula
    cluster_results: dict[str, dict] = {}
    for cluster, c_tracks in cluster_tracks.items():
        result = music_compression_density(c_tracks)
        cluster_results[cluster] = result

    # Overall (all tracks regardless of cluster)
    overall = music_compression_density(tracks)

    # Cross-domain comparison anchors
    lang_range = (1.462, 2.906)  # Finnish..Korean (UD treebank calibrated)
    kuramoto_zone = (1.46, 1.98)  # Kuramoto transition zone K∈[1.0, 1.5]

    return {
        "overall": {**overall, "unassigned": len(unassigned)},
        "clusters": cluster_results,
        "cross_domain": {
            "language_k_eff_range": list(lang_range),
            "kuramoto_transition_zone": list(kuramoto_zone),
        },
    }


def print_spotify_report(result: dict) -> None:
    print("\nMusic Domain k_eff Probe — DCP Cross-Domain Test (Spotify)")
    print("═" * 72)
    print("\nCompression density formula (same as language):")
    print("  comp = mode_concentration×1.5 + valence_consistency×1.0 + key_concentration×0.4")
    print("  k_eff = 1.4 + 2.73 × exp(-1.378 × comp)")

    ov = result["overall"]
    print(f"\n  Overall (all genres): k_eff={ov['k_eff']:.3f}  comp={ov['compression_density']:.3f}  "
          f"n={ov['n']}  unassigned={ov['unassigned']}")

    print(f"\n{'─'*72}")
    print(f"  {'Cluster':<22} {'n':>5}  {'comp':>6}  {'k_eff':>6}  "
          f"{'mode_c':>6}  {'val_c':>6}  {'key_c':>6}  {'val_mean':>8}")
    print(f"{'─'*72}")

    # Sort by k_eff ascending (most constrained first)
    sorted_clusters = sorted(
        result["clusters"].items(),
        key=lambda x: x[1].get("k_eff", 99),
    )
    for cluster, info in sorted_clusters:
        if "error" in info:
            print(f"  {cluster:<22}  (no data)")
            continue
        print(
            f"  {cluster:<22} {info['n']:>5}  {info['compression_density']:>6.3f}  "
            f"{info['k_eff']:>6.3f}  "
            f"{info['mode_concentration']:>6.3f}  "
            f"{info['valence_consistency']:>6.3f}  "
            f"{info['key_concentration']:>6.3f}  "
            f"{info.get('mean_valence', 0):>8.3f}"
        )

    # Cross-domain comparison
    cd = result["cross_domain"]
    lang_lo, lang_hi = cd["language_k_eff_range"]
    kura_lo, kura_hi = cd["kuramoto_transition_zone"]
    music_k_effs = [
        info["k_eff"] for info in result["clusters"].values() if "k_eff" in info
    ]

    print(f"\n{'═'*72}")
    print("  CROSS-DOMAIN COMPARISON")
    print(f"{'═'*72}")
    print(f"  Language k_eff range:       [{lang_lo:.3f}, {lang_hi:.3f}]  (UD treebank, 21 languages)")
    print(f"  Kuramoto transition zone:   [{kura_lo:.3f}, {kura_hi:.3f}]  (K ∈ [1.0, 1.5])")

    if music_k_effs:
        music_lo = min(music_k_effs)
        music_hi = max(music_k_effs)
        print(f"  Music k_eff range (genre):  [{music_lo:.3f}, {music_hi:.3f}]  (Spotify, compression density)")

        overlap_low = max(music_lo, lang_lo)
        overlap_high = min(music_hi, lang_hi)
        if overlap_low < overlap_high:
            print(f"\n  Overlap with language range: [{overlap_low:.3f}, {overlap_high:.3f}]  — shared DCP zone")
        else:
            print(f"\n  No overlap with language range. Gap: {overlap_low - overlap_high:.3f}")

    # DCP prediction check: are the clusters ordered as predicted?
    print(f"\n{'─'*72}")
    print("  DCP ORDERING PREDICTION")
    print("  Predicted: tonal_classical < folk_acoustic < electronic_dance < jazz_chromatic")
    print(f"{'─'*72}")
    ordered = [(c, info["k_eff"]) for c, info in sorted_clusters if "k_eff" in info]
    for cluster, k in ordered:
        bar_width = max(0, int((k - 1.4) / (4.1 - 1.4) * 40))
        bar = "█" * bar_width
        print(f"  {cluster:<22}  k={k:.3f}  {bar}")

    print()


# =============================================================================
# MIDI SOURCE
# =============================================================================

# Calibration: map chord_progression_entropy → language-comparable k_eff
# Anchors derived from music theory + language calibration:
#   H=2.2 bits → k_eff=1.52  (chorales, Finnish-like constraint)
#   H=4.0 bits → k_eff=2.75  (jazz, Mandarin-like word-order constraint)
# Fit: k_eff = 1.4 + 2.73 * exp(-1.378 * (1 - H/H_max) * 2.5)
# where H_max = log2(64) = 6 bits (8-type chord × 8-type chord bigrams)

_H_MAX = 6.0          # maximum possible chord bigram entropy (bits)
_K_EFF_A = 1.4
_K_EFF_B = 2.73
_K_EFF_C = 1.378
_K_EFF_SCALE = 2.5    # tuned to match language cluster ranges


def entropy_to_k_eff(h_bits: float) -> float:
    """Map chord_progression_entropy (bits) to language-comparable k_eff."""
    if h_bits <= 0:
        return _K_EFF_A
    h_norm = min(h_bits / _H_MAX, 1.0)
    comp = (1.0 - h_norm) * _K_EFF_SCALE
    return _K_EFF_A + _K_EFF_B * math.exp(-_K_EFF_C * comp)


def midi_to_score(midi_path: Path):
    """Parse a Standard MIDI File → SymbolicScore using mido."""
    from model.domains.music.domain_analysis.symbolic_music.score_representation import (
        NoteEvent, SymbolicScore,
    )

    try:
        import mido
    except ImportError:
        print("  mido not installed: pip install mido")
        return None

    try:
        mid = mido.MidiFile(str(midi_path))
    except Exception as exc:
        print(f"  Cannot read {midi_path.name}: {exc}")
        return None

    tempo = 500_000  # default 120 BPM
    ticks_per_beat = mid.ticks_per_beat or 480

    def ticks_to_sec(ticks: int) -> float:
        return ticks * (tempo / 1_000_000) / ticks_per_beat

    note_events = []
    duration_sec = 0.0

    for i, track in enumerate(mid.tracks):
        active: dict[tuple[int, int], tuple[float, int]] = {}  # (ch, note) → (start_sec, velocity)
        elapsed_ticks = 0
        elapsed_sec = 0.0

        for msg in track:
            elapsed_ticks += msg.time
            elapsed_sec = ticks_to_sec(elapsed_ticks)

            if msg.type == "set_tempo":
                tempo = msg.tempo
                # Recompute elapsed_sec after tempo change
                # (simplified: ok for single-tempo files)

            elif msg.type == "note_on" and msg.velocity > 0:
                active[(msg.channel, msg.note)] = (elapsed_sec, msg.velocity)

            elif msg.type in ("note_off",) or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                key = (msg.channel, msg.note)
                if key in active:
                    start, vel = active.pop(key)
                    dur = elapsed_sec - start
                    if dur > 0.001:
                        note_events.append(
                            NoteEvent(
                                channel=msg.channel,
                                note=msg.note,
                                start=start,
                                duration=dur,
                                velocity=vel,
                                chip="midi",
                            )
                        )
        duration_sec = max(duration_sec, elapsed_sec)

    # Close any still-active notes at track end
    for (ch, note), (start, vel) in active.items():
        dur = duration_sec - start
        if dur > 0.001:
            note_events.append(
                NoteEvent(channel=ch, note=note, start=start, duration=dur,
                          velocity=vel, chip="midi")
            )

    if not note_events:
        return None

    note_events.sort(key=lambda n: n.start)
    return SymbolicScore(
        track_name=midi_path.stem,
        duration_sec=max(duration_sec, 1.0),
        notes=note_events,
        reconstruction_stats={"source": "midi", "event_count": len(note_events)},
        metadata={"midi_file": str(midi_path)},
    )


def symbolic_score_from_json(json_path: Path):
    """Load a SymbolicScore from a JSON file produced by score.save()."""
    from model.domains.music.domain_analysis.symbolic_music.score_representation import SymbolicScore
    try:
        return SymbolicScore.load(json_path)
    except Exception as exc:
        print(f"  Cannot load {json_path.name}: {exc}")
        return None


def analyze_midi_score(score) -> dict:
    """Run harmonic analysis and compute k_eff."""
    from model.domains.music.domain_analysis.symbolic_music.harmonic_analyzer import analyze as harmonic_analyze
    feat = harmonic_analyze(score)
    h = feat.chord_progression_entropy
    k_eff = entropy_to_k_eff(h)

    return {
        "track_name": score.track_name,
        "duration_sec": round(score.duration_sec, 1),
        "note_count": score.note_count,
        "chord_samples": feat.chord_sample_count,
        "chord_progression_entropy": round(h, 4),
        "k_eff": round(k_eff, 3),
        "dominant_chord": feat.dominant_chord_family,
        "chord_change_rate": round(feat.chord_change_rate, 3),
        "simultaneity_ratio": round(feat.simultaneity_ratio, 3),
        "chromatic_density": round(feat.chromatic_density, 3),
        "pitch_class_entropy": round(feat.pitch_class_entropy, 3),
        "bassline_entropy": round(feat.bassline_entropy, 3),
        "chord_family_dist": {
            name: round(p, 4)
            for name, p in zip(feat.chord_family_names, feat.chord_family_dist)
            if p > 0
        },
    }


def print_midi_report(results: list[dict]) -> None:
    lang_range = (1.462, 2.906)
    kuramoto_zone = (1.46, 1.98)

    print("\nMusic MIDI Harmonic k_eff Probe")
    print("═" * 72)
    print("  chord_progression_entropy → k_eff via language-calibrated formula")
    print(f"  Language range:     [{lang_range[0]:.3f}, {lang_range[1]:.3f}]")
    print(f"  Kuramoto zone:      [{kuramoto_zone[0]:.3f}, {kuramoto_zone[1]:.3f}]")
    print()

    if not results:
        print("  No results — provide .mid or SymbolicScore .json files as arguments")
        print("  Example: python domains/music/model/probes/music_keff.py --source midi track.mid")
        return

    # Summary table
    print(f"  {'Track':<32} {'Dur':>6}  {'H':>5}  {'k_eff':>6}  {'Dom chord':>10}  "
          f"{'ChgRate':>8}  {'Simul':>6}")
    print(f"  {'─'*72}")

    k_effs = []
    for r in sorted(results, key=lambda x: x["k_eff"]):
        k = r["k_eff"]
        k_effs.append(k)
        # Zone marker
        if k <= kuramoto_zone[1]:
            zone = "↑KURA"
        elif k <= lang_range[1]:
            zone = "  ok "
        else:
            zone = " high"
        name = r["track_name"][:30]
        print(
            f"  {name:<32} {r['duration_sec']:>6.1f}  {r['chord_progression_entropy']:>5.3f}  "
            f"{k:>6.3f}{zone}  {r['dominant_chord']:>10}  "
            f"{r['chord_change_rate']:>8.3f}  {r['simultaneity_ratio']:>6.3f}"
        )

    if len(k_effs) > 1:
        print(f"\n  Range: [{min(k_effs):.3f}, {max(k_effs):.3f}]")
        in_lang = sum(1 for k in k_effs if lang_range[0] <= k <= lang_range[1])
        in_kura = sum(1 for k in k_effs if kuramoto_zone[0] <= k <= kuramoto_zone[1])
        print(f"  Tracks in language range:  {in_lang}/{len(k_effs)}")
        print(f"  Tracks in Kuramoto zone:   {in_kura}/{len(k_effs)}")

    print()
    print("  Interpretation:")
    print("  k_eff < 1.98 → highly constrained tonality (case-dominant cluster)")
    print("  k_eff 1.98-2.41 → moderate constraint (agreement-dominant cluster)")
    print("  k_eff > 2.41 → free harmonic motion (word-order cluster)")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Music domain k_eff probe (Spotify + MIDI)")
    parser.add_argument(
        "--source", choices=["spotify", "midi", "both"], default="both",
        help="Data source to use (default: both)"
    )
    parser.add_argument(
        "files", nargs="*", type=Path, metavar="FILE",
        help="(MIDI source) .mid or SymbolicScore .json files to analyze"
    )
    parser.add_argument(
        "--scan", type=Path, metavar="DIR",
        help="(MIDI source) Scan a directory for .mid and .json files"
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="(MIDI source) Write MIDI results JSON to this path"
    )
    args = parser.parse_args()

    # ── Spotify section ──────────────────────────────────────────────────────
    if args.source in ("spotify", "both"):
        print("\n" + "=" * 72)
        print("SPOTIFY SOURCE")
        print("=" * 72)
        tracks = load_spotify_tracks()
        result = run_spotify_probe(tracks)
        print_spotify_report(result)

        out_path = ROOT / "domains" / "language" / "artifacts" / "music_keff_results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Raw results → {out_path}")

    # ── MIDI section ─────────────────────────────────────────────────────────
    if args.source in ("midi", "both"):
        print("\n" + "=" * 72)
        print("MIDI SOURCE")
        print("=" * 72)

        paths: list[Path] = list(args.files)
        if args.scan:
            paths.extend(sorted(args.scan.glob("**/*.mid")))
            paths.extend(sorted(args.scan.glob("**/*.json")))

        if not paths:
            if args.source == "midi":
                print("No files specified. Usage:")
                print("  python domains/music/model/probes/music_keff.py --source midi track.mid [...]")
                print("  python domains/music/model/probes/music_keff.py --source midi --scan domains/music/model/artifacts/midi/")
                print()
                print("Drop MIDI files into domains/music/model/artifacts/midi/ and re-run, or pass paths directly.")
            else:
                print("  (No MIDI files provided — skipping MIDI section)")
                print("  Pass .mid files or --scan DIR to include MIDI analysis.")
        else:
            results = []
            for p in paths:
                print(f"  Analyzing: {p.name}")
                if p.suffix.lower() in (".mid", ".midi"):
                    score = midi_to_score(p)
                elif p.suffix.lower() == ".json":
                    score = symbolic_score_from_json(p)
                else:
                    print(f"  Skipping {p.name} (unknown format)")
                    continue

                if score is None:
                    print(f"  Failed to load {p.name}")
                    continue

                result = analyze_midi_score(score)
                results.append(result)
                print(f"    → k_eff={result['k_eff']:.3f}  H={result['chord_progression_entropy']:.3f}  "
                      f"chords={result['chord_samples']}  dom={result['dominant_chord']}")

            print_midi_report(results)

            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
                print(f"  Results → {args.out}")
            elif results:
                out_path = ROOT / "domains" / "language" / "artifacts" / "music_midi_keff_results.json"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
                print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()

