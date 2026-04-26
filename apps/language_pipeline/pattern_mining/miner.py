"""
Pattern miner — extracts reusable editing patterns from the operator's JSONL history.

Operates on the normalized JSONL artifact from the ingest runner.
Does not call the live API. Output is advisory — patterns require human review
before promotion to the pattern library.

Mining strategy:
  - Group by comment text clusters → surface recurring edit intents
  - Identify template-namespace edits with recurring comment signatures
  - Identify main-ns infobox edits by comment keyword
  - Find size-diff signatures (net-neutral, small-positive, small-negative)
  - Extract repeated page+comment co-occurrences (same page, same comment family)
  - Flag "leave it alone" candidates (reverted or immediately followed edits)

Each mined pattern has a confidence level:
  high   — appears in 5+ distinct edits with consistent comment+ns profile
  medium — appears in 2-4 edits
  low    — single observation, noted but not promoted
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_ARTIFACT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data" / "artifacts"
    / "wiki_20260329_222848"
)

_COMMENT_CLUSTERS: dict[str, list[str]] = {
    "infobox_update":     [r"\binfobox\b", r"\bibox\b"],
    "template_fix":       [r"\btemplate\b", r"\btlx\b", r"\b{{"],
    "stat_update":        [r"\bstat\b", r"\bstatistic\b", r"\bcareer\b"],
    "link_fix":           [r"\blink\b", r"\bwikilink\b", r"\bpiped\b"],
    "date_fix":           [r"\bdate\b", r"\bborn\b", r"\bdied\b"],
    "ref_fix":            [r"\bcite\b", r"\bref\b", r"\bcitation\b"],
    "revert":             [r"\brevert\b", r"\bundid\b", r"\bundo\b"],
    "copyedit":           [r"\bce\b", r"\bcopy\b", r"\bgrammar\b", r"\btypo\b"],
    "lead_section":       [r"\blead\b", r"\blede\b", r"\bintro\b"],
    "nfl_specific":       [r"\bnfl\b", r"\bdraft\b", r"\bcommanders\b", r"\bearns\b"],
    "vg_specific":        [r"\bgame\b", r"\bvg\b", r"\bvideo\b", r"\bdota\b"],
    "whitespace_cleanup": [r"\bws\b", r"\bwhitespace\b", r"\bspacing\b", r"\bblank\b"],
    "deprecated_param":   [r"\bdeprecated\b", r"\bremov\b", r"\bclean\b", r"\bparam\b"],
    "fallback_add":       [r"\bfallback\b", r"\balias\b", r"\bdefault\b"],
}


@dataclass
class MinedPattern:
    id: str
    name: str
    cluster: str                  # which comment cluster triggered this
    evidence_count: int           # number of distinct edits supporting it
    evidence_samples: list[str]   # up to 5 example comments
    namespace_ids: list[int]      # namespaces this was observed in
    size_diff_profile: str        # "net_neutral" | "small_add" | "small_remove" | "large_add" | "mixed"
    likely_purpose: str
    risk_notes: str
    confidence: str               # "high" | "medium" | "low"
    top_pages: list[str]          # pages this pattern was applied to most

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "cluster": self.cluster,
            "evidence_count": self.evidence_count,
            "evidence_samples": self.evidence_samples,
            "namespace_ids": self.namespace_ids,
            "size_diff_profile": self.size_diff_profile,
            "likely_purpose": self.likely_purpose,
            "risk_notes": self.risk_notes,
            "confidence": self.confidence,
            "top_pages": self.top_pages,
        }


@dataclass
class MiningReport:
    total_edits_scanned: int
    patterns_found: list[MinedPattern]
    leave_alone_candidates: list[str]   # pages with revert evidence
    high_frequency_pages: list[dict]    # [{title, edits}] top 20
    comment_cluster_dist: dict[str, int]

    def display_summary(self) -> str:
        lines = [
            f"Mining report: {self.total_edits_scanned:,} edits scanned",
            f"Patterns found: {len(self.patterns_found)} "
            f"({sum(1 for p in self.patterns_found if p.confidence == 'high')} high confidence)",
            f"Leave-alone candidates: {len(self.leave_alone_candidates)}",
            "",
            "Top clusters:",
        ]
        for cluster, count in sorted(self.comment_cluster_dist.items(), key=lambda x: -x[1])[:8]:
            lines.append(f"  {cluster:25s} {count:,}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "total_edits_scanned": self.total_edits_scanned,
            "patterns_found": [p.to_dict() for p in self.patterns_found],
            "leave_alone_candidates": self.leave_alone_candidates,
            "high_frequency_pages": self.high_frequency_pages,
            "comment_cluster_dist": self.comment_cluster_dist,
        }


class PatternMiner:
    """
    Mines the operator's JSONL edit history for recurring patterns.

    Usage:
        miner = PatternMiner()
        report = miner.mine()
        print(report.display_summary())
        miner.save(report)
    """

    def __init__(self, artifact_dir: Path | None = None):
        self.artifact_dir = artifact_dir or _ARTIFACT_ROOT

    def mine(self) -> MiningReport:
        records = self._load_records()
        if not records:
            return MiningReport(0, [], [], [], {})

        cluster_buckets: dict[str, list[dict]] = defaultdict(list)
        page_counter: Counter[str] = Counter()
        revert_pages: set[str] = set()

        for rec in records:
            comment = rec.get("comment", "").lower()
            ns = rec.get("page", {}).get("namespace_id", -1)
            title = rec.get("page", {}).get("title", "")
            cls = rec.get("classification", "")

            # Track revert evidence
            if cls == "revert_or_undo":
                revert_pages.add(title)

            # Page frequency (main ns only)
            if ns == 0 and title:
                page_counter[title] += 1

            # Cluster assignment
            matched = False
            for cluster, patterns in _COMMENT_CLUSTERS.items():
                if any(re.search(p, comment) for p in patterns):
                    cluster_buckets[cluster].append(rec)
                    matched = True
                    break
            if not matched and ns == 10:
                cluster_buckets["template_fix"].append(rec)

        # Build mined patterns from clusters
        mined: list[MinedPattern] = []
        cluster_dist: dict[str, int] = {}

        for cluster, edits in cluster_buckets.items():
            cluster_dist[cluster] = len(edits)
            if len(edits) < 2:
                continue

            # Namespace profile
            ns_counts: Counter[int] = Counter(
                e.get("page", {}).get("namespace_id", -1) for e in edits
            )
            ns_ids = [ns for ns, _ in ns_counts.most_common(3)]

            # Size diff profile
            diffs = [e.get("sizediff", 0) for e in edits]
            size_profile = self._classify_size_profile(diffs)

            # Evidence samples (unique comments, up to 5)
            comments = list({
                e.get("comment", "").strip()
                for e in edits
                if e.get("comment", "").strip()
            })[:5]

            # Top pages
            page_ctr: Counter[str] = Counter(
                e.get("page", {}).get("title", "") for e in edits
            )
            top_pages = [t for t, _ in page_ctr.most_common(5) if t]

            confidence = "high" if len(edits) >= 5 else "medium"

            purpose, risk = self._infer_purpose_risk(cluster, ns_ids, size_profile)

            mined.append(MinedPattern(
                id=f"mined_{cluster}",
                name=self._cluster_to_name(cluster),
                cluster=cluster,
                evidence_count=len(edits),
                evidence_samples=comments,
                namespace_ids=ns_ids,
                size_diff_profile=size_profile,
                likely_purpose=purpose,
                risk_notes=risk,
                confidence=confidence,
                top_pages=top_pages,
            ))

        mined.sort(key=lambda p: -p.evidence_count)

        high_freq = [
            {"title": t, "edits": c}
            for t, c in page_counter.most_common(20)
        ]

        return MiningReport(
            total_edits_scanned=len(records),
            patterns_found=mined,
            leave_alone_candidates=sorted(revert_pages)[:30],
            high_frequency_pages=high_freq,
            comment_cluster_dist=cluster_dist,
        )

    def save(self, report: MiningReport, out_dir: Path | None = None) -> Path:
        target = out_dir or (
            Path(__file__).resolve().parents[1]
            / "data"
        )
        target.mkdir(parents=True, exist_ok=True)
        path = target / "edit_pattern_mining_report.json"
        path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_records(self) -> list[dict]:
        jsonl = self.artifact_dir / "wikimedia_normalized_edits.jsonl"
        if not jsonl.exists():
            return []
        records = []
        with open(jsonl, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records

    @staticmethod
    def _classify_size_profile(diffs: list[int]) -> str:
        if not diffs:
            return "unknown"
        avg = sum(diffs) / len(diffs)
        pos = sum(1 for d in diffs if d > 50)
        neg = sum(1 for d in diffs if d < -50)
        if abs(avg) < 30:
            return "net_neutral"
        if pos > neg * 2:
            return "small_add" if avg < 500 else "large_add"
        if neg > pos * 2:
            return "small_remove"
        return "mixed"

    @staticmethod
    def _cluster_to_name(cluster: str) -> str:
        return {
            "infobox_update":     "Infobox parameter update",
            "template_fix":       "Template namespace edit",
            "stat_update":        "Career statistics update",
            "link_fix":           "Wikilink correction",
            "date_fix":           "Date/birth/death field fix",
            "ref_fix":            "Reference/citation work",
            "revert":             "Revert or undo",
            "copyedit":           "Copy-edit / grammar / typo",
            "lead_section":       "Lead section rewrite",
            "nfl_specific":       "NFL-specific structural edit",
            "vg_specific":        "Video game-specific edit",
            "whitespace_cleanup": "Whitespace / blank line cleanup",
            "deprecated_param":   "Deprecated parameter removal",
            "fallback_add":       "Fallback / alias / default add",
        }.get(cluster, cluster.replace("_", " ").title())

    @staticmethod
    def _infer_purpose_risk(cluster: str, ns_ids: list[int], size_profile: str) -> tuple[str, str]:
        purpose_map = {
            "infobox_update":     ("Update infobox field values, usually chronology or stats.",
                                   "BLP risk if updating living person facts without citation."),
            "template_fix":       ("Fix or improve a template in Template namespace.",
                                   "Review rendered output; template changes affect all transclusions."),
            "stat_update":        ("Update career statistics in article body or infobox.",
                                   "Verify source; stats are frequently contested."),
            "link_fix":           ("Fix broken, double, or over-linked wikilinks.",
                                   "Low risk. Check disambiguation targets."),
            "date_fix":           ("Correct or add birth/death/event dates.",
                                   "BLP risk for living persons. Require inline citation."),
            "ref_fix":            ("Add, fix, or consolidate inline references.",
                                   "Low risk. Check ref name collisions."),
            "revert":             ("Undo a prior edit.",
                                   "Context-dependent. Review what was reverted before mimicking."),
            "copyedit":           ("Grammar, typo, or prose cleanup.",
                                   "Low risk. Watch for meaning changes in borderline BLP content."),
            "lead_section":       ("Rewrite or update the article lead.",
                                   "Lead must summarize body. BLP sensitivity applies."),
            "nfl_specific":       ("NFL article structural edit (draft, contract, team history).",
                                   "WP:NFL notability + BLP apply. Contract/salary needs sourcing."),
            "vg_specific":        ("Video game article edit (platform, release, gameplay).",
                                   "MOS:VG applies. Avoid peacock terms."),
            "whitespace_cleanup": ("Remove trailing whitespace, blank lines, extra spaces.",
                                   "Safe. No semantic change."),
            "deprecated_param":   ("Remove or replace deprecated template parameters.",
                                   "Check for legacy transclusions still using the old param name."),
            "fallback_add":       ("Add fallback/alias/default to template parameter.",
                                   "Safe if old param name is genuinely unused. Verify."),
        }
        purpose, risk = purpose_map.get(cluster, ("Recurring edit pattern.", "Review context."))
        if 10 in ns_ids:
            risk += " Template-namespace change — affects all transclusions."
        return purpose, risk
