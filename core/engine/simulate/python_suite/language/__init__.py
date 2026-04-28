"""Compatibility exports for legacy language helper imports."""

from domains.language.feature_extraction.comprehension_metrics import ComprehenMetrics
from domains.language.ingestion.corpus_loader import CorpusLoader
from domains.language.pattern_detection.grammar_patterns import GrammarPatterns
from domains.language.structural_analysis.structure_analysis import StructureAnalyzer

__all__ = [
    "ComprehenMetrics",
    "CorpusLoader",
    "GrammarPatterns",
    "StructureAnalyzer",
]
