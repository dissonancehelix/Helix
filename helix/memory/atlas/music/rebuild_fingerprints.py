"""
rebuild_fingerprints.py — Recompute composer style signatures from full analysis corpus
========================================================================================

After new analysis runs complete, this script reads all analyzed artifact files
for each composer and recomputes the style_signature from the full corpus,
then writes it back into the composer entity files and the fingerprints artifact.

This closes the feedback loop:
    library analysis run → artifacts → rebuild_fingerprints → entity style_signature

The fingerprint is a mean across all hw/seq artifact symbolic sections for each
composer, using the same feature set as the calibration fingerprints.

Run:
    python codex/atlas/music/rebuild_fingerprints.py
    python codex/atlas/music/rebuild_fingerprints.py --composers "Miyoko Takaoka"
    python codex/atlas/music/rebuild_fingerprints.py --dry-run
"""
from __future__ import annotations
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)

ARTIFACTS_DIR  = ROOT / "domains" / "language" / "artifacts" / "analysis"
ARTISTS_DIR    = ROOT / "codex" / "atlas" / "music" / "artists"
FINGERPRINTS   = ROOT / "domains" / "language" / "artifacts" / "analysis" / "s3k_composer_fingerprints.json"
FIELD_INDEX    = ROOT / "codex" / "library" / "music" / ".field_index.json"

# Features to include in the recomputed fingerprint
SCALAR_FEATURES = [
    "pitch_entropy", "chromatic_intrusion_rate", "rhythmic_entropy",
    "off_beat_ratio", "motif_recurrence", "sustained_ratio",
    "register_separation", "groove_score", "bass_rhythmic_regularity",
    "melody_bass_independence", "harmonic_tension_score",
    "prevalence_of_tritones", "vertical_dissonance",
    "note_density", "avg_phrase_length", "phrase_regularity",
    "pulse_coherence", "interval_roughness", "tempo_bpm",
    "pre_seam_density_spike", "seam_sharpness",
    "emergence_index", "disappearance_index",
    "fm_unique_patches", "fm_timbre_reuse_ratio",
]
STRING_FEATURES = ["scale_mode", "melodic_contour", "dynamic_arc"]

