"""
gameplay_role.py — Gameplay Function Classification
====================================================
Classifies VGM tracks into likely gameplay roles using a rule-based
classifier operating on symbolic and ludomusicological features.

Roles: exploration | boss | menu | tension | cutscene | bonus | special |
       jingle | ambient | unknown

Classification uses a scored decision tree on:
  - tempo (boss/tension = high, ambient/cutscene = low)
  - loop_stability (boss/exploration = stable, cutscene = unstable)
  - energy_variance (tension/boss = high, menu/ambient = low)
  - harmonic_rhythm (boss = fast, ambient = slow)
  - psg_to_fm_ratio (noise channels → action feel)
  - duration (jingles = short < 15s, full tracks = long > 45s)
  - chord_progression_entropy (exploration = mid, boss = high)
  - breakdown_fraction (cutscene = high silence)

API
---
classify(features) -> GameplayRoleResult
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ROLES = [
    "boss",
    "exploration",
    "tension",
    "menu",
    "cutscene",
    "bonus",
    "special",
    "jingle",
    "ambient",
    "unknown",
]


@dataclass
class GameplayRoleResult:
    gameplay_role:            str
    gameplay_role_confidence: float          # 0–1
    role_scores:              dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "gameplay_role":            self.gameplay_role,
            "gameplay_role_confidence": round(self.gameplay_role_confidence, 3),
            "role_scores": {k: round(v, 3) for k, v in self.role_scores.items()},
        }


def classify(features: dict[str, Any]) -> GameplayRoleResult:
    """
    Classify a track's gameplay role from its analysis features.

    features dict can contain any subset of:
      layer1:              dict with duration_sec, keyon_density, psg_to_fm_ratio,
                           rhythmic_entropy
      layer2_rhythm:       dict with tempo_bpm, syncopation, beat_regularity
      layer2_harmonic:     dict with chord_progression_entropy, harmonic_rhythm,
                           chromatic_density
      layer2_arrangement:  dict with breakdown_fraction, section_count
      ludomusicology:      dict with loop_stability_index, energy_variance,
                           energy_ramp_type
    """
    l1   = features.get("layer1", {}) or {}
    rhy  = features.get("layer2_rhythm", {}) or {}
    harm = features.get("layer2_harmonic", {}) or {}
    arr  = features.get("layer2_arrangement", {}) or {}
    ludo = features.get("ludomusicology", {}) or {}

    duration        = float(l1.get("duration_sec", 60.0) or 60.0)
    tempo           = float(rhy.get("tempo_bpm", 120.0) or 120.0)
    syncopation     = float(rhy.get("syncopation", 0.0) or 0.0)
    beat_reg        = float(rhy.get("beat_regularity", 0.5) or 0.5)
    psg_ratio       = float(l1.get("psg_to_fm_ratio", 0.0) or 0.0)
    keyon_density   = float(l1.get("keyon_density", 0.0) or 0.0)
    rhy_entropy     = float(l1.get("rhythmic_entropy", 0.0) or 0.0)
    chord_entropy   = float(harm.get("chord_progression_entropy", 0.0) or 0.0)
    chrom_density   = float(harm.get("chromatic_density", 0.0) or 0.0)
    breakdown_frac  = float(arr.get("breakdown_fraction", 0.0) or 0.0)
    section_count   = int(arr.get("section_count", 1) or 1)
    loop_stability  = float(ludo.get("loop_stability_index", 0.5) or 0.5)
    energy_var      = float(ludo.get("energy_curve_variance", 0.1) or 0.1)
    ramp_type       = str(ludo.get("energy_ramp_type", "flat") or "flat")

    scores: dict[str, float] = {role: 0.0 for role in ROLES}

    # --- JINGLE (short stings < 15s) ---
    if duration < 15.0:
        scores["jingle"] += 0.7
        if duration < 6.0:
            scores["jingle"] += 0.2

    # --- BOSS ---
    if tempo > 160:
        scores["boss"] += 0.25
    if tempo > 140:
        scores["boss"] += 0.15
    if syncopation > 0.4:
        scores["boss"] += 0.15
    if keyon_density > 10:
        scores["boss"] += 0.1
    if chord_entropy > 0.6:
        scores["boss"] += 0.1
    if energy_var > 0.05:
        scores["boss"] += 0.1
    if beat_reg > 0.6 and tempo > 130:
        scores["boss"] += 0.1

    # --- TENSION ---
    if 90 < tempo < 160 and chord_entropy > 0.5:
        scores["tension"] += 0.2
    if chrom_density > 0.5:
        scores["tension"] += 0.2
    if ramp_type in ("build", "arch"):
        scores["tension"] += 0.15
    if section_count >= 4:
        scores["tension"] += 0.1
    if energy_var > 0.06:
        scores["tension"] += 0.1

    # --- EXPLORATION ---
    if 80 <= tempo <= 150:
        scores["exploration"] += 0.15
    if 0.3 <= chord_entropy <= 0.65:
        scores["exploration"] += 0.15
    if loop_stability >= 0.6:
        scores["exploration"] += 0.2
    if beat_reg >= 0.5:
        scores["exploration"] += 0.1
    if ramp_type == "flat":
        scores["exploration"] += 0.1
    if duration >= 45:
        scores["exploration"] += 0.1

    # --- MENU ---
    if tempo < 120:
        scores["menu"] += 0.2
    if chord_entropy < 0.4:
        scores["menu"] += 0.15
    if breakdown_frac > 0.15:
        scores["menu"] += 0.1
    if loop_stability >= 0.7:
        scores["menu"] += 0.1
    if syncopation < 0.2:
        scores["menu"] += 0.1

    # --- CUTSCENE ---
    if breakdown_frac > 0.30:
        scores["cutscene"] += 0.3
    if loop_stability < 0.3:
        scores["cutscene"] += 0.2
    if section_count >= 5:
        scores["cutscene"] += 0.15
    if duration > 60 and ramp_type in ("arch", "build"):
        scores["cutscene"] += 0.15

    # --- BONUS ---
    if 110 <= tempo <= 170 and psg_ratio > 0.15:
        scores["bonus"] += 0.2
    if syncopation > 0.3 and beat_reg > 0.55:
        scores["bonus"] += 0.15
    if loop_stability >= 0.6 and tempo > 120:
        scores["bonus"] += 0.1

    # --- SPECIAL STAGE ---
    if 90 <= tempo <= 140 and psg_ratio > 0.1 and rhy_entropy > 0.4:
        scores["special"] += 0.2
    if chord_entropy < 0.4 and beat_reg > 0.6:
        scores["special"] += 0.1

    # --- AMBIENT ---
    if tempo < 80:
        scores["ambient"] += 0.3
    if keyon_density < 3:
        scores["ambient"] += 0.2
    if breakdown_frac > 0.2:
        scores["ambient"] += 0.1
    if chord_entropy < 0.3:
        scores["ambient"] += 0.1

    # Normalize scores
    total = sum(scores.values())
    if total > 0:
        scores = {k: round(v / total, 4) for k, v in scores.items()}
    else:
        scores["unknown"] = 1.0

    best_role = max(scores, key=lambda r: scores[r])
    confidence = scores[best_role]

    return GameplayRoleResult(
        gameplay_role=best_role,
        gameplay_role_confidence=confidence,
        role_scores=scores,
    )
