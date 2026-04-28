"""
cross_era.py — Cross-Era Composer Reasoning
=============================================
Compares ArtistStyleVector snapshots from different hardware eras to
detect musical similarities and explain differences caused by platform
constraints.

Design principle:
    Hardware constraints explain observed differences.
    Musical cognition features identify the same composer.

Example use case:
    Motoi Sakuraba — YM2612 era (El Viento, 1991, Genesis)
    vs. Motoi Sakuraba — orchestral era (Dark Souls, 2011, PS3)

    Expected output:
      - SIMILAR:  melodic interval behavior (wide leaps, specific contour)
      - SIMILAR:  harmonic motion patterns (modulation frequency)
      - SIMILAR:  rhythmic motif reuse (distinctive patterns)
      - DIFFERENT: brightness (YM2612 harsh FM vs. orchestral warmth)
      - DIFFERENT: spectral centroid (chip frequencies vs. sample-based)
      - EXPLANATION: brightness/timbral differences attributed to hardware

Atlas integration:
    CrossEraAnalyzer produces relationship annotations:
      - ArtistStyleVector SIMILAR_TO ArtistStyleVector (musical cognition match)
      - ArtistStyleVector DIVERGES_FROM ArtistStyleVector (hardware era divergence)
      - ArtistStyleVector ATTRIBUTED_TO Composer (both vectors)
"""
from __future__ import annotations

import math
from typing import Any


