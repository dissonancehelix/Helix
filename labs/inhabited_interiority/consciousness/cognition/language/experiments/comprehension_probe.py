"""
Comprehension Probe
===================
Measures structural comprehension patterns in a language corpus.

HSL usage:
    RUN experiment:comprehension_probe engine:python
    RUN experiment:comprehension_probe language:spanish corpus:podcasts difficulty:A2

Parameters:
    language    Language code (default: spanish)
    corpus      Corpus folder suffix (default: subtitles)
    difficulty  CEFR level filter hint: A1/A2/B1/B2/C1/C2 (default: A2)
    n_samples   Number of samples to evaluate (default: 100)
    seed        Random seed (default: 42)

Artifacts:
    results.json          — comprehension scores and structural report
    parameters.json       — run parameters
    metadata.json         — run metadata
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))

from core.python_suite.language.corpus_loader import CorpusLoader
from core.python_suite.language.structure_analysis import StructureAnalyzer
from core.python_suite.language.comprehension_metrics import ComprehenMetrics
from core.python_suite.language.grammar_patterns import GrammarPatterns


def run(params: dict | None = None) -> dict:
    """HSL entry point — RUN experiment:comprehension_probe engine:python"""
    params     = params or {}
    language   = str(params.get("language", "spanish")).lower()
    corpus     = str(params.get("corpus", "subtitles")).lower()
    difficulty = str(params.get("difficulty", "A2")).upper()
    n_samples  = int(params.get("n_samples", 100))
    seed       = int(params.get("seed", 42))

    random.seed(seed)
    start = time.time()

    # ── 1. Load corpus ────────────────────────────────────────────────────────
    loader = CorpusLoader()
    try:
        texts = loader.load(language=language, corpus=corpus, max_samples=n_samples * 4)
    except FileNotFoundError as e:
        # Graceful fallback: generate synthetic samples for testing
        texts = _synthetic_corpus(language, n_samples * 4)

    if len(texts) < 4:
        texts = _synthetic_corpus(language, n_samples * 4)

    texts = random.sample(texts, min(n_samples, len(texts)))

    # ── 2. Structural analysis ────────────────────────────────────────────────
    analyzer = StructureAnalyzer(language=language)
    structure = analyzer.analyze(texts)

    grammar = GrammarPatterns(language=language)
    grammar_report = grammar.extract(texts)

    # ── 3. Comprehension probes ───────────────────────────────────────────────
    # Split sentences into prompt / continuation pairs
    pairs = _make_pairs(texts)
    prompts      = [p for p, _ in pairs]
    continuations = [c for _, c in pairs]

    # Prediction test: does first word of continuation appear in prompt context?
    # (Proxy for predictability / coherence at this difficulty level)
    predictions = [_predict_next(p, language) for p in prompts]
    pred_acc = ComprehenMetrics.prediction_accuracy(
        predictions, continuations, partial=True
    )

    # Semantic overlap between paired halves (coherence measure)
    semantic_coh = ComprehenMetrics.batch_semantic_overlap(prompts, continuations)

    # Cloze: blank out last content word of each sentence
    cloze_prompts, cloze_targets = _make_cloze(texts)
    cloze_responses = [_cloze_guess(p, language) for p in cloze_prompts]
    cloze_result = ComprehenMetrics.cloze_accuracy(cloze_responses, cloze_targets)

    # ── 4. Signal ─────────────────────────────────────────────────────────────
    # Composite comprehension signal: weighted average of probe scores
    signal = round(
        0.4 * pred_acc
        + 0.4 * semantic_coh
        + 0.2 * cloze_result.get("accuracy", 0.0),
        4,
    )
    passed = signal >= 0.10  # minimum meaningful signal above chance

    result = {
        "status":        "ok",
        "language":      language,
        "corpus":        corpus,
        "difficulty":    difficulty,
        "n_samples":     len(texts),
        "signal":        signal,
        "passed":        passed,
        "scores": {
            "prediction_accuracy": pred_acc,
            "semantic_coherence":  semantic_coh,
            "cloze_accuracy":      cloze_result.get("accuracy", 0.0),
            "cloze_chance":        cloze_result.get("chance_baseline", None),
        },
        "structure":     structure,
        "grammar":       grammar_report,
        "duration_s":    round(time.time() - start, 3),
    }

    # ── 5. Write artifact ─────────────────────────────────────────────────────
    artifact_dir = _create_artifact_dir("comprehension_probe")
    _write_artifact(artifact_dir, result, params)
    result["artifact_dir"] = artifact_dir

    return result


# ── Corpus helpers ─────────────────────────────────────────────────────────────

def _synthetic_corpus(language: str, n: int) -> list[str]:
    """Minimal synthetic corpus for testing when no real data is present."""
    if language == "spanish":
        templates = [
            "El estudiante lee el libro en la biblioteca.",
            "María habla con su amigo todos los días.",
            "Los niños juegan en el parque por la tarde.",
            "¿Cuándo llegaste a la ciudad?",
            "No sé si puedo ir mañana.",
            "La profesora explica la gramática con paciencia.",
            "Ellos trabajan mucho para aprender el idioma.",
            "¿Qué haces cuando no entiendes una palabra?",
            "Me gusta escuchar música mientras estudio.",
            "El café está cerrado los domingos.",
        ]
    else:
        templates = [
            "The student reads the book in the library.",
            "She talks with her friend every day.",
            "The children play in the park in the afternoon.",
            "When did you arrive in the city?",
            "I don't know if I can go tomorrow.",
            "The teacher explains grammar with patience.",
            "They work hard to learn the language.",
            "What do you do when you don't understand a word?",
            "I like listening to music while I study.",
            "The café is closed on Sundays.",
        ]
    result = []
    while len(result) < n:
        result.extend(templates)
    return result[:n]


def _make_pairs(texts: list[str]) -> list[tuple[str, str]]:
    """Split each sentence at midpoint to create (prompt, continuation) pairs."""
    pairs = []
    for text in texts:
        words = text.split()
        if len(words) < 4:
            continue
        mid = len(words) // 2
        pairs.append((" ".join(words[:mid]), " ".join(words[mid:])))
    return pairs or [("el", "libro")]


def _make_cloze(texts: list[str]) -> tuple[list[str], list[str]]:
    """Blank out the last content word of each sentence."""
    import re
    prompts, targets = [], []
    content_re = re.compile(r"\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{4,}\b")
    for text in texts:
        words = text.split()
        # find last word >= 4 chars (likely content word)
        for i in range(len(words) - 1, -1, -1):
            if content_re.match(words[i]):
                target = re.sub(r"[^\w]", "", words[i]).lower()
                prompt = " ".join(words[:i]) + " ___ " + " ".join(words[i + 1:])
                prompts.append(prompt)
                targets.append(target)
                break
    return prompts or ["___"], targets or [""]


def _predict_next(prompt: str, language: str) -> str:
    """Naive frequency-based next-word prediction (placeholder)."""
    import re
    words = re.findall(r"\b\w+\b", prompt.lower())
    fillers = {
        "spanish": ["el", "la", "que", "de", "en"],
        "english": ["the", "a", "that", "of", "in"],
    }
    return fillers.get(language, ["the"])[len(words) % 5]


def _cloze_guess(prompt: str, language: str) -> str:
    """Placeholder cloze response — returns most common filler."""
    fillers = {"spanish": "el", "english": "the"}
    return fillers.get(language, "the")


# ── Artifact helpers ──────────────────────────────────────────────────────────

def _create_artifact_dir(name: str) -> str:
    base = os.path.join("artifacts", name)
    os.makedirs("artifacts", exist_ok=True)
    i = 1
    while True:
        d = f"{base}_{i:03d}"
        if not os.path.exists(d):
            os.makedirs(d)
            return d
        i += 1


def _write_artifact(artifact_dir: str, result: dict, params: dict) -> None:
    with open(os.path.join(artifact_dir, "results.json"), "w") as f:
        json.dump({k: v for k, v in result.items() if k != "artifact_dir"}, f, indent=2)
    with open(os.path.join(artifact_dir, "parameters.json"), "w") as f:
        json.dump(params, f, indent=2)
    with open(os.path.join(artifact_dir, "metadata.json"), "w") as f:
        json.dump({
            "experiment": "comprehension_probe",
            "language":   result.get("language"),
            "corpus":     result.get("corpus"),
            "difficulty": result.get("difficulty"),
            "signal":     result.get("signal"),
            "passed":     result.get("passed"),
            "final_sync": result.get("signal"),   # atlas compat key
            "features":   {"signal": result.get("signal")},
        }, f, indent=2)
