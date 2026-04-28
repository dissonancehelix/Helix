"""Compatibility exports for legacy language helper imports."""

from model.domains.language.feature_extraction.comprehension_metrics import ComprehenMetrics
from model.domains.language.ingestion.corpus_loader import CorpusLoader
from model.domains.language.pattern_detection.grammar_patterns import GrammarPatterns
from model.domains.language.structural_analysis.structure_analysis import StructureAnalyzer

__all__ = [
    "ComprehenMetrics",
    "CorpusLoader",
    "GrammarPatterns",
    "StructureAnalyzer",
]

