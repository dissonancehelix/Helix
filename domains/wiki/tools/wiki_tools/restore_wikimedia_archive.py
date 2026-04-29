#!/usr/bin/env python3
"""Restore normalized Wikimedia contribution history from archived API artifacts.

The raw zip is used only when restored locally as substantial provenance. This script reads the archived
pipeline outputs and materializes current wiki-domain normalized data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ARCHIVE = ROOT / "archive" / "raw" / "raw_datasets" / "wikipedia_2026-04-28.zip"
DEFAULT_NORMALIZED = ROOT / "domains" / "wiki" / "data" / "normalized"
DEFAULT_REPORTS = ROOT / "domains" / "wiki" / "reports"
DEFAULT_USERNAME = "Dissident93"

SUMMARY_FILES = {
    "run_log": "run_log.json",
    "ingest_manifest": "wikimedia_ingest_manifest.json",
    "project_summary": "wikimedia_project_summary.json",
    "edit_classification": "wikimedia_edit_classification.json",
    "namespace_distribution": "wikimedia_namespace_distribution.json",
    "yearly_activity": "wikimedia_yearly_activity.json",
    "page_focus_report": "wikimedia_page_focus_report.json",
}


def archive_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_member(members: list[str], suffix: str) -> str:
    matches = [m for m in members if m.endswith(suffix)]
    if not matches:
        raise FileNotFoundError(f"Missing archived member ending with {suffix!r}")
    if len(matches) > 1:
        raise ValueError(f"Ambiguous archived member for {suffix!r}: {matches}")
    return matches[0]


def read_json(zip_file: ZipFile, members: list[str], suffix: str) -> dict:
    name = find_member(members, suffix)
    return json.loads(zip_file.read(name).decode("utf-8"))


def read_edits(zip_file: ZipFile, members: list[str]) -> tuple[list[dict], str]:
    name = find_member(members, "wikimedia_normalized_edits.jsonl")
    edits = []
    with zip_file.open(name) as f:
        for line in f:
            if line.strip():
                edits.append(json.loads(line.decode("utf-8")))
    return edits, name


def build_summary(username: str, archive_path: Path, archive_members: list[str], edits: list[dict], summaries: dict) -> dict:
    projects = Counter(edit.get("project", "unknown") for edit in edits)
    namespaces = Counter(str((edit.get("page") or {}).get("namespace_id", "unknown")) for edit in edits)
    classifications = Counter(edit.get("classification", "unknown") for edit in edits)
    years = Counter((edit.get("timestamp") or "")[:4] for edit in edits if edit.get("timestamp"))
    titles = Counter((edit.get("page") or {}).get("title", "") for edit in edits if (edit.get("page") or {}).get("namespace_id") == 0)
    first_timestamp = min((e.get("timestamp") for e in edits if e.get("timestamp")), default=None)
    last_timestamp = max((e.get("timestamp") for e in edits if e.get("timestamp")), default=None)
    return {
        "dataset": "dissident93_wikimedia_history",
        "username": username,
        "status": "normalized_from_archived_api_pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_archive": str(archive_path.relative_to(ROOT)).replace("\\", "/"),
        "source_archive_sha256": archive_sha256(archive_path),
        "source_members": archive_members,
        "record_count": len(edits),
        "date_range": {
            "first": first_timestamp,
            "last": last_timestamp,
        },
        "by_project": dict(projects.most_common()),
        "by_namespace_id": dict(namespaces.most_common()),
        "by_classification": dict(classifications.most_common()),
        "by_year": dict(sorted(years.items())),
        "top_mainspace_pages": [{"title": title, "edits": count} for title, count in titles.most_common(30)],
        "archived_summaries": summaries,
    }


def write_report(report_path: Path, summary: dict, normalized_path: Path, summary_path: Path) -> None:
    project_rows = "\n".join(f"| `{k}` | {v:,} |" for k, v in summary["by_project"].items())
    class_rows = "\n".join(f"| `{k}` | {v:,} |" for k, v in list(summary["by_classification"].items())[:15])
    page_rows = "\n".join(f"| {row['title']} | {row['edits']:,} |" for row in summary["top_mainspace_pages"][:15])
    content = f"""# Wikimedia History Restore — Dissident93

## Scope

- Source archive: `{summary['source_archive']}`
- Source status: archived API pipeline output; source archive may be deleted after domain extraction
- Username: `{summary['username']}`
- Records restored: {summary['record_count']:,}
- Date range: {summary['date_range']['first']} to {summary['date_range']['last']}
- Normalized output: `{normalized_path.relative_to(ROOT).as_posix()}`
- Summary output: `{summary_path.relative_to(ROOT).as_posix()}`

## Project Split

| Project | Records |
|---|---:|
{project_rows}

## Edit Classification

| Classification | Records |
|---|---:|
{class_rows}

## Mainspace Focus

| Page | Records |
|---|---:|
{page_rows}

## Notes

This is normalized domain data, not raw provenance. The raw zip remains the evidence source. The restored JSON preserves per-edit normalized fields from the old API pipeline so wiki-domain tools can use the account history without unpacking the archive each time.
"""
    report_path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore Dissident93 Wikimedia normalized history from archive zip.")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_NORMALIZED)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(args.archive) as z:
        members = z.namelist()
        edits, edits_member = read_edits(z, members)
        summaries = {
            key: read_json(z, members, suffix)
            for key, suffix in SUMMARY_FILES.items()
            if any(m.endswith(suffix) for m in members)
        }

    archive_members = [edits_member]
    archive_members.extend(find_member(members, suffix) for suffix in SUMMARY_FILES.values() if any(m.endswith(suffix) for m in members))
    summary = build_summary(args.username, args.archive, archive_members, edits, summaries)

    normalized_path = args.out_dir / "dissident93_wikimedia_history.json"
    summary_path = args.out_dir / "dissident93_wikimedia_history_summary.json"
    report_path = args.reports_dir / "dissident93_wikimedia_history_restore.md"

    normalized_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "dataset": summary["dataset"],
                    "username": summary["username"],
                    "status": summary["status"],
                    "generated_at": summary["generated_at"],
                    "source_archive": summary["source_archive"],
                    "source_archive_sha256": summary["source_archive_sha256"],
                    "record_count": summary["record_count"],
                    "date_range": summary["date_range"],
                },
                "edits": edits,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(report_path, summary, normalized_path, summary_path)

    print(
        json.dumps(
            {
                "records": summary["record_count"],
                "normalized": str(normalized_path),
                "summary": str(summary_path),
                "report": str(report_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
