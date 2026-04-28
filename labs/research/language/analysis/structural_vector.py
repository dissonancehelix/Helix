"""
Spanish-first structural vector extraction for the Helix language substrate.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Sequence

from model.domains.language.pattern_detection.grammar_patterns import GrammarPatterns
from model.domains.language.structural_analysis.structure_analysis import StructureAnalyzer


AXES: tuple[str, ...] = (
    "inflectional_load",
    "subject_explicitness",
    "clause_subordination",
    "function_word_scaffolding",
    "tense_aspect_marking",
    "mood_polarity",
    "frame_stability",
    "lexical_variation",
)


def vector_distance(a: dict[str, float], b: dict[str, float]) -> float:
    keys = [axis for axis in AXES if axis in a and axis in b]
    if not keys:
        return 0.0
    total = sum((float(a[key]) - float(b[key])) ** 2 for key in keys)
    return math.sqrt(total / len(keys))


def mean_vector(vectors: Sequence[dict[str, float]]) -> dict[str, float]:
    if not vectors:
        return {axis: 0.0 for axis in AXES}
    return {
        axis: round(sum(float(vector.get(axis, 0.0)) for vector in vectors) / len(vectors), 4)
        for axis in AXES
    }


class StructuralVectorExtractor:
    """
    Extract a compact construction-space vector from raw text.

    This is intentionally heuristic and language-local. It marks where
    Spanish structure is concentrated instead of pretending to be a full parser.
    """

    def __init__(self, language: str = "spanish") -> None:
        self.language = language.lower()
        self.structure = StructureAnalyzer(language=self.language)
        self.grammar = GrammarPatterns(language=self.language)

    def summarize(self, records: Sequence[dict[str, Any]]) -> dict[str, Any]:
        if not records:
            return {
                "language": self.language,
                "axes": list(AXES),
                "count": 0,
                "vectors": [],
                "centroid": {axis: 0.0 for axis in AXES},
                "dispersion": 0.0,
                "frame_concentration": {},
            }

        vectors = [self.vectorize_record(record) for record in records]
        frame_counts = Counter(vector["frame_anchor"] for vector in vectors if vector["frame_anchor"])
        total = len(vectors) or 1

        for vector in vectors:
            frame_anchor = vector["frame_anchor"]
            frame_stability = frame_counts[frame_anchor] / total if frame_anchor else 0.0
            vector["axis_values"]["frame_stability"] = round(frame_stability, 4)

        axis_vectors = [vector["axis_values"] for vector in vectors]
        centroid = mean_vector(axis_vectors)
        dispersion = round(
            sum(vector_distance(vector, centroid) for vector in axis_vectors) / len(axis_vectors),
            4,
        )

        return {
            "language": self.language,
            "axes": list(AXES),
            "count": len(vectors),
            "vectors": vectors,
            "centroid": centroid,
            "dispersion": dispersion,
            "frame_concentration": {
                frame: round(count / total, 4)
                for frame, count in frame_counts.most_common(12)
            },
        }

    def vectorize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        text = str(record.get("text", "")).strip()
        tokens = self.structure._tokenize(text)  # noqa: SLF001 - shared tokenizer
        token_count = max(len(tokens), 1)

        morph = self.structure.verb_morphology(tokens, self.language)
        grammar = self.grammar.extract([text])
        function_word_dist = grammar.get("function_word_dist", {})
        clause_types = grammar.get("clause_types", {})
        sentence_types = grammar.get("sentence_types", {})
        pro_drop = grammar.get("pro_drop_evidence", {})

        morph_counts = {
            key: int(value.get("count", 0))
            for key, value in morph.items()
            if isinstance(value, dict)
        }
        total_morph = sum(morph_counts.values()) or 1

        function_word_scaffolding = sum(
            float(function_word_dist.get(label, {}).get("rate", 0.0))
            for label in ("articles", "prepositions", "coordinators", "subordinators")
        )
        mood_signal = (
            float(sentence_types.get("interrogative", {}).get("ratio", 0.0))
            + float(sentence_types.get("exclamatory", {}).get("ratio", 0.0))
            + float(grammar.get("negation_rate", 0.0))
        ) / 3.0

        frame_anchor = " ".join(tokens[:3]) if len(tokens) >= 3 else " ".join(tokens)
        axis_values = {
            "inflectional_load": round(sum(morph_counts.values()) / token_count, 4),
            "subject_explicitness": round(float(pro_drop.get("pronoun_sentence_rate", 0.0)), 4),
            "clause_subordination": round(
                float(clause_types.get("subordinate", {}).get("ratio", 0.0)),
                4,
            ),
            "function_word_scaffolding": round(min(function_word_scaffolding, 1.0), 4),
            "tense_aspect_marking": round(
                (
                    morph_counts.get("past", 0)
                    + morph_counts.get("gerund", 0)
                    + morph_counts.get("subjunctive", 0)
                ) / total_morph,
                4,
            ),
            "mood_polarity": round(mood_signal, 4),
            "frame_stability": 0.0,
            "lexical_variation": round(self.structure.type_token_ratio(tokens), 4),
        }

        return {
            "id": record.get("id"),
            "language": record.get("language", self.language),
            "family": record.get("family"),
            "label": record.get("label"),
            "transform": record.get("transform"),
            "text": text,
            "token_count": token_count,
            "frame_anchor": frame_anchor,
            "axis_values": axis_values,
        }


def project_helix_embedding(
    centroid: dict[str, float],
    null_signal: dict[str, Any] | None = None,
    domain: str = "language",
) -> dict[str, Any]:
    """
    Project the language-local vector into the shared Helix embedding axes.
    """
    confidence = 0.35
    if null_signal:
        confidence = max(confidence, float(null_signal.get("confidence", confidence)))

    structure = (
        float(centroid.get("frame_stability", 0.0))
        + float(centroid.get("function_word_scaffolding", 0.0))
    ) / 2.0
    complexity = (
        float(centroid.get("inflectional_load", 0.0))
        + float(centroid.get("clause_subordination", 0.0))
    ) / 2.0
    repetition = float(centroid.get("frame_stability", 0.0))
    density = (
        float(centroid.get("function_word_scaffolding", 0.0))
        + float(centroid.get("tense_aspect_marking", 0.0))
    ) / 2.0
    expression = 1.0 - float(centroid.get("subject_explicitness", 0.0))
    variation = float(centroid.get("lexical_variation", 0.0))

    return {
        "complexity": round(min(max(complexity, 0.0), 1.0), 4),
        "structure": round(min(max(structure, 0.0), 1.0), 4),
        "repetition": round(min(max(repetition, 0.0), 1.0), 4),
        "density": round(min(max(density, 0.0), 1.0), 4),
        "expression": round(min(max(expression, 0.0), 1.0), 4),
        "variation": round(min(max(variation, 0.0), 1.0), 4),
        "confidence": round(min(max(confidence, 0.0), 1.0), 4),
        "domain": domain,
        "source_vector": "language_structural_vector",
        "projection_schema": "language_v1",
    }

