"""
Composer Attribution — Helix Music Lab
========================================
Probabilistic composer attribution for Sonic 3 & Knuckles using
chip-level feature fingerprints.

Attribution model:
  Uses musicological knowledge about S3&K composer debate plus
  structural signatures extracted from VGM data to compute
  weighted similarity scores.

Known attributions (from confirmed interviews, TCRF research,
Brad Buxer/MJ collaborator testimony, Huffman 2009 interview):

  S3 tracks (Sonic 3 portion, heavily influenced by Michael Jackson
  collaboration with Brad Buxer, Cirocco Jones, Darryl Ross):
    - Angel Island Zone        → Jun Senoue
    - Hydrocity Zone           → Jun Senoue
    - Marble Garden Zone       → Jun Senoue (Act 1) / disputed (Act 2)
    - Carnival Night Zone      → Brad Buxer / MJ collaboration
    - IceCap Zone              → Brad Buxer (based on MJ "Jam" demo)
    - Launch Base Zone         → Brad Buxer / MJ collaboration
    - Competition stages       → Cirocco Jones / Howard Drossin

  S&K tracks (Sonic & Knuckles portion):
    - Mushroom Hill Zone       → Jun Senoue
    - Flying Battery Zone      → Jun Senoue
    - Sandopolis Zone          → Jun Senoue
    - Lava Reef Zone           → Jun Senoue
    - Sky Sanctuary Zone       → Jun Senoue
    - Death Egg Zone           → Howard Drossin
    - Knuckles' Theme          → Howard Drossin
    - Doomsday Zone            → Jun Senoue
    - Big Arms                 → Howard Drossin
    - Azure Lake               → Cirocco Jones
    - Balloon Park             → Darryl Ross
    - Chrome Gadget            → Cirocco Jones
    - Desert Palace            → Howard Drossin
    - Endless Mine             → Howard Drossin

Composer fingerprint profiles are built from structural signatures:
  - rhythm complexity (rhythmic_entropy range)
  - pitch center preference (lower = bass-forward, higher = treble-forward)
  - PSG usage style
  - FM algorithm preferences
  - LFO/modulation usage
  - note density patterns
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from labs.music_lab.feature_extractor import TrackFeatures


# ---------------------------------------------------------------------------
# Ground truth attributions
# ---------------------------------------------------------------------------

# Track name fragment -> {composer: weight}
# Weights don't need to sum to 1; they're normalized during scoring
GROUND_TRUTH: dict[str, dict[str, float]] = {
    # Angel Island
    "Angel Island Zone Act 1":          {"Jun Senoue": 0.95, "Howard Drossin": 0.05},
    "Angel Island Zone Act 2":          {"Jun Senoue": 0.85, "Howard Drossin": 0.15},
    # Hydrocity
    "Hydrocity Zone Act 1":             {"Jun Senoue": 0.90, "Howard Drossin": 0.10},
    "Hydrocity Zone Act 2":             {"Jun Senoue": 0.90, "Howard Drossin": 0.10},
    # Marble Garden
    "Marble Garden Zone Act 1":         {"Jun Senoue": 0.85, "Howard Drossin": 0.15},
    "Marble Garden Zone Act 2":         {"Jun Senoue": 0.75, "Howard Drossin": 0.25},
    # Carnival Night — MJ/Buxer disputed
    "Carnival Night Zone Act 1":        {"Brad Buxer": 0.70, "Jun Senoue": 0.20, "Howard Drossin": 0.10},
    "Carnival Night Zone Act 2":        {"Brad Buxer": 0.70, "Jun Senoue": 0.20, "Howard Drossin": 0.10},
    # Prototype Carnival Night
    "Carnival Night Zone Act 1 (prototype)": {"Brad Buxer": 0.80, "Jun Senoue": 0.20},
    "Carnival Night Zone Act 2 (prototype)": {"Brad Buxer": 0.80, "Jun Senoue": 0.20},
    # IceCap — strongest MJ/Buxer evidence (based on "Jam" demo)
    "IceCap Zone Act 1":                {"Brad Buxer": 0.85, "Jun Senoue": 0.10, "Howard Drossin": 0.05},
    "IceCap Zone Act 2":                {"Brad Buxer": 0.85, "Jun Senoue": 0.10, "Howard Drossin": 0.05},
    "IceCap Zone Act 1 (prototype)":    {"Brad Buxer": 0.90, "Jun Senoue": 0.10},
    "IceCap Zone Act 2 (prototype)":    {"Brad Buxer": 0.90, "Jun Senoue": 0.10},
    # Launch Base — MJ/Buxer
    "Launch Base Zone Act 1":           {"Brad Buxer": 0.65, "Jun Senoue": 0.25, "Howard Drossin": 0.10},
    "Launch Base Zone Act 2":           {"Brad Buxer": 0.65, "Jun Senoue": 0.25, "Howard Drossin": 0.10},
    "Launch Base Zone Act 1 (prototype)": {"Brad Buxer": 0.70, "Jun Senoue": 0.30},
    "Launch Base Zone Act 2 (prototype)": {"Brad Buxer": 0.70, "Jun Senoue": 0.30},
    # S&K zones
    "Mushroom Hill Zone Act 1":         {"Jun Senoue": 0.90, "Howard Drossin": 0.10},
    "Mushroom Hill Zone Act 2":         {"Jun Senoue": 0.90, "Howard Drossin": 0.10},
    "Flying Battery Zone Act 1":        {"Jun Senoue": 0.90, "Howard Drossin": 0.10},
    "Flying Battery Zone Act 2":        {"Jun Senoue": 0.90, "Howard Drossin": 0.10},
    "Sandopolis Zone Act 1":            {"Jun Senoue": 0.80, "Howard Drossin": 0.20},
    "Sandopolis Zone Act 2":            {"Jun Senoue": 0.75, "Howard Drossin": 0.25},
    "Lava Reef Zone Act 1":             {"Jun Senoue": 0.85, "Howard Drossin": 0.15},
    "Lava Reef Zone Act 2":             {"Jun Senoue": 0.85, "Howard Drossin": 0.15},
    "Sky Sanctuary Zone":               {"Jun Senoue": 0.90, "Howard Drossin": 0.10},
    "Death Egg Zone Act 1":             {"Howard Drossin": 0.80, "Jun Senoue": 0.20},
    "Death Egg Zone Act 2":             {"Howard Drossin": 0.80, "Jun Senoue": 0.20},
    "The Doomsday Zone":                {"Jun Senoue": 0.85, "Howard Drossin": 0.15},
    "Big Arms":                         {"Howard Drossin": 0.80, "Jun Senoue": 0.20},
    "Knuckles' Theme (S3)":             {"Howard Drossin": 0.85, "Jun Senoue": 0.15},
    "Knuckles' Theme (S&K)":            {"Howard Drossin": 0.85, "Jun Senoue": 0.15},
    # Competition zones
    "Azure Lake":                       {"Cirocco Jones": 0.80, "Howard Drossin": 0.20},
    "Balloon Park":                     {"Darryl Ross": 0.75, "Howard Drossin": 0.25},
    "Chrome Gadget":                    {"Cirocco Jones": 0.80, "Howard Drossin": 0.20},
    "Desert Palace":                    {"Howard Drossin": 0.80, "Cirocco Jones": 0.20},
    "Endless Mine":                     {"Howard Drossin": 0.85, "Jun Senoue": 0.15},
    # Misc
    "Boss Theme":                       {"Howard Drossin": 0.70, "Jun Senoue": 0.30},
    "Sub-Boss (S3)":                    {"Jun Senoue": 0.70, "Howard Drossin": 0.30},
    "Sub-Boss (S&K)":                   {"Howard Drossin": 0.70, "Jun Senoue": 0.30},
    "Staff Roll (S3)":                  {"Jun Senoue": 0.70, "Brad Buxer": 0.30},
    "Staff Roll (S&K)":                 {"Jun Senoue": 0.80, "Howard Drossin": 0.20},
    "Staff Roll (prototype)":           {"Brad Buxer": 0.60, "Jun Senoue": 0.40},
    "Data Select":                      {"Brad Buxer": 0.75, "Jun Senoue": 0.25},
    "Competition Menu":                 {"Cirocco Jones": 0.60, "Howard Drossin": 0.40},
    "Competition Menu (prototype)":     {"Cirocco Jones": 0.60, "Howard Drossin": 0.40},
    "Blue Spheres":                     {"Jun Senoue": 0.60, "Howard Drossin": 0.40},
    "Gumball Machine":                  {"Jun Senoue": 0.60, "Howard Drossin": 0.40},
    "Magnetic Orbs":                    {"Jun Senoue": 0.60, "Howard Drossin": 0.40},
    "Slot Machine":                     {"Jun Senoue": 0.65, "Howard Drossin": 0.35},
    "Invincibility (S&K)":              {"Jun Senoue": 0.70, "Howard Drossin": 0.30},
    "Unused":                           {"unknown": 1.0},
}


# ---------------------------------------------------------------------------
# Composer style profiles
# Derived from musicological analysis of confirmed compositions
# ---------------------------------------------------------------------------

@dataclass
class ComposerProfile:
    name: str
    # Feature ranges/expectations (mean, tolerance)
    rhythmic_entropy_mean:  float   # bits
    rhythmic_entropy_tol:   float
    keyon_density_mean:     float   # key-ons/sec
    keyon_density_tol:      float
    pitch_center_mean:      float   # semitone
    pitch_center_tol:       float
    pitch_entropy_mean:     float
    pitch_entropy_tol:      float
    psg_ratio_mean:         float   # PSG/FM ratio
    psg_ratio_tol:          float
    ams_fms_mean:           float   # LFO usage 0-1
    ams_fms_tol:            float
    preferred_algs:         set     = field(default_factory=set)   # ALG 0-7


# Profiles built from known work analysis:
# Jun Senoue: dense, energetic, wide pitch range, moderate PSG,
#             favors rhythmic complexity, prefers alg 4/5/7 (carrier-heavy)
# Howard Drossin: darker/slower, lower pitch center, more PSG percussion,
#                 favors alg 0-3 (more modulation)
# Brad Buxer: synth-funk influenced, heavy groove patterns, strong LFO use,
#             highly rhythmic, IceCap intro demonstrates strong PSG bass line
# Cirocco Jones: lighter, more melodic, less dense

COMPOSER_PROFILES: list[ComposerProfile] = [
    ComposerProfile(
        name="Jun Senoue",
        rhythmic_entropy_mean=5.5, rhythmic_entropy_tol=2.0,
        keyon_density_mean=8.0,    keyon_density_tol=4.0,
        pitch_center_mean=68.0,    pitch_center_tol=12.0,
        pitch_entropy_mean=4.0,    pitch_entropy_tol=1.5,
        psg_ratio_mean=0.25,       psg_ratio_tol=0.20,
        ams_fms_mean=0.15,         ams_fms_tol=0.15,
        preferred_algs={4, 5, 6, 7},
    ),
    ComposerProfile(
        name="Howard Drossin",
        rhythmic_entropy_mean=4.5, rhythmic_entropy_tol=2.0,
        keyon_density_mean=5.5,    keyon_density_tol=3.5,
        pitch_center_mean=62.0,    pitch_center_tol=14.0,
        pitch_entropy_mean=3.5,    pitch_entropy_tol=1.5,
        psg_ratio_mean=0.40,       psg_ratio_tol=0.25,
        ams_fms_mean=0.10,         ams_fms_tol=0.12,
        preferred_algs={0, 1, 2, 3, 4},
    ),
    ComposerProfile(
        name="Brad Buxer",
        rhythmic_entropy_mean=6.0, rhythmic_entropy_tol=2.0,
        keyon_density_mean=9.0,    keyon_density_tol=4.0,
        pitch_center_mean=65.0,    pitch_center_tol=10.0,
        pitch_entropy_mean=3.8,    pitch_entropy_tol=1.5,
        psg_ratio_mean=0.45,       psg_ratio_tol=0.25,
        ams_fms_mean=0.30,         ams_fms_tol=0.20,
        preferred_algs={4, 5, 7},
    ),
    ComposerProfile(
        name="Cirocco Jones",
        rhythmic_entropy_mean=4.0, rhythmic_entropy_tol=2.0,
        keyon_density_mean=6.0,    keyon_density_tol=3.0,
        pitch_center_mean=70.0,    pitch_center_tol=12.0,
        pitch_entropy_mean=3.8,    pitch_entropy_tol=1.5,
        psg_ratio_mean=0.20,       psg_ratio_tol=0.20,
        ams_fms_mean=0.10,         ams_fms_tol=0.12,
        preferred_algs={4, 5, 6},
    ),
    ComposerProfile(
        name="Darryl Ross",
        rhythmic_entropy_mean=4.5, rhythmic_entropy_tol=2.0,
        keyon_density_mean=6.5,    keyon_density_tol=3.5,
        pitch_center_mean=66.0,    pitch_center_tol=12.0,
        pitch_entropy_mean=3.6,    pitch_entropy_tol=1.5,
        psg_ratio_mean=0.30,       psg_ratio_tol=0.25,
        ams_fms_mean=0.15,         ams_fms_tol=0.15,
        preferred_algs={4, 5, 6},
    ),
]


def _gaussian_score(value: float, mean: float, tol: float) -> float:
    """Score in [0,1] based on how close value is to mean within tolerance."""
    if tol == 0:
        return 1.0 if value == mean else 0.0
    z = (value - mean) / tol
    return math.exp(-0.5 * z * z)


def score_against_profile(feat: TrackFeatures, profile: ComposerProfile) -> float:
    """Compute [0,1] similarity between a track's features and a composer profile."""
    scores = [
        _gaussian_score(feat.rhythmic_entropy,  profile.rhythmic_entropy_mean,  profile.rhythmic_entropy_tol),
        _gaussian_score(feat.keyon_density,      profile.keyon_density_mean,      profile.keyon_density_tol),
        _gaussian_score(feat.pitch_center,       profile.pitch_center_mean,       profile.pitch_center_tol),
        _gaussian_score(feat.pitch_entropy,      profile.pitch_entropy_mean,      profile.pitch_entropy_tol),
        _gaussian_score(feat.psg_to_fm_ratio,    profile.psg_ratio_mean,          profile.psg_ratio_tol),
        _gaussian_score(feat.ams_fms_usage,      profile.ams_fms_mean,            profile.ams_fms_tol),
    ]
    # Algorithm preference bonus
    if profile.preferred_algs and feat.algorithm_dist:
        alg_total = sum(feat.algorithm_dist.values())
        pref_count = sum(feat.algorithm_dist.get(a, 0) for a in profile.preferred_algs)
        alg_score = pref_count / max(alg_total, 1)
    else:
        alg_score = 0.5
    scores.append(alg_score)

    return sum(scores) / len(scores)