class CrossEraAnalyzer:
    """
    Compares two ArtistStyleVector snapshots for the same (or different) composer.

    Usage:
        analyzer = CrossEraAnalyzer()
        result = analyzer.compare(
            vector_a=style_vector_ym2612,
            vector_b=style_vector_orchestral,
            composer_id="music.composer:motoi_sakuraba",
        )
    """

    # Thresholds for similarity classification
    SIMILAR_THRESHOLD  = 0.75  # cosine similarity >= this → SIMILAR
    DIVERGENT_THRESHOLD = 0.40  # cosine similarity < this → DIVERGES_FROM

    def compare(
        self,
        vector_a: dict[str, Any],
        vector_b: dict[str, Any],
        composer_id: str | None = None,
        label_a: str = "era_a",
        label_b: str = "era_b",
    ) -> dict[str, Any]:
        """
        Compare two ArtistStyleVectors and produce a similarity report.

        Returns:
            {
                "composer_id":          str | None,
                "similarity_scores":    dict,    # feature category → cosine similarity
                "overall_similarity":   float,   # weighted average across musical features
                "cognition_similarity": float,   # musical cognition only (melodic/harmonic/rhythmic)
                "hardware_divergence":  float,   # timbral divergence (attributed to hardware)
                "findings":             list[dict],  # per-feature explanations
                "relationship":         str,     # SIMILAR_TO | DIVERGES_FROM | MIXED
                "attribution_note":     str,     # natural language summary
            }
        """
        scores: dict[str, float] = {}
        findings: list[dict] = []

        # Musical cognition features (define identity)
        mel_sim = self._compare_melodic(
            vector_a.get("melodic_features", {}),
            vector_b.get("melodic_features", {}),
        )
        scores["melodic"] = mel_sim
        findings.append(self._finding("melodic_features", mel_sim, label_a, label_b,
                                      is_hardware=False))

        harm_sim = self._compare_harmonic(
            vector_a.get("harmonic_features", {}),
            vector_b.get("harmonic_features", {}),
        )
        scores["harmonic"] = harm_sim
        findings.append(self._finding("harmonic_features", harm_sim, label_a, label_b,
                                      is_hardware=False))

        rhy_sim = self._compare_rhythmic(
            vector_a.get("rhythmic_features", {}),
            vector_b.get("rhythmic_features", {}),
        )
        scores["rhythmic"] = rhy_sim
        findings.append(self._finding("rhythmic_features", rhy_sim, label_a, label_b,
                                      is_hardware=False))

        mot_sim = self._compare_motivic(
            vector_a.get("motivic_features", {}),
            vector_b.get("motivic_features", {}),
        )
        scores["motivic"] = mot_sim
        findings.append(self._finding("motivic_features", mot_sim, label_a, label_b,
                                      is_hardware=False))

        # Structural features
        str_sim = self._compare_structural(
            vector_a.get("structural_features", {}),
            vector_b.get("structural_features", {}),
        )
        scores["structural"] = str_sim
        findings.append(self._finding("structural_features", str_sim, label_a, label_b,
                                      is_hardware=False))

        # Timbral features — hardware-influenced
        tim_sim = self._compare_timbral(
            vector_a.get("timbral_features", {}),
            vector_b.get("timbral_features", {}),
        )
        scores["timbral"] = tim_sim
        findings.append(self._finding("timbral_features", tim_sim, label_a, label_b,
                                      is_hardware=True,
                                      hardware_note="Timbral differences reflect hardware constraints, not composer identity."))

        # Weighted similarity — cognition features weighted 3x timbral
        cognition_scores = [mel_sim, harm_sim, rhy_sim, mot_sim, str_sim]
        timbral_score    = [tim_sim]

        cog_sim = sum(cognition_scores) / len(cognition_scores)
        tim_div = 1.0 - tim_sim   # divergence = complement of similarity

        # Overall: 80% cognition, 20% timbral
        overall = round(0.8 * cog_sim + 0.2 * tim_sim, 4)

        # Relationship classification
        if cog_sim >= self.SIMILAR_THRESHOLD:
            relationship = "SIMILAR_TO"
        elif cog_sim < self.DIVERGENT_THRESHOLD:
            relationship = "DIVERGES_FROM"
        else:
            relationship = "MIXED"

        # Context explanation
        ctx_a = vector_a.get("context_metadata", {})
        ctx_b = vector_b.get("context_metadata", {})
        chips_a   = ctx_a.get("chips_used", [])
        chips_b   = ctx_b.get("chips_used", [])
        era_a     = ctx_a.get("era_range")
        era_b     = ctx_b.get("era_range")

        attribution_note = self._build_attribution_note(
            composer_id, cog_sim, tim_div,
            chips_a, chips_b, era_a, era_b,
            label_a, label_b,
        )

        return {
            "composer_id":          composer_id,
            "label_a":              label_a,
            "label_b":              label_b,
            "similarity_scores":    {k: round(v, 4) for k, v in scores.items()},
            "overall_similarity":   overall,
            "cognition_similarity": round(cog_sim, 4),
            "hardware_divergence":  round(tim_div, 4),
            "findings":             findings,
            "relationship":         relationship,
            "attribution_note":     attribution_note,
        }

    # ── Per-feature comparisons ────────────────────────────────────────────

    def _compare_melodic(self, a: dict, b: dict) -> float:
        sims = []

        # Interval distributions — cosine similarity
        ia = a.get("interval_distribution", {})
        ib = b.get("interval_distribution", {})
        if ia and ib:
            sims.append(self._cosine_dicts(ia, ib))

        # Leap frequency — scalar proximity
        lf_a = a.get("leap_frequency")
        lf_b = b.get("leap_frequency")
        if lf_a is not None and lf_b is not None:
            sims.append(1.0 - min(abs(float(lf_a) - float(lf_b)), 1.0))

        # Melodic contour bias
        mc_a = a.get("melodic_contour_bias")
        mc_b = b.get("melodic_contour_bias")
        if mc_a is not None and mc_b is not None:
            sims.append(1.0 - min(abs(float(mc_a) - float(mc_b)), 1.0))

        return _mean_or_zero(sims)

    def _compare_harmonic(self, a: dict, b: dict) -> float:
        sims = []

        ca = a.get("chord_type_distribution", {})
        cb = b.get("chord_type_distribution", {})
        if ca and cb:
            sims.append(self._cosine_dicts(ca, cb))

        mf_a = a.get("modulation_frequency")
        mf_b = b.get("modulation_frequency")
        if mf_a is not None and mf_b is not None:
            max_mf = max(abs(float(mf_a)), abs(float(mf_b)), 1.0)
            sims.append(1.0 - min(abs(float(mf_a) - float(mf_b)) / max_mf, 1.0))

        return _mean_or_zero(sims)

    def _compare_rhythmic(self, a: dict, b: dict) -> float:
        sims = []

        for key in ("syncopation_score", "note_density_mean", "tempo_mean"):
            va = a.get(key)
            vb = b.get(key)
            if va is not None and vb is not None:
                denom = max(abs(float(va)), abs(float(vb)), 1.0)
                sims.append(1.0 - min(abs(float(va) - float(vb)) / denom, 1.0))

        return _mean_or_zero(sims)

    def _compare_structural(self, a: dict, b: dict) -> float:
        sims = []
        for key in ("track_length_mean", "phrase_count_mean", "section_transition_freq"):
            va = a.get(key)
            vb = b.get(key)
            if va is not None and vb is not None:
                denom = max(abs(float(va)), abs(float(vb)), 1.0)
                sims.append(1.0 - min(abs(float(va) - float(vb)) / denom, 1.0))
        return _mean_or_zero(sims)

    def _compare_timbral(self, a: dict, b: dict) -> float:
        """Timbral similarity — lower = more hardware divergence."""
        sims = []

        for key in ("brightness_mean", "spectral_centroid_mean", "dynamic_range_mean"):
            va = a.get(key)
            vb = b.get(key)
            if va is not None and vb is not None:
                denom = max(abs(float(va)), abs(float(vb)), 1.0)
                sims.append(1.0 - min(abs(float(va) - float(vb)) / denom, 1.0))

        bd_a = a.get("brightness_distribution")
        bd_b = b.get("brightness_distribution")
        if bd_a and bd_b and len(bd_a) == len(bd_b):
            sims.append(self._cosine_lists(bd_a, bd_b))

        return _mean_or_zero(sims)

    def _compare_motivic(self, a: dict, b: dict) -> float:
        sims = []

        me_a = a.get("motif_entropy")
        me_b = b.get("motif_entropy")
        if me_a is not None and me_b is not None:
            denom = max(abs(float(me_a)), abs(float(me_b)), 1.0)
            sims.append(1.0 - min(abs(float(me_a) - float(me_b)) / denom, 1.0))

        mr_a = a.get("motif_repetition_frequency")
        mr_b = b.get("motif_repetition_frequency")
        if mr_a is not None and mr_b is not None:
            sims.append(1.0 - min(abs(float(mr_a) - float(mr_b)), 1.0))

        return _mean_or_zero(sims)

    # ── Cosine similarity utilities ───────────────────────────────────────

    def _cosine_dicts(self, a: dict, b: dict) -> float:
        """Cosine similarity between two frequency distributions (as dicts)."""
        keys = set(a.keys()) | set(b.keys())
        if not keys:
            return 0.0
        va = [float(a.get(k, 0.0)) for k in keys]
        vb = [float(b.get(k, 0.0)) for k in keys]
        return self._cosine_lists(va, vb)

    def _cosine_lists(self, a: list, b: list) -> float:
        """Cosine similarity between two numeric lists."""
        if len(a) != len(b) or not a:
            return 0.0
        dot  = sum(x * y for x, y in zip(a, b))
        na   = math.sqrt(sum(x * x for x in a))
        nb   = math.sqrt(sum(y * y for y in b))
        denom = na * nb
        return round(dot / denom, 6) if denom > 0 else 0.0

    # ── Helpers ───────────────────────────────────────────────────────────

    def _finding(
        self,
        category: str,
        similarity: float,
        label_a: str,
        label_b: str,
        is_hardware: bool = False,
        hardware_note: str = "",
    ) -> dict[str, Any]:
        if similarity >= self.SIMILAR_THRESHOLD:
            verdict = "SIMILAR"
        elif similarity < self.DIVERGENT_THRESHOLD:
            verdict = "DIVERGENT"
        else:
            verdict = "PARTIAL"

        result = {
            "category":    category,
            "similarity":  round(similarity, 4),
            "verdict":     verdict,
            "label_a":     label_a,
            "label_b":     label_b,
            "is_hardware": is_hardware,
        }
        if is_hardware and hardware_note:
            result["hardware_note"] = hardware_note
        return result

    def _build_attribution_note(
        self,
        composer_id: str | None,
        cog_sim: float,
        tim_div: float,
        chips_a: list,
        chips_b: list,
        era_a: Any,
        era_b: Any,
        label_a: str,
        label_b: str,
    ) -> str:
        comp_name = composer_id.split(":")[-1].replace("_", " ").title() if composer_id else "The composer"
        sim_desc  = "highly similar" if cog_sim >= 0.75 else ("partially similar" if cog_sim >= 0.5 else "divergent")
        chip_desc_a = ", ".join(chips_a) if chips_a else label_a
        chip_desc_b = ", ".join(chips_b) if chips_b else label_b

        note = (
            f"{comp_name} shows {sim_desc} musical cognition patterns "
            f"between {label_a} ({chip_desc_a}) and {label_b} ({chip_desc_b}). "
        )
        if tim_div > 0.4:
            note += (
                f"Timbral divergence ({tim_div:.0%}) is attributed to hardware constraints "
                f"rather than compositional intent. "
            )
        if era_a and era_b:
            note += f"Era range: {era_a} → {era_b}."
        return note.strip()


# ── Helpers ────────────────────────────────────────────────────────────────

def _mean_or_zero(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