S3K_COMPOSERS = [
    "Tatsuyuki Maeda", "Sachio Ogawa", "Tomonori Sawada", "Masaru Setsumaru",
    "Jun Senoue", "Masayuki Nagao", "Yoshiaki Kashima",
    "Masanori Hikichi", "Miyoko Takaoka",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[\s\-\/]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s.strip("_")


def load_field_index() -> dict:
    with open(FIELD_INDEX, encoding="utf-8") as f:
        return json.load(f)


def get_hw_seq_track_ids(composer_slug: str) -> list[str]:
    """Load pre-computed hw_seq_track_ids from entity file."""
    entity_file = ARTISTS_DIR / f"{composer_slug}.json"
    if not entity_file.exists():
        return []
    with open(entity_file, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("library", {}).get("hw_seq_track_ids", [])


def artifact_path_for(track_id: str) -> Path:
    """Convert track_id to artifact file path."""
    slug = track_id.replace(":", "_").replace(".", "_")
    return ARTIFACTS_DIR / f"{slug}.json"


def load_artifact_symbolic(track_id: str) -> dict | None:
    """Load the symbolic section from an analyzed artifact."""
    path = artifact_path_for(track_id)
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        sym = d.get("analysis", {}).get("symbolic") or {}
        if sym.get("error"):
            return None
        # Also pull from library_meta.symbolic_full if present (older format)
        if not sym:
            sym = d.get("analysis", {}).get("library_meta", {}).get("symbolic_full") or {}
        return sym if sym else None
    except Exception:
        return None


def compute_fingerprint(track_ids: list[str]) -> dict:
    """Compute mean scalar features + mode plurality across a list of track IDs."""
    scalar_accum: dict[str, list[float]] = defaultdict(list)
    string_accum: dict[str, list[str]]  = defaultdict(list)
    found = 0

    for t_id in track_ids:
        sym = load_artifact_symbolic(t_id)
        if sym is None:
            continue
        found += 1
        for feat in SCALAR_FEATURES:
            v = sym.get(feat)
            if v is not None and not isinstance(v, str):
                try:
                    fv = float(v)
                    if not math.isnan(fv):
                        scalar_accum[feat].append(fv)
                except (TypeError, ValueError):
                    pass
        for feat in STRING_FEATURES:
            v = sym.get(feat)
            if v and isinstance(v, str):
                string_accum[feat].append(v)

    result: dict = {"analyzed_track_count": found, "input_track_count": len(track_ids)}
    for feat in SCALAR_FEATURES:
        vals = scalar_accum.get(feat, [])
        result[feat] = round(sum(vals) / len(vals), 6) if vals else None
    for feat in STRING_FEATURES:
        vals = string_accum.get(feat, [])
        if vals:
            from collections import Counter
            result[feat] = Counter(vals).most_common(1)[0][0]
        else:
            result[feat] = None

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(target_names: list[str] | None = None, dry_run: bool = False) -> None:
    names = target_names or S3K_COMPOSERS

    # Load existing fingerprints file (to update in place)
    fp_data: dict = {"report": "s3k_composer_fingerprint_calibration", "composers": []}
    if FINGERPRINTS.exists():
        with open(FINGERPRINTS, encoding="utf-8") as f:
            fp_data = json.load(f)
    fp_by_name = {c["composer"]: c for c in fp_data.get("composers", [])}

    updated = []
    for name in names:
        slug = slugify(name)
        entity_file = ARTISTS_DIR / f"{slug}.json"
        if not entity_file.exists():
            print(f"  SKIP {name}: no entity file at {entity_file.name}")
            continue

        track_ids = get_hw_seq_track_ids(slug)
        if not track_ids:
            print(f"  SKIP {name}: no hw_seq_track_ids in entity file")
            continue

        print(f"  {name}: computing fingerprint from {len(track_ids)} tracks...", end=" ", flush=True)
        fp = compute_fingerprint(track_ids)
        print(f"{fp['analyzed_track_count']} artifacts found  mode={fp.get('scale_mode','?')}")

        if fp["analyzed_track_count"] == 0:
            print(f"    WARNING: no analyzed artifacts found — skipping update")
            continue

        if dry_run:
            continue

        # Update entity file style_signature
        with open(entity_file, encoding="utf-8") as f:
            entity = json.load(f)

        sig = {k: v for k, v in fp.items() if k not in ("input_track_count",)}
        sig["calibration_track_count"] = fp["analyzed_track_count"]
        sig["source"] = "rebuild_fingerprints.py (full corpus)"
        entity["style_signature"] = sig
        entity_file.write_text(json.dumps(entity, indent=2, ensure_ascii=False), encoding="utf-8")

        # Update fingerprints artifact
        fp_entry = dict(fp_by_name.get(name, {"composer": name}))
        fp_entry["composer"]    = name
        fp_entry["track_count"] = fp["analyzed_track_count"]
        for k, v in fp.items():
            if k not in ("analyzed_track_count", "input_track_count"):
                fp_entry[k] = v
        fp_by_name[name] = fp_entry
        updated.append(name)

    if not dry_run and updated:
        fp_data["composers"] = list(fp_by_name.values())
        FINGERPRINTS.write_text(json.dumps(fp_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nUpdated {len(updated)} composer fingerprints → {FINGERPRINTS.name}")
        print("Run build_composer_entities.py to sync registry.json")
    elif dry_run:
        print("\n[dry-run] no files written")
    else:
        print("\nNothing updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild composer fingerprints from analyzed artifacts")
    parser.add_argument("--composers", nargs="+", metavar="NAME")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(args.composers, args.dry_run)