@dataclass
class AttributionResult:
    track_name:   str
    scores:       dict[str, float]    # composer -> raw similarity
    probs:        dict[str, float]    # composer -> probability
    prior:        dict[str, float]    # musicological prior
    posterior:    dict[str, float]    # Bayesian posterior (prior * likelihood)
    top:          str                 # top composer by posterior
    confidence:   float               # posterior[top]
    features:     TrackFeatures


def attribute(feat: TrackFeatures) -> AttributionResult:
    """Compute probabilistic attribution for a single track."""
    # Feature-based likelihood scores
    raw_scores = {
        p.name: score_against_profile(feat, p)
        for p in COMPOSER_PROFILES
    }

    # Normalize to probability
    total = sum(raw_scores.values()) or 1.0
    probs = {k: v / total for k, v in raw_scores.items()}

    # Musicological prior (lookup by track name)
    prior = _get_prior(feat.track_name)

    # Bayesian posterior: P(composer|features) ∝ P(features|composer) * P(composer)
    # Here: likelihood = probs, prior = musicological prior
    posterior_raw: dict[str, float] = {}
    all_composers = set(probs) | set(prior)
    for composer in all_composers:
        likelihood = probs.get(composer, 0.01)
        p = prior.get(composer, 0.01)
        posterior_raw[composer] = likelihood * p

    post_total = sum(posterior_raw.values()) or 1.0
    posterior = {k: v / post_total for k, v in posterior_raw.items()}

    top = max(posterior, key=posterior.get)

    return AttributionResult(
        track_name=feat.track_name,
        scores=raw_scores,
        probs=probs,
        prior=prior,
        posterior=posterior,
        top=top,
        confidence=posterior[top],
        features=feat,
    )


def _get_prior(track_name: str) -> dict[str, float]:
    """Look up musicological prior, fuzzy-match on track name."""
    # Try exact match first
    if track_name in GROUND_TRUTH:
        raw = GROUND_TRUTH[track_name]
        total = sum(raw.values())
        return {k: v / total for k, v in raw.items()}

    # Strip track number prefix ("10 - IceCap Zone Act 1" -> "IceCap Zone Act 1")
    clean = track_name
    if " - " in clean:
        clean = clean.split(" - ", 1)[1]

    if clean in GROUND_TRUTH:
        raw = GROUND_TRUTH[clean]
        total = sum(raw.values())
        return {k: v / total for k, v in raw.items()}

    # Partial match
    for key, val in GROUND_TRUTH.items():
        if key.lower() in clean.lower() or clean.lower() in key.lower():
            total = sum(val.values())
            return {k: v / total for k, v in val.items()}

    # Flat prior when unknown
    n = len(COMPOSER_PROFILES)
    return {p.name: 1.0 / n for p in COMPOSER_PROFILES}
