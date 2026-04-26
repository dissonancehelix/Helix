"""
reports.py — Report formatting and artifact output for the Foobar tool.

Writes all output to domains/music/tools/foobar/artifacts/.
Never writes to Atlas, Foobar SQLite internals, or external tags.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TOOL_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = _TOOL_ROOT / "artifacts"


# ---------------------------------------------------------------------------
# Artifact path helpers
# ---------------------------------------------------------------------------

def _artifact(name: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / name


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ---------------------------------------------------------------------------
# JSON writer
# ---------------------------------------------------------------------------

def write_json(name: str, data: Any, *, indent: int = 2) -> Path:
    path = _artifact(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)
    return path


# ---------------------------------------------------------------------------
# audit_summary.md
# ---------------------------------------------------------------------------

def write_audit_summary(
    sync_result: dict,
    library_audit: dict,
    schema_audit: dict,
    structure_audit: dict,
    loved_audit: dict,
    *,
    library_root: str = "",
    runtime_root: str = "",
    corpus_results: list[dict] | None = None,
) -> Path:
    """Write the human-readable audit summary markdown."""

    summary = sync_result.get("summary", {})
    lines = [
        "# Helix Foobar Tool — Audit Summary",
        f"Generated: {_now_str()}",
        "",
        "---",
        "",
        "## Roots",
        f"- **Library corpus root:** `{library_root or 'not set'}`",
        f"- **Foobar runtime root:** `{runtime_root or 'not set'}`",
        "",
        "---",
        "",
        "## Sync Overview",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Foobar tracks scanned | {sync_result.get('total_foobar', 0)} |",
        f"| Codex records | {sync_result.get('total_codex', 0)} |",
    ]

    for state, count in sorted(summary.items()):
        lines.append(f"| {state} | {count} |")

    lines += [
        "",
        "---",
        "",
        "## Library Health",
        f"- Tracks checked: {library_audit.get('total_checked', 0)}",
        f"- Total issues: {library_audit.get('total_issues', 0)}",
    ]

    # Top issue codes
    issue_codes: dict[str, int] = {}
    for iss in library_audit.get("issues", []):
        code = iss.get("issue_code", "unknown")
        issue_codes[code] = issue_codes.get(code, 0) + 1
    if issue_codes:
        lines.append("")
        lines.append("### Issue breakdown")
        lines.append("| Issue Code | Count |")
        lines.append("|------------|-------|")
        for code, cnt in sorted(issue_codes.items(), key=lambda x: -x[1]):
            lines.append(f"| `{code}` | {cnt} |")

    lines += [
        "",
        "---",
        "",
        "## Custom Schema Coverage",
        f"- Tracks checked: {schema_audit.get('total_checked', 0)}",
        f"- Schema issues: {schema_audit.get('total_issues', 0)}",
    ]

    alias_cands = schema_audit.get("alias_candidates", [])
    if alias_cands:
        lines.append(f"- Sound team alias candidates: {len(alias_cands)}")
        lines.append("")
        lines.append("### Sound team alias candidates")
        for a in alias_cands[:10]:
            lines.append(f"  - `{a['normalized']}` → variants: {a['variants']}")

    p_chip = schema_audit.get("platform_chip_distribution", {})
    if p_chip:
        lines.append("")
        lines.append("### Platform / chip distribution (top 10)")
        lines.append("| Platform / Chip | Count |")
        lines.append("|-----------------|-------|")
        for k, v in list(p_chip.items())[:10]:
            lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "---",
        "",
        "## Release Structure",
        f"- Albums checked: {structure_audit.get('total_albums', 0)}",
        f"- Albums with issues: {structure_audit.get('albums_with_issues', 0)}",
        f"- Total structural issues: {structure_audit.get('total_issues', 0)}",
    ]

    album_reps = structure_audit.get("album_reports", [])
    if album_reps:
        lines.append("")
        lines.append("### Albums with numbering issues")
        lines.append("| Album | Tracks | Issues |")
        lines.append("|-------|--------|--------|")
        for a in album_reps[:20]:
            lines.append(f"| {a['album']!r} | {a['track_count']} | {', '.join(a['issues'])} |")

    lines += [
        "",
        "---",
        "",
        "## Loved / Stats",
        f"- Loved in Foobar: {loved_audit.get('total_loved_foobar', 0)}",
        f"- Loved drift count: {loved_audit.get('loved_drift_count', 0)}",
        f"- Newly loved (not yet in codex): {loved_audit.get('newly_loved_count', 0)}",
        f"- Stats drift count: {loved_audit.get('stats_drift_count', 0)}",
        f"- Priority refresh candidates: {loved_audit.get('priority_refresh_count', 0)}",
    ]

    if loved_audit.get("newly_loved"):
        lines.append("")
        lines.append("### Newly loved tracks (sample, first 10)")
        lines.append("| Title | Album |")
        lines.append("|-------|-------|")
        for t in loved_audit["newly_loved"][:10]:
            lines.append(f"| {t.get('title')} | {t.get('album')} |")

    # Research corpus results
    if corpus_results:
        lines += [
            "",
            "---",
            "",
            "## Research Corpus Integrity",
        ]
        for cr in corpus_results:
            status = cr.get("status", "unknown")
            status_icon = "✓" if status == "healthy" else "⚠"
            lines += [
                f"### {status_icon} {cr.get('corpus_name')}",
                f"- Status: **{status}**",
                f"- Track count: {cr.get('track_count', 0)}",
                f"- In codex: {cr.get('in_codex', 0)}",
                f"- Issues: {cr.get('issue_count', 0)}",
            ]
            for iss in cr.get("issues", []):
                lines.append(f"  - `{iss['issue_code']}`: {iss.get('detail', '')}")

    lines += [
        "",
        "---",
        "",
        "## Output Artifacts",
        f"All artifacts written to: `{ARTIFACTS_DIR}`",
        "",
        "| File | Contents |",
        "|------|----------|",
        "| `audit_summary.md` | This file |",
        "| `track_issues.json` | Per-track issues |",
        "| `album_issues.json` | Per-album issues |",
        "| `sync_manifest.json` | Full sync state per track |",
        "| `repair_plan.csv` | Reviewable patch plan |",
        "| `new_in_foobar.json` | Tracks not yet in codex |",
        "| `codex_orphans.json` | Codex records with no library source |",
        "| `loved_drift.json` | Loved / stats drift |",
        "| `normalization_candidates.json` | Alias and normalization candidates |",
    ]

    path = _artifact("audit_summary.md")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Individual artifact writers
# ---------------------------------------------------------------------------

def write_track_issues(library_audit: dict) -> Path:
    issues = [
        {k: v for k, v in iss.items() if k != "diff"}
        for iss in library_audit.get("issues", [])
    ]
    return write_json("track_issues.json", issues)


def write_album_issues(structure_audit: dict) -> Path:
    return write_json("album_issues.json", structure_audit.get("album_reports", []))


def write_sync_manifest(sync_result: dict) -> Path:
    manifest = []
    for tr in sync_result.get("track_results", []):
        entry = {
            "file_path": tr.get("file_path"),
            "states": tr.get("states", []),
            "title": None, "album": None, "artist": None,
            "platform": None, "franchise": None, "sound_chip": None,
            "loved": None,
        }
        fb = tr.get("foobar_record", {})
        if fb:
            from .diff import _norm, _norm_bool
            entry.update({
                "title": _norm(fb.get("title")),
                "album": _norm(fb.get("album")),
                "artist": _norm(fb.get("artist")),
                "platform": _norm(fb.get("platform")),
                "franchise": _norm(fb.get("franchise")),
                "sound_chip": _norm(fb.get("sound_chip")),
                "loved": _norm_bool(fb.get("loved")),
            })
        manifest.append(entry)

    for orp in sync_result.get("codex_orphans", []):
        cx = orp.get("codex_record", {})
        manifest.append({
            "file_path": orp.get("file_path"),
            "states": ["codex_orphan"],
            "title": cx.get("title"), "album": cx.get("album"),
        })

    return write_json("sync_manifest.json", {
        "generated": _now_str(),
        "summary": sync_result.get("summary", {}),
        "total_foobar": sync_result.get("total_foobar"),
        "total_codex": sync_result.get("total_codex"),
        "tracks": manifest,
    })


def write_new_in_foobar(sync_result: dict) -> Path:
    new_tracks = [
        tr for tr in sync_result.get("track_results", [])
        if "new_in_foobar" in tr.get("states", [])
    ]
    out = []
    for tr in new_tracks:
        fb = tr.get("foobar_record", {})
        from .diff import _norm
        out.append({
            "file_path": fb.get("file_path"),
            "title": _norm(fb.get("title")),
            "album": _norm(fb.get("album")),
            "artist": _norm(fb.get("artist")),
            "platform": _norm(fb.get("platform")),
            "franchise": _norm(fb.get("franchise")),
        })
    return write_json("new_in_foobar.json", out)


def write_codex_orphans(sync_result: dict) -> Path:
    orphans = []
    for orp in sync_result.get("codex_orphans", []):
        cx = orp.get("codex_record", {})
        orphans.append({
            "file_path": orp.get("file_path"),
            "title": cx.get("title"),
            "album": cx.get("album"),
            "ingested_ts": cx.get("ingested_ts"),
        })
    return write_json("codex_orphans.json", orphans)


def write_loved_drift(loved_audit: dict) -> Path:
    return write_json("loved_drift.json", {
        "generated": _now_str(),
        "total_loved_foobar": loved_audit.get("total_loved_foobar"),
        "loved_drift": loved_audit.get("loved_drift", []),
        "newly_loved": loved_audit.get("newly_loved", []),
        "stats_drift": loved_audit.get("stats_drift", []),
        "priority_refresh": loved_audit.get("priority_refresh", []),
    })


def write_normalization_candidates(schema_audit: dict) -> Path:
    return write_json("normalization_candidates.json", {
        "generated": _now_str(),
        "sound_team_aliases": schema_audit.get("alias_candidates", []),
        "schema_issues": [
            iss for iss in schema_audit.get("issues", [])
            if iss.get("issue_code") in (
                "platform_without_franchise",
                "franchise_without_platform",
                "suspicious_chip_platform",
                "mixed_franchise_in_album",
            )
        ],
    })


def write_corpus_manifest(corpus_result: dict) -> Path:
    name = corpus_result.get("corpus_name", "corpus").replace(" ", "_").lower()
    filename = f"corpus_{name}_manifest.json"
    return write_json(filename, {
        "generated": _now_str(),
        "corpus_name": corpus_result.get("corpus_name"),
        "status": corpus_result.get("status"),
        "track_count": corpus_result.get("track_count"),
        "in_codex": corpus_result.get("in_codex"),
        "issues": corpus_result.get("issues", []),
        "manifest": corpus_result.get("manifest", []),
    })


# ---------------------------------------------------------------------------
# Console summary printer
# ---------------------------------------------------------------------------

def print_summary(sync_result: dict, *, verbose: bool = False) -> None:
    summary = sync_result.get("summary", {})
    print()
    print("=== Foobar Tool — Sync Summary ===")
    print(f"  Foobar tracks : {sync_result.get('total_foobar', 0)}")
    print(f"  Codex records : {sync_result.get('total_codex', 0)}")
    print()
    for state, count in sorted(summary.items()):
        icon = "✓" if state == "in_sync" else "⚠" if count > 0 else " "
        print(f"  {icon}  {state:<35} {count}")
    print()
