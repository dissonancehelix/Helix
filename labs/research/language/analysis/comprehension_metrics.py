"""
Comprehension Metrics
=====================
Evaluation metrics for language comprehension experiments.

Usage:
    from core.python_suite.language.comprehension_metrics import ComprehenMetrics
    score = ComprehenMetrics.recognition_accuracy(predictions, targets)
"""
from __future__ import annotations

import re
from typing import Sequence


class ComprehenMetrics:
    """
    Evaluation metrics for comprehension probes.

    Metrics:
        recognition_accuracy   — exact or normalized token match rate
        semantic_overlap       — Jaccard similarity of word sets
        prediction_accuracy    — next-token or next-word hit rate
        response_latency       — pass-through for timed experiments
        cloze_accuracy         — fill-in-the-blank accuracy
    """

    @staticmethod
    def recognition_accuracy(predictions: Sequence[str], targets: Sequence[str]) -> float:
        """
        Fraction of predictions that exactly match their target (normalized).
        Normalization: lowercase, strip punctuation.
        """
        if not targets:
            return 0.0
        correct = sum(
            ComprehenMetrics._normalize(p) == ComprehenMetrics._normalize(t)
            for p, t in zip(predictions, targets)
        )
        return round(correct / len(targets), 4)

    @staticmethod
    def semantic_overlap(text_a: str, text_b: str) -> float:
        """
        Jaccard similarity between word sets of two texts.
        Proxy for semantic similarity without embeddings.
        """
        tokens_a = set(ComprehenMetrics._tokenize(text_a))
        tokens_b = set(ComprehenMetrics._tokenize(text_b))
        if not tokens_a and not tokens_b:
            return 1.0
        if not tokens_a or not tokens_b:
            return 0.0
        return round(len(tokens_a & tokens_b) / len(tokens_a | tokens_b), 4)

    @staticmethod
    def batch_semantic_overlap(texts_a: Sequence[str], texts_b: Sequence[str]) -> float:
        """Mean semantic overlap across paired lists."""
        if not texts_a:
            return 0.0
        scores = [
            ComprehenMetrics.semantic_overlap(a, b)
            for a, b in zip(texts_a, texts_b)
        ]
        return round(sum(scores) / len(scores), 4)

    @staticmethod
    def prediction_accuracy(
        predictions: Sequence[str], targets: Sequence[str], partial: bool = False
    ) -> float:
        """
        Next-token prediction accuracy.
        If partial=True, accept prefix matches (first word of target).
        """
        if not targets:
            return 0.0
        hits = 0
        for pred, target in zip(predictions, targets):
            pred_norm   = ComprehenMetrics._normalize(pred)
            target_norm = ComprehenMetrics._normalize(target)
            if partial:
                first = target_norm.split()[0] if target_norm.split() else target_norm
                hits += int(pred_norm.startswith(first))
            else:
                hits += int(pred_norm == target_norm)
        return round(hits / len(targets), 4)

    @staticmethod
    def cloze_accuracy(
        responses: Sequence[str],
        correct_words: Sequence[str],
        distractors: Sequence[list[str]] | None = None,
    ) -> dict:
        """
        Cloze test accuracy — fill-in-the-blank.
        Returns accuracy, and if distractors provided, chance-corrected score.
        """
        if not correct_words:
            return {"accuracy": 0.0}
        correct = sum(
            ComprehenMetrics._normalize(r) == ComprehenMetrics._normalize(c)
            for r, c in zip(responses, correct_words)
        )
        accuracy = round(correct / len(correct_words), 4)
        result = {"accuracy": accuracy, "n": len(correct_words)}
        if distractors:
            avg_choices = sum(len(d) + 1 for d in distractors) / len(distractors)
            chance = 1.0 / avg_choices
            corrected = (accuracy - chance) / (1.0 - chance) if chance < 1 else 0.0
            result["chance_corrected"] = round(corrected, 4)
            result["chance_baseline"]  = round(chance, 4)
        return result

    @staticmethod
    def response_latency(latencies_ms: Sequence[float]) -> dict:
        """Summary statistics for response latency measurements (ms)."""
        if not latencies_ms:
            return {}
        n = len(latencies_ms)
        s = sorted(latencies_ms)
        return {
            "n":      n,
            "mean":   round(sum(s) / n, 2),
            "median": s[n // 2],
            "min":    s[0],
            "max":    s[-1],
            "p90":    s[int(n * 0.9)],
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^\w\s]", "", text.lower()).strip()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())
