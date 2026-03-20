"""
Grammar Patterns
================
Identify grammar structures and dependency patterns in text corpora.

Usage:
    from core.python_suite.language.grammar_patterns import GrammarPatterns
    patterns = GrammarPatterns(language="spanish")
    report = patterns.extract(texts)
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Sequence


class GrammarPatterns:
    """
    Identifies grammar structures from surface features of text.

    Does not require a dependency parser — uses rule-based heuristics
    that work on raw tokenized text. Suitable for corpus statistics
    before introducing heavier NLP tools.

    Patterns extracted:
        - clause boundaries (subordinators, coordinators)
        - question patterns
        - negation patterns
        - determiner + noun phrases
        - common grammatical function word distributions
    """

    # Language-specific function word lists
    _FUNCTION_WORDS: dict[str, dict[str, list[str]]] = {
        "spanish": {
            "articles":       ["el", "la", "los", "las", "un", "una", "unos", "unas"],
            "prepositions":   ["de", "en", "a", "por", "para", "con", "sin", "sobre",
                               "entre", "hasta", "desde", "hacia", "según"],
            "coordinators":   ["y", "o", "pero", "sino", "ni", "aunque", "porque"],
            "subordinators":  ["que", "cuando", "como", "donde", "si", "aunque",
                               "mientras", "porque", "para que", "después"],
            "negations":      ["no", "nunca", "jamás", "nada", "nadie", "tampoco"],
            "question_words": ["qué", "cómo", "dónde", "cuándo", "quién", "cuál",
                               "cuánto", "por qué"],
            "subject_pronouns": ["yo", "tú", "él", "ella", "nosotros", "vosotros",
                                  "ellos", "ellas", "usted", "ustedes"],
        },
        "english": {
            "articles":         ["the", "a", "an"],
            "prepositions":     ["in", "on", "at", "of", "to", "for", "with",
                                 "by", "from", "about", "as", "into"],
            "coordinators":     ["and", "or", "but", "nor", "so", "yet", "for"],
            "subordinators":    ["that", "when", "because", "if", "although",
                                 "while", "after", "before", "since", "unless"],
            "negations":        ["not", "never", "no", "nothing", "nobody", "neither"],
            "question_words":   ["what", "how", "where", "when", "who", "which",
                                 "why", "whose"],
            "subject_pronouns": ["i", "you", "he", "she", "we", "they", "it"],
        },
    }

    def __init__(self, language: str = "unknown"):
        self.language = language.lower()
        self._fw = self._FUNCTION_WORDS.get(self.language, {})

    def extract(self, texts: Sequence[str]) -> dict:
        """Run all grammar pattern extractors on a text corpus."""
        tokenized = [self._tokenize(t) for t in texts]
        return {
            "language":             self.language,
            "sample_count":         len(texts),
            "function_word_dist":   self.function_word_distribution(tokenized),
            "clause_types":         self.clause_type_distribution(tokenized),
            "sentence_types":       self.sentence_type_distribution(texts),
            "negation_rate":        self.negation_rate(tokenized),
            "pro_drop_evidence":    self.pro_drop_evidence(tokenized),
            "top_frames":           self.top_sentence_frames(tokenized),
        }

    # ── Extractors ────────────────────────────────────────────────────────────

    def function_word_distribution(self, tokenized: list[list[str]]) -> dict:
        """Count occurrences of each grammatical category's function words."""
        all_tokens = [t for sent in tokenized for t in sent]
        total = len(all_tokens) or 1
        result = {}
        for category, words in self._fw.items():
            count = sum(all_tokens.count(w) for w in words)
            result[category] = {
                "count": count,
                "rate":  round(count / total, 4),
            }
        return result

    def clause_type_distribution(self, tokenized: list[list[str]]) -> dict:
        """Count subordinate vs coordinate clause markers."""
        subs = self._fw.get("subordinators", [])
        coords = self._fw.get("coordinators", [])
        sub_count = coord_count = 0
        for sent in tokenized:
            sub_count   += sum(1 for t in sent if t in subs)
            coord_count += sum(1 for t in sent if t in coords)
        total = sub_count + coord_count or 1
        return {
            "subordinate":  {"count": sub_count,   "ratio": round(sub_count / total, 4)},
            "coordinate":   {"count": coord_count, "ratio": round(coord_count / total, 4)},
            "sub_to_coord": round(sub_count / (coord_count or 1), 4),
        }

    def sentence_type_distribution(self, texts: Sequence[str]) -> dict:
        """Classify sentences as declarative, interrogative, or exclamatory."""
        counts = Counter()
        for text in texts:
            stripped = text.strip()
            if stripped.endswith("?") or stripped.startswith("¿"):
                counts["interrogative"] += 1
            elif stripped.endswith("!") or stripped.startswith("¡"):
                counts["exclamatory"] += 1
            else:
                counts["declarative"] += 1
        total = len(texts) or 1
        return {k: {"count": v, "ratio": round(v / total, 4)} for k, v in counts.items()}

    def negation_rate(self, tokenized: list[list[str]]) -> float:
        """Fraction of sentences containing at least one negation marker."""
        neg_words = self._fw.get("negations", [])
        if not neg_words or not tokenized:
            return 0.0
        neg_sents = sum(1 for sent in tokenized if any(t in neg_words for t in sent))
        return round(neg_sents / len(tokenized), 4)

    def pro_drop_evidence(self, tokenized: list[list[str]]) -> dict:
        """
        Evidence for pro-drop: compare explicit subject pronoun rate.
        High rate → subject pronouns usually explicit (English-like).
        Low rate  → pro-drop likely (Spanish-like for many contexts).
        """
        pronouns = self._fw.get("subject_pronouns", [])
        if not pronouns or not tokenized:
            return {}
        pronoun_sents = sum(
            1 for sent in tokenized if any(t in pronouns for t in sent)
        )
        rate = round(pronoun_sents / len(tokenized), 4)
        return {
            "pronoun_sentence_rate": rate,
            "pro_drop_likely": rate < 0.5,
        }

    @staticmethod
    def top_sentence_frames(
        tokenized: list[list[str]], top_n: int = 20
    ) -> list[tuple[str, int]]:
        """
        Extract the most common 3-token sentence frames (first 3 tokens).
        Reveals dominant syntactic construction patterns.
        """
        frames: Counter = Counter()
        for sent in tokenized:
            if len(sent) >= 3:
                frames[" ".join(sent[:3])] += 1
        return frames.most_common(top_n)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())
