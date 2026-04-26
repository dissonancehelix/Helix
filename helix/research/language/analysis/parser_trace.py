"""
Sentence-level parser traces for the Helix language runtime.

These traces are intentionally honest: they are surface-parser projections,
not full dependency parses. The schema is explicit so deeper adapters can slot
in later without changing the pipeline contract.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

from domains.language.feature_extraction.structural_vector import StructuralVectorExtractor
from domains.language.pattern_detection.grammar_patterns import GrammarPatterns
from domains.language.structural_analysis.structure_analysis import StructureAnalyzer

TRACE_SCHEMA_VERSION = "language_parser_trace_v1"
TRACE_BACKEND = "heuristic_surface_parser"

_ENGLISH_AUX = {
    "do", "does", "did", "is", "are", "was", "were", "will",
    "would", "can", "could", "should", "have", "has", "had",
}


def build_parser_traces(
    *,
    language: str,
    records: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    extractor = StructuralVectorExtractor(language=language)
    grammar = GrammarPatterns(language=language)
    structure = StructureAnalyzer(language=language)

    traces = [
        build_parser_trace(
            language=language,
            record=record,
            extractor=extractor,
            grammar=grammar,
            structure=structure,
        )
        for record in records
    ]

    return {
        "block": "parser_traces",
        "schema_version": TRACE_SCHEMA_VERSION,
        "backend": TRACE_BACKEND,
        "language": language,
        "trace_count": len(traces),
        "summary": _summarize_traces(traces),
        "traces": traces,
    }


def build_parser_trace(
    *,
    language: str,
    record: dict[str, Any],
    extractor: StructuralVectorExtractor,
    grammar: GrammarPatterns,
    structure: StructureAnalyzer,
) -> dict[str, Any]:
    text = str(record.get("text", "")).strip()
    tokens = structure._tokenize(text)  # noqa: SLF001 - canonical shared tokenizer
    grammar_report = grammar.extract([text])
    vector = extractor.vectorize_record(record)
    subject_span = _subject_span(
        tokens=tokens,
        text=text,
        language=language,
        grammar_report=grammar_report,
        record=record,
    )
    root_index = _root_index(tokens=tokens, subject_span=subject_span, language=language)
    subject_tokens = [tokens[index] for index in subject_span if 0 <= index < len(tokens)]
    complementizers = _complementizers(tokens=tokens, grammar_report=grammar_report)

    return {
        "record_id": str(record.get("id", "")),
        "language": language,
        "backend": TRACE_BACKEND,
        "schema_version": TRACE_SCHEMA_VERSION,
        "family": record.get("family"),
        "label": record.get("label"),
        "transform": record.get("transform"),
        "edge_from": record.get("edge_from"),
        "construction_role": "variant" if record.get("transform") else "base",
        "text": text,
        "tokens": tokens,
        "token_count": len(tokens),
        "sentence_type": _dominant_label(grammar_report.get("sentence_types", {}), default="declarative"),
        "negation_present": bool(grammar_report.get("negation_rate", 0.0)),
        "pro_drop_likely": bool(grammar_report.get("pro_drop_evidence", {}).get("pro_drop_likely")),
        "frame_anchor": vector.get("frame_anchor"),
        "axis_values": vector.get("axis_values", {}),
        "function_word_dist": grammar_report.get("function_word_dist", {}),
        "clause_profile": grammar_report.get("clause_types", {}),
        "dependency_proxy": {
            "root_index": root_index,
            "root_token": tokens[root_index] if tokens and 0 <= root_index < len(tokens) else None,
            "subject_span": subject_span,
            "subject_tokens": subject_tokens,
            "complementizer_tokens": complementizers,
            "pre_root_tokens": tokens[:root_index],
            "post_root_tokens": tokens[root_index + 1:] if tokens and 0 <= root_index < len(tokens) else [],
        },
        "confidence": _trace_confidence(tokens=tokens, grammar_report=grammar_report),
        "notes": (
            "Surface-parser trace derived from token order, function-word distribution, "
            "and record-local structural vector."
        ),
    }


def _subject_span(
    *,
    tokens: list[str],
    text: str,
    language: str,
    grammar_report: dict[str, Any],
    record: dict[str, Any] | None = None,
) -> list[int]:
    if not tokens:
        return []

    record = record or {}
    if str(record.get("transform", "")).lower() == "drop_subject":
        return []

    function_words = grammar_report.get("function_word_dist", {})
    pronoun_tokens = set(
        GrammarPatterns._FUNCTION_WORDS.get(language, {}).get("subject_pronouns", [])  # noqa: SLF001
    )
    article_tokens = set(
        GrammarPatterns._FUNCTION_WORDS.get(language, {}).get("articles", [])  # noqa: SLF001
    )

    if language == "english" and tokens[0] in _ENGLISH_AUX:
        if len(tokens) > 1 and tokens[1] in pronoun_tokens:
            return [1]
        if len(tokens) > 2 and tokens[1] in article_tokens:
            return [1, 2]

    if tokens[0] in pronoun_tokens:
        return [0]
    if tokens[0] in article_tokens and len(tokens) > 1:
        return [0, 1]

    if language == "spanish" and text.startswith("¿"):
        return []

    if function_words.get("subject_pronouns", {}).get("count", 0) == 0 and language == "spanish":
        return []

    return [0]


def _root_index(*, tokens: list[str], subject_span: list[int], language: str) -> int:
    if not tokens:
        return 0

    if language == "english" and tokens[0] in _ENGLISH_AUX and len(tokens) > 2:
        return 2

    if subject_span:
        return min(max(subject_span[-1] + 1, 0), len(tokens) - 1)

    return 0


def _complementizers(*, tokens: list[str], grammar_report: dict[str, Any]) -> list[str]:
    subordinator_count = grammar_report.get("function_word_dist", {}).get("subordinators", {}).get("count", 0)
    if not subordinator_count:
        return []

    known = {
        "that", "if", "when", "because", "although", "while", "after", "before", "since", "unless",
        "que", "cuando", "como", "donde", "si", "aunque", "mientras", "porque", "para",
    }
    return [token for token in tokens if token in known]


def _dominant_label(counter_map: dict[str, Any], default: str) -> str:
    best_label = default
    best_score = -1.0
    for label, payload in counter_map.items():
        score = float(payload.get("ratio", 0.0))
        if score > best_score:
            best_label = label
            best_score = score
    return best_label


def _trace_confidence(*, tokens: list[str], grammar_report: dict[str, Any]) -> float:
    token_signal = min(len(tokens) / 8.0, 1.0)
    clause_signal = min(
        float(grammar_report.get("clause_types", {}).get("subordinate", {}).get("ratio", 0.0))
        + float(grammar_report.get("clause_types", {}).get("coordinate", {}).get("ratio", 0.0)),
        1.0,
    )
    polarity_signal = min(
        float(grammar_report.get("negation_rate", 0.0))
        + float(grammar_report.get("sentence_types", {}).get("interrogative", {}).get("ratio", 0.0)),
        1.0,
    )
    return round((0.45 * token_signal) + (0.35 * clause_signal) + (0.20 * polarity_signal), 4)


def _summarize_traces(traces: Sequence[dict[str, Any]]) -> dict[str, Any]:
    family_counter = Counter(str(trace.get("family", "ungrouped")) for trace in traces)
    sentence_counter = Counter(str(trace.get("sentence_type", "unknown")) for trace in traces)
    mean_token_count = 0.0
    if traces:
        mean_token_count = round(
            sum(int(trace.get("token_count", 0)) for trace in traces) / len(traces),
            2,
        )

    return {
        "family_distribution": dict(family_counter),
        "sentence_type_distribution": dict(sentence_counter),
        "mean_token_count": mean_token_count,
    }
