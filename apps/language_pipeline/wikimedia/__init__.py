"""
Wikimedia language-domain ingestion and classification layer.
"""
from .client import WikimediaClient
from .normalizer import WikiProjectSource, PageEntityReference, EditEvent, normalize_contribution
from .classifier import classify_edit
from .corpus import EditClassification, build_corpus_artifacts

__all__ = [
    "WikimediaClient",
    "WikiProjectSource",
    "PageEntityReference",
    "EditEvent",
    "normalize_contribution",
    "classify_edit",
    "EditClassification",
    "build_corpus_artifacts",
]
