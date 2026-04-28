"""
Corpus aggregation logic for building Language-domain artifacts.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .normalizer import EditEvent

@dataclass
class EditClassification:
    event: EditEvent
    category: str


def build_corpus_artifacts(classified_edits: list[EditClassification]) -> dict[str, Any]:
    """
    Computes summary metrics to generate operator-facing artifacts.
    """
    artifacts = {}

    # 1. Project Summary
    project_totals = Counter(ce.event.project for ce in classified_edits)
    artifacts["wikimedia_project_summary"] = {
        "total_edits": len(classified_edits),
        "by_project": dict(project_totals),
    }

    # 2. Edit Classification Dist
    classes = Counter(ce.category for ce in classified_edits)
    artifacts["wikimedia_edit_classification"] = {
        "total_classified": len(classified_edits),
        "distribution": dict(sorted(classes.items(), key=lambda x: -x[1])),
    }

    # 3. Namespace Distribution 
    ns_dist = Counter(ce.event.page.namespace_id for ce in classified_edits)
    artifacts["wikimedia_namespace_distribution"] = {
        "by_namespace_id": dict(sorted(ns_dist.items(), key=lambda x: -x[1])),
    }

    # 4. Yearly Activity
    years = Counter(ce.event.timestamp[:4] for ce in classified_edits if ce.event.timestamp)
    artifacts["wikimedia_yearly_activity"] = {
        "by_year": dict(sorted(years.items())),
    }

    # 5. Page Focus Report
    pages = Counter(ce.event.page.title for ce in classified_edits if ce.event.page.namespace_id == 0)
    most_edited = [{"title": title, "edits": count} for title, count in pages.most_common(50)]
    artifacts["wikimedia_page_focus_report"] = {
        "total_unique_main_pages": len(pages),
        "most_edited_pages": most_edited,
    }

    # 6. Normalized Traces (just the raw sequence for raw JSON output)
    normalized_json = [ce.event.to_dict() | {"classification": ce.category} for ce in classified_edits]
    artifacts["wikimedia_normalized_edits"] = normalized_json

    return artifacts
