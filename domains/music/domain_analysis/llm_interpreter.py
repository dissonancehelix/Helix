"""
llm_interpreter.py — LLM Interpretation Layer (Layer 9)
=========================================================
Generates research-grade insights from structured analysis outputs using
the Claude API. The LLM operates ONLY on structured summaries — never on
raw MIDI events, chip telemetry, or binary data.

Input:  structured analysis dicts (feature vectors, clusters, style maps,
        melodic/harmonic/arrangement summaries)
Output: research insight JSON with interpretations keyed by aspect

Design principle: The LLM is a hypothesis generator. It reads cleaned,
summarized analysis artifacts and produces musicological interpretations
at research-paper quality. It does not make up data — it synthesizes
what the analysis pipeline extracted.

Usage
-----
    from domains.music.analysis.llm_interpreter import interpret_corpus, interpret_track

    # Single track interpretation
    insight = interpret_track(track_result, composer="Masayuki Nagao")

    # Corpus-level interpretation (after full pipeline run)
    corpus_insight = interpret_corpus(
        profiles=composer_profiles,
        clusters=cluster_result,
        style_space=style_space_result,
        patterns=pattern_result,
        n_tracks=37,
        soundtrack="Sonic 3 & Knuckles",
    )
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anthropic SDK
# ---------------------------------------------------------------------------

try:
    import anthropic as _anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _anthropic = None  # type: ignore
    _HAS_ANTHROPIC = False
    log.debug("llm_interpreter: anthropic SDK not installed — interpretation unavailable")

# Default model: Opus for research-quality depth, Sonnet for fast batch processing
_DEFAULT_MODEL  = "claude-opus-4-6"
_FAST_MODEL     = "claude-sonnet-4-6"
_MAX_TOKENS     = 2048


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _fmt_key_val(d: dict | None, keys: list[str]) -> str:
    if not d:
        return "(unavailable)"
    parts = []
    for k in keys:
        v = d.get(k)
        if v is not None:
            parts.append(f"{k}={v}")
    return ", ".join(parts) if parts else "(no data)"


def _build_track_prompt(
    track_result: dict[str, Any],
    composer: str | None = None,
) -> str:
    tn   = track_result.get("track_name", "unknown")
    l1   = track_result.get("layer1", {}) or {}
    mel  = track_result.get("layer2_melodic", {}) or {}
    harm = track_result.get("layer2_harmonic", {}) or {}
    arr  = track_result.get("layer2_arrangement", {}) or {}
    key  = track_result.get("layer2_key", {}) or {}
    rhy  = track_result.get("layer2_rhythm", {}) or {}
    sym  = track_result.get("layer2_symbolic", {}) or {}
    ludo = track_result.get("ludomusicology", {}) or {}

    m21  = sym.get("music21", {}) or {}
    msf  = sym.get("musif", {}) or {}

    lines = [
        f"# Track Dialect Analysis: {tn}",
        f"Composer (known/predicted): {composer or 'unknown'}",
        "",
        "## chip_control dialect (Synthesis Layer)",
        f"  Duration: {l1.get('duration_sec')}s, KeyOn density: {l1.get('keyon_density')}/s",
        f"  Dominant algorithm: {l1.get('dominant_alg')}, Carrier brightness: {l1.get('carrier_brightness')}",
        f"  PSG/FM ratio: {l1.get('psg_to_fm_ratio')}, Silence: {l1.get('silence_ratio')}",
        f"  Rhythmic entropy: {l1.get('rhythmic_entropy')}, Pitch entropy: {l1.get('pitch_entropy')}",
        "",
        "## symbolic_music dialect (Musical Layer)",
        f"  Key: {key.get('key')} {key.get('mode')} (confidence {key.get('confidence')})",
        f"  Tempo: {rhy.get('tempo_bpm')} BPM, Syncopation: {rhy.get('syncopation')}, Beat regularity: {rhy.get('beat_regularity')}",
        f"  Phrases: {mel.get('phrase_count')}, Mean phrase length: {mel.get('phrase_len_mean')} notes",
        f"  Stepwise motion: {mel.get('stepwise_ratio')}, Leaps: {mel.get('leap_ratio')}",
        f"  Contour: up={mel.get('contour_up_ratio')}, down={mel.get('contour_down_ratio')}, same={mel.get('contour_same_ratio')}",
        f"  Repetition score: {mel.get('repetition_score')}, Motif 4-grams: {mel.get('motif_4gram_count')}",
        f"  Dominant chord family: {harm.get('dominant_chord_family')}",
        f"  Chord progression entropy: {harm.get('chord_progression_entropy')}",
        f"  Bassline: step={harm.get('bassline_step_ratio')}, leap={harm.get('bassline_leap_ratio')}",
        f"  Chromatic density: {harm.get('chromatic_density')}, Pitch class entropy: {harm.get('pitch_class_entropy')}",
    ]

    if m21:
        chords_str = " → ".join((m21.get("chord_sequence") or [])[:8])
        cads = m21.get("cadences") or []
        cad_types = [c.get("type") for c in cads[:4]]
        lines += [
            "",
            "## Computational Musicology (music21)",
            f"  Key: {m21.get('key')}, mode: {m21.get('mode')}, correlation: {m21.get('key_confidence')}",
            f"  Chord sequence (first 8): {chords_str}",
            f"  Cadences detected: {cad_types}",
            f"  Phrase count: {m21.get('phrase_count')}",
            f"  Contour (first 32): {(m21.get('contour_string') or '')[:32]}",
        ]

    if msf:
        lines += [
            "",
            "## musif Features",
            f"  Melodic complexity (LZ): {msf.get('melodic_complexity')}",
            f"  Tonal tension mean: {msf.get('tonal_tension_mean')}",
            f"  Harmonic rhythm: {msf.get('harmonic_rhythm')} changes/beat",
            f"  Interval entropy: {msf.get('interval_entropy')}",
            f"  Motif density: {msf.get('motif_density')}",
        ]

    if arr:
        lines += [
            "",
            "## Arrangement",
            f"  Lead channel: {arr.get('lead_channel')}, Bass channel: {arr.get('bass_channel')}",
            f"  Active channels: {arr.get('active_channels')}, Mean polyphony: {arr.get('mean_polyphony')}",
            f"  Section count: {arr.get('section_count')}, Breakdown fraction: {arr.get('breakdown_fraction')}",
            f"  Channel handoffs: {arr.get('handoff_count')}",
        ]

    if ludo:
        lines += [
            "",
            "## Ludomusicology",
            f"  Loop stability: {ludo.get('loop_stability_index')}",
            f"  Energy variance: {ludo.get('energy_curve_variance')}",
            f"  Gameplay role: {ludo.get('gameplay_role')} ({ludo.get('gameplay_role_confidence')})",
            f"  Loop cadence type: {ludo.get('loop_cadence_type')}",
        ]

    lines += [
        "",
        "---",
        "Provide a concise musicological interpretation of this track covering its HSL dialect translations:",
        "1. **Melodic character (symbolic_music)** — what is compositionally distinctive about the melodic writing?",
        "2. **Harmonic language** — tonal center usage, chord vocabulary, progression tendencies",
        "3. **Rhythmic feel** — tempo, groove, syncopation character",
        "4. **Synthesis identity (chip_control)** — how FM algorithm and operator choices shape the timbre",
        "5. **Attribution signal** — which features are stylistically distinctive for composer attribution?",
        "6. **Invariant discovery** — one novel observation about structural invariants detected across dialects",
        "",
        "Be concise (6 bullet points max). Use musicological terminology.",
    ]

    return "\n".join(lines)


def _build_corpus_prompt(
    profiles:    dict[str, Any],
    clusters:    dict[str, Any],
    style_space: dict[str, Any] | None,
    patterns:    dict[str, Any] | None,
    n_tracks:    int,
    soundtrack:  str,
) -> str:
    # Summarize composer profiles
    prof_summary: list[str] = []
    for composer, info in (profiles.get("known_profiles") or {}).items():
        centroid = info.get("centroid", [])[:8]
        prof_summary.append(
            f"  {composer}: {info.get('track_count')} tracks"
            f", fingerprint[0:8]={[round(x,3) for x in centroid]}"
        )

    # Attribution predictions
    pred_summary: list[str] = []
    for p in (profiles.get("unattributed_predictions") or [])[:8]:
        top = (p.get("centroid_pred") or [{}])[0]
        pred_summary.append(
            f"  {p['track_name']} → {top.get('composer','?')} ({top.get('score',0):.3f})"
        )

    # Cluster summary
    hdb = clusters.get("hdbscan", {}) or {}
    km  = clusters.get("kmeans", {}) or {}
    cos = clusters.get("cosine_clusters", {}) or {}

    # Network summary
    net = clusters.get("similarity_network", {}) or {}
    motifs = (patterns or {}).get("motif_families", [])[:5] if patterns else []

    lines = [
        f"# Corpus Analysis: {soundtrack} ({n_tracks} tracks)",
        "",
        "## Composer Profiles (centroid fingerprints)",
    ] + prof_summary + [
        "",
        "## Attribution Predictions (unattributed tracks)",
    ] + pred_summary + [
        "",
        "## Cluster Analysis",
        f"  HDBSCAN: {hdb.get('n_clusters')} clusters, silhouette={hdb.get('silhouette')}",
        f"  k-means:  {km.get('n_clusters')} clusters, silhouette={km.get('silhouette')}",
        f"  Cosine greedy (≥0.85): {cos.get('n_clusters')} clusters",
        "",
        "## Track Similarity Network",
        f"  Edges (sim≥{net.get('threshold')}): {net.get('edge_count')}, density={net.get('density')}",
        f"  Connected components: {net.get('components')}, modularity={net.get('modularity')}",
        "",
        "## Cross-Track Motif Families",
    ] + [
        f"  Motif '{m.get('motif','?')}': shared by {m.get('track_count')} tracks ({m.get('tracks',[])})"
        for m in motifs
    ] + [
        "",
        "---",
        f"Provide research-paper-level analysis of the {soundtrack} VGM corpus covering:",
        "1. **Composer style boundaries** — where do the fingerprint clusters align or diverge from known attributions?",
        "2. **Attribution confidence** — which unattributed tracks have strong vs ambiguous composer signals?",
        "3. **Cross-composer influence** — are there shared motifs or techniques that cross composer boundaries?",
        "4. **Structural archetypes** — what recurring musical structures define this soundtrack family?",
        "5. **Synthesis palette** — how do FM algorithm preferences differ between composers?",
        "6. **Historical context** — what does this analysis reveal about 1994 Sega Genesis compositional practice?",
        "",
        "Write 6 numbered paragraphs. Use musicological language. Be specific about track names and feature values.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# API caller
# ---------------------------------------------------------------------------

def _call_claude(prompt: str, model: str = _DEFAULT_MODEL) -> str | None:
    if not _HAS_ANTHROPIC:
        log.warning("llm_interpreter: anthropic not installed")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("llm_interpreter: ANTHROPIC_API_KEY not set")
        return None

    try:
        client = _anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            system=(
                "You are a computational musicologist specializing in video game music (VGM) "
                "analysis and FM synthesis within the Helix Structural Language (HSL) framework. "
                "You interpret translated musical dialects (chip_control, symbolic_music, etc.) "
                "to produce research-grade insights and discover structural invariants. "
                "You are precise, technically accurate, and write in the style of an academic musicology paper."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text if msg.content else None
    except Exception as exc:
        log.warning("llm_interpreter: API call failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def interpret_track(
    track_result: dict[str, Any],
    composer:     str | None = None,
    model:        str = _FAST_MODEL,
) -> dict[str, Any]:
    """
    Generate a musicological interpretation of a single track.
    Returns a dict with keys: track_name, composer, interpretation, model, available.
    """
    prompt = _build_track_prompt(track_result, composer)
    text   = _call_claude(prompt, model=model)

    return {
        "track_name":     track_result.get("track_name"),
        "composer":       composer,
        "interpretation": text,
        "model":          model,
        "available":      _HAS_ANTHROPIC and bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


def interpret_corpus(
    profiles:    dict[str, Any],
    clusters:    dict[str, Any],
    style_space: dict[str, Any] | None = None,
    patterns:    dict[str, Any] | None = None,
    n_tracks:    int = 0,
    soundtrack:  str = "VGM Soundtrack",
    model:       str = _DEFAULT_MODEL,
) -> dict[str, Any]:
    """
    Generate research-grade corpus insights after a full pipeline run.
    Returns dict with: interpretation, model, available.
    """
    prompt = _build_corpus_prompt(profiles, clusters, style_space, patterns, n_tracks, soundtrack)
    text   = _call_claude(prompt, model=model)

    return {
        "soundtrack":     soundtrack,
        "n_tracks":       n_tracks,
        "interpretation": text,
        "model":          model,
        "available":      _HAS_ANTHROPIC and bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


def available() -> bool:
    return _HAS_ANTHROPIC and bool(os.environ.get("ANTHROPIC_API_KEY"))
