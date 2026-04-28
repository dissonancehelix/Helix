"""
Stimulus Generator
==================
Generates language training exercises from corpus data.

Exercise types:
    phrase_chunk_drill     — identify/repeat common phrase chunks
    sentence_prediction    — predict missing words or continuations
    continuation_exercise  — complete an incomplete sentence

Usage:
    from labs.cognition.language.training.stimulus_generator import StimulusGenerator
    gen = StimulusGenerator(language="spanish")
    exercises = gen.generate(texts, exercise_type="phrase_chunk_drill", n=20)
"""
from __future__ import annotations

import random
import re
from typing import Literal

ExerciseType = Literal["phrase_chunk_drill", "sentence_prediction", "continuation_exercise"]


class StimulusGenerator:
    """
    Generates structured language training exercises from raw text samples.

    All methods return lists of exercise dicts with consistent keys:
        type        — exercise type string
        prompt      — what the learner sees
        target      — correct answer / expected response
        distractors — wrong options (for multiple-choice variants)
        context     — source sentence (for review)
        difficulty  — estimated CEFR level (A1–C2) based on word length heuristic
    """

    _CEFR_THRESHOLDS = {
        "A1": (0, 4),
        "A2": (4, 6),
        "B1": (6, 8),
        "B2": (8, 11),
        "C1": (11, 14),
        "C2": (14, 999),
    }

    def __init__(self, language: str = "unknown", seed: int = 42):
        self.language = language.lower()
        random.seed(seed)

    def generate(
        self,
        texts: list[str],
        exercise_type: ExerciseType = "sentence_prediction",
        n: int = 20,
        difficulty: str | None = None,
    ) -> list[dict]:
        """Generate n exercises of the given type from the provided texts."""
        if exercise_type == "phrase_chunk_drill":
            exercises = self._phrase_chunk_drills(texts)
        elif exercise_type == "sentence_prediction":
            exercises = self._sentence_predictions(texts)
        elif exercise_type == "continuation_exercise":
            exercises = self._continuation_exercises(texts)
        else:
            raise ValueError(f"Unknown exercise type: {exercise_type!r}")

        if difficulty:
            exercises = [e for e in exercises if e.get("difficulty") == difficulty.upper()]

        random.shuffle(exercises)
        return exercises[:n]

    def generate_all(self, texts: list[str], n_each: int = 10) -> dict[str, list[dict]]:
        """Generate all three exercise types."""
        return {
            "phrase_chunk_drill":    self.generate(texts, "phrase_chunk_drill",    n_each),
            "sentence_prediction":   self.generate(texts, "sentence_prediction",   n_each),
            "continuation_exercise": self.generate(texts, "continuation_exercise", n_each),
        }

    # ── Exercise builders ─────────────────────────────────────────────────────

    def _phrase_chunk_drills(self, texts: list[str]) -> list[dict]:
        """
        Extract common 2–4 word phrase chunks.
        Exercise: show chunk with one word blanked; learner fills it in.
        """
        from collections import Counter
        tokenized = [self._tokenize(t) for t in texts]
        bigrams: Counter = Counter()
        for sent in tokenized:
            for i in range(len(sent) - 1):
                bigrams[tuple(sent[i : i + 2])] += 1

        exercises = []
        for (w1, w2), count in bigrams.most_common(200):
            if count < 2:
                break
            # Blank either word
            for blank_pos, target in [(0, w1), (1, w2)]:
                chunk = [w1, w2]
                prompt_words = chunk.copy()
                prompt_words[blank_pos] = "___"
                exercises.append({
                    "type":        "phrase_chunk_drill",
                    "prompt":      " ".join(prompt_words),
                    "target":      target,
                    "distractors": self._distractors(target, tokenized),
                    "context":     f"{w1} {w2}",
                    "difficulty":  self._estimate_difficulty([w1, w2]),
                    "frequency":   count,
                })
        return exercises

    def _sentence_predictions(self, texts: list[str]) -> list[dict]:
        """
        Exercise: given first N-1 words, predict the last word.
        """
        exercises = []
        for text in texts:
            words = text.split()
            if len(words) < 4:
                continue
            target = re.sub(r"[^\w]", "", words[-1]).lower()
            if len(target) < 2:
                continue
            prompt = " ".join(words[:-1]) + " ___"
            all_tokens = [self._tokenize(t) for t in texts]
            exercises.append({
                "type":        "sentence_prediction",
                "prompt":      prompt,
                "target":      target,
                "distractors": self._distractors(target, all_tokens),
                "context":     text,
                "difficulty":  self._estimate_difficulty(words),
            })
        return exercises

    def _continuation_exercises(self, texts: list[str]) -> list[dict]:
        """
        Exercise: given first half of sentence, produce the second half.
        """
        exercises = []
        for text in texts:
            words = text.split()
            if len(words) < 6:
                continue
            mid = len(words) // 2
            prompt = " ".join(words[:mid]) + " ..."
            target = " ".join(words[mid:])
            exercises.append({
                "type":       "continuation_exercise",
                "prompt":     prompt,
                "target":     target,
                "distractors": [],  # open-ended, no MC options
                "context":    text,
                "difficulty": self._estimate_difficulty(words),
            })
        return exercises

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _distractors(
        self, target: str, tokenized: list[list[str]], n: int = 3
    ) -> list[str]:
        """Pick n plausible distractors that are not the target."""
        from collections import Counter
        all_words = [t for sent in tokenized for t in sent]
        freq = Counter(all_words)
        candidates = [
            w for w, _ in freq.most_common(300)
            if w != target and len(w) >= 2
        ]
        random.shuffle(candidates)
        return candidates[:n]

    def _estimate_difficulty(self, words: list[str]) -> str:
        """Heuristic CEFR difficulty based on average word length."""
        if not words:
            return "A2"
        avg_len = sum(len(w) for w in words) / len(words)
        for level, (lo, hi) in self._CEFR_THRESHOLDS.items():
            if lo <= avg_len < hi:
                return level
        return "C2"

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())
