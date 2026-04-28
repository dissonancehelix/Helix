"""
Account ingest layer for the Wikipedia operator subsystem.

Wraps the existing model/domains/language/ingestion/wikimedia/ pipeline and adds
template-focused pattern extraction on top. The underlying API client,
normalizer, and classifier are not duplicated — this module orchestrates them
and produces operator-useful artifacts.

No live edits. Read-only API access.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Re-use the existing ingest layer
from system.tools.language_pipeline.wikimedia.client import WikimediaClient
from system.tools.language_pipeline.wikimedia.normalizer import (
    WikiProjectSource, normalize_contribution, EditEvent,
)
from system.tools.language_pipeline.wikimedia.classifier import (
    classify_edit,
    CLS_TEMPLATE_WORK, CLS_INFOBOX_UPDATE,
)
from system.tools.language_pipeline.wikimedia.corpus import (
    EditClassification, build_corpus_artifacts,
)
from system.tools.language_pipeline import OPERATOR_USERNAME, ENWIKI_API

_ARTIFACTS_ROOT = Path(__file__).resolve().parents[3] / "data" / "raw" / "wikipedia"

# Known artifact from the 2026-04-11 run
_LATEST_ARTIFACT = _ARTIFACTS_ROOT / "wiki_20260411_150435"

PROJECTS = {
    "enwiki": WikiProjectSource("en.wikipedia.org", "enwiki", ENWIKI_API),
    "wikidata": WikiProjectSource("www.wikidata.org", "wikidata", "https://www.wikidata.org/w/api.php"),
    "commons": WikiProjectSource("commons.wikimedia.org", "commons", "https://commons.wikimedia.org/w/api.php"),
}


@dataclass
class TemplateEditSummary:
    """Summary of template-namespace and infobox-related edit activity."""
    total_template_ns_edits: int
    total_infobox_edits: int
    top_templates_edited: list[dict]       # [{title, edits}]
    infobox_comment_samples: list[str]     # edit comments mentioning infobox
    template_comment_samples: list[str]    # edit comments for template-ns edits
    common_template_names: list[str]       # template titles touched most often
    yearly_template_velocity: dict[str, int]


@dataclass
class AccountIngestResult:
    username: str
    total_edits: int
    by_project: dict[str, int]
    classification_distribution: dict[str, int]
    template_summary: TemplateEditSummary
    page_focus: list[dict]                 # top 50 main-ns pages
    artifacts_path: str | None = None


class AccountIngest:
    """
    Operator account ingest — reads from existing artifact cache or re-fetches.

    Usage:
        ingest = AccountIngest()
        result = ingest.from_artifact()   # fast: loads from 2026-03-29 run
        result = ingest.from_api(limit=10000)  # slow: hits live API
    """

    def __init__(self, username: str = OPERATOR_USERNAME):
        self.username = username

    # ------------------------------------------------------------------
    # Load from existing artifact cache (preferred — avoids API hammering)
    # ------------------------------------------------------------------

    def from_artifact(self, artifact_dir: Path | None = None) -> AccountIngestResult:
        """Load from the most recent artifact run."""
        dir_ = artifact_dir or _LATEST_ARTIFACT
        if not dir_.exists():
            raise FileNotFoundError(
                f"No artifact found at {dir_}. Run from_api() first or "
                f"point artifact_dir at an existing wikimedia artifact directory."
            )
        return self._parse_artifact_dir(dir_)

    def _parse_artifact_dir(self, dir_: Path) -> AccountIngestResult:
        def _load(name: str) -> Any:
            p = dir_ / name
            if not p.exists():
                return {}
            with open(p, encoding="utf-8") as f:
                return json.load(f)

        project_summary = _load("wikimedia_project_summary.json")
        cls_data        = _load("wikimedia_edit_classification.json")
        page_focus      = _load("wikimedia_page_focus_report.json")

        # Template-focused extraction from normalized JSONL
        template_summary = self._extract_template_summary(dir_)

        return AccountIngestResult(
            username=self.username,
            total_edits=project_summary.get("total_edits", 0),
            by_project=project_summary.get("by_project", {}),
            classification_distribution=cls_data.get("distribution", {}),
            template_summary=template_summary,
            page_focus=page_focus.get("most_edited_pages", []),
            artifacts_path=str(dir_),
        )

    def _extract_template_summary(self, dir_: Path) -> TemplateEditSummary:
        """
        Walk the normalized JSONL and pull template-focused signals.
        Targets:
          - ns=10 (Template namespace) edits → top templates touched
          - CLS_INFOBOX_UPDATE edits → infobox comment samples
          - yearly velocity for template-ns edits
        """
        jsonl_path = dir_ / "wikimedia_normalized_edits.jsonl"
        if not jsonl_path.exists():
            return _empty_template_summary()

        template_ns_counter: Counter[str] = Counter()
        infobox_comments: list[str] = []
        template_comments: list[str] = []
        yearly: Counter[str] = Counter()

        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ns = rec.get("page", {}).get("namespace_id", -1)
                comment = rec.get("comment", "")
                cls = rec.get("classification", "")
                ts = rec.get("timestamp", "")

                if ns == 10:  # Template namespace
                    title = rec.get("page", {}).get("title", "")
                    template_ns_counter[title] += 1
                    if comment:
                        template_comments.append(comment)
                    if ts:
                        yearly[ts[:4]] += 1

                if cls == CLS_INFOBOX_UPDATE and comment:
                    infobox_comments.append(comment)

        top_templates = [
            {"title": t, "edits": c}
            for t, c in template_ns_counter.most_common(30)
        ]
        common_names = [
            t.replace("Template:", "")
            for t, _ in template_ns_counter.most_common(20)
        ]

        return TemplateEditSummary(
            total_template_ns_edits=sum(template_ns_counter.values()),
            total_infobox_edits=len(infobox_comments),
            top_templates_edited=top_templates,
            infobox_comment_samples=infobox_comments[:50],
            template_comment_samples=template_comments[:50],
            common_template_names=common_names,
            yearly_template_velocity=dict(sorted(yearly.items())),
        )

    # ------------------------------------------------------------------
    # Live API fetch (use sparingly — rate-limited)
    # ------------------------------------------------------------------

    def from_api(self, limit: int = 5000, projects: list[str] | None = None) -> AccountIngestResult:
        """Fetch live from MediaWiki APIs. Writes no artifacts — caller handles persistence."""
        targets = [PROJECTS[p] for p in (projects or PROJECTS.keys())]
        all_classified: list[EditClassification] = []

        for project in targets:
            client = WikimediaClient(project.api_endpoint)
            pulled = 0
            for batch in client.get_user_contributions(self.username):
                for raw in batch:
                    if pulled >= limit:
                        break
                    ev = normalize_contribution(raw, project, self.username)
                    all_classified.append(EditClassification(ev, classify_edit(ev)))
                    pulled += 1
                if pulled >= limit:
                    break

        artifacts_data = build_corpus_artifacts(all_classified)

        proj_sum = artifacts_data["wikimedia_project_summary"]
        cls_data = artifacts_data["wikimedia_edit_classification"]
        page_focus = artifacts_data["wikimedia_page_focus_report"]

        # Build template summary in-memory
        template_ns: Counter[str] = Counter()
        infobox_comments: list[str] = []
        template_comments: list[str] = []
        yearly: Counter[str] = Counter()

        for ce in all_classified:
            ev = ce.event
            if ev.page.namespace_id == 10:
                template_ns[ev.page.title] += 1
                if ev.comment:
                    template_comments.append(ev.comment)
                if ev.timestamp:
                    yearly[ev.timestamp[:4]] += 1
            if ce.category == CLS_INFOBOX_UPDATE and ev.comment:
                infobox_comments.append(ev.comment)

        template_summary = TemplateEditSummary(
            total_template_ns_edits=sum(template_ns.values()),
            total_infobox_edits=len(infobox_comments),
            top_templates_edited=[{"title": t, "edits": c} for t, c in template_ns.most_common(30)],
            infobox_comment_samples=infobox_comments[:50],
            template_comment_samples=template_comments[:50],
            common_template_names=[t.replace("Template:", "") for t, _ in template_ns.most_common(20)],
            yearly_template_velocity=dict(sorted(yearly.items())),
        )

        return AccountIngestResult(
            username=self.username,
            total_edits=proj_sum["total_edits"],
            by_project=proj_sum["by_project"],
            classification_distribution=cls_data["distribution"],
            template_summary=template_summary,
            page_focus=page_focus.get("most_edited_pages", []),
            artifacts_path=None,
        )


def _empty_template_summary() -> TemplateEditSummary:
    return TemplateEditSummary(
        total_template_ns_edits=0,
        total_infobox_edits=0,
        top_templates_edited=[],
        infobox_comment_samples=[],
        template_comment_samples=[],
        common_template_names=[],
        yearly_template_velocity={},
    )

