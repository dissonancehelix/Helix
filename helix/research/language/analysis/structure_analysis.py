"""
Structure Analysis
==================
Extract structural patterns from text corpora.

Usage:
    from core.python_suite.language.structure_analysis import StructureAnalyzer
    analyzer = StructureAnalyzer()
    report = analyzer.analyze(texts)
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Sequence


class StructureAnalyzer:
    """
    Extracts surface structural patterns from a list of text samples.

    Patterns extracted:
        - word frequency distribution
        - phrase frequency (bigrams, trigrams)
        - word order patterns (sentence-initial tokens)
        - verb morphology distribution (suffix-based heuristic)
        - sentence length distribution
        - type-token ratio (lexical diversity)
    """

    def __init__(self, language: str = "unknown"):
        self.language = language

    def analyze(self, texts: Sequence[str]) -> dict:
        """Run all analyses. Returns a flat result dict."""
        tokens_per_sent = [self._tokenize(t) for t in texts]
        all_tokens = [tok for sent in tokens_per_sent for tok in sent]

        return {
            "language":            self.language,
            "sample_count":        len(texts),
            "word_frequency":      self.word_frequency(all_tokens),
            "bigram_frequency":    self.ngram_frequency(tokens_per_sent, n=2),
            "trigram_frequency":   self.ngram_frequency(tokens_per_sent, n=3),
            "word_order":          self.word_order_patterns(tokens_per_sent),
            "verb_morphology":     self.verb_morphology(all_tokens, self.language),
            "sentence_lengths":    self.sentence_length_stats(tokens_per_sent),
            "type_token_ratio":    self.type_token_ratio(all_tokens),
        }

    # ── Pattern extractors ────────────────────────────────────────────────────

    @staticmethod
    def word_frequency(tokens: list[str], top_n: int = 50) -> list[tuple[str, int]]:
        return Counter(tokens).most_common(top_n)

    @staticmethod
    def ngram_frequency(
        tokenized_sents: list[list[str]], n: int = 2, top_n: int = 30
    ) -> list[tuple[str, int]]:
        ngrams: list[str] = []
        for sent in tokenized_sents:
            for i in range(len(sent) - n + 1):
                ngrams.append(" ".join(sent[i : i + n]))
        return Counter(ngrams).most_common(top_n)

    @staticmethod
    def word_order_patterns(
        tokenized_sents: list[list[str]], top_n: int = 20
    ) -> dict:
        """Collect sentence-initial and final bigrams as word order proxies."""
        initial = Counter()
        final   = Counter()
        for sent in tokenized_sents:
            if len(sent) >= 2:
                initial[" ".join(sent[:2])] += 1
                final[" ".join(sent[-2:])] += 1
        return {
            "initial_bigrams": initial.most_common(top_n),
            "final_bigrams":   final.most_common(top_n),
        }

    @staticmethod
    def verb_morphology(tokens: list[str], language: str = "unknown") -> dict:
        """
        Heuristic verb morphology distribution based on common suffixes.
        For Spanish: -ar/-er/-ir infinitives; -ó/-é/-ió past; -ndo gerund.
        For English: -ing/-ed/-s present/past.
        """
        suffixes: dict[str, list[str]] = {
            "spanish": {
                "infinitive_ar":  [r"ar$"],
                "infinitive_er":  [r"er$"],
                "infinitive_ir":  [r"ir$"],
                "past":           [r"ó$", r"é$", r"ió$", r"aron$", r"ieron$"],
                "gerund":         [r"ndo$"],
                "subjunctive":    [r"e$", r"en$", r"es$"],
            },
            "english": {
                "gerund":    [r"ing$"],
                "past":      [r"ed$"],
                "3rd_sg":    [r"(?<![aeiou])s$"],
            },
        }
        lang_key = language.lower()
        patterns = suffixes.get(lang_key, {})
        counts: dict[str, int] = {k: 0 for k in patterns}
        for tok in tokens:
            for label, regexes in patterns.items():
                if any(re.search(rx, tok.lower()) for rx in regexes):
                    counts[label] += 1
        total = sum(counts.values()) or 1
        return {k: {"count": v, "ratio": round(v / total, 4)} for k, v in counts.items()}

    @staticmethod
    def sentence_length_stats(tokenized_sents: list[list[str]]) -> dict:
        lengths = [len(s) for s in tokenized_sents if s]
        if not lengths:
            return {}
        return {
            "min":    min(lengths),
            "max":    max(lengths),
            "mean":   round(sum(lengths) / len(lengths), 2),
            "median": sorted(lengths)[len(lengths) // 2],
        }

    @staticmethod
    def type_token_ratio(tokens: list[str]) -> float:
        if not tokens:
            return 0.0
        return round(len(set(tokens)) / len(tokens), 4)

    # ── Tokenizer ─────────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())
