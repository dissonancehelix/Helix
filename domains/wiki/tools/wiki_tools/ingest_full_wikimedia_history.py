#!/usr/bin/env python3
"""Full Wikimedia contribution history ingester for Dissident93.

This is intentionally local and reproducible. It calls public Wikimedia APIs,
normalizes contribution rows into wiki-domain JSONL, and writes compact profile
artifacts that can be shared with an LLM without making it read every edit row.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_NORMALIZED = ROOT / "domains" / "wiki" / "data" / "normalized"
DEFAULT_REPORTS = ROOT / "domains" / "wiki" / "reports"
DEFAULT_USERNAME = "Dissident93"
USER_AGENT = "Dissident93-HelixWikiFullHistory/1.0 (https://en.wikipedia.org/wiki/User:Dissident93; local personal archive analysis)"


@dataclass(frozen=True)
class Project:
    code: str
    label: str
    endpoint: str


PROJECTS = {
    "enwiki": Project("enwiki", "English Wikipedia", "https://en.wikipedia.org/w/api.php"),
    "wikidata": Project("wikidata", "Wikidata", "https://www.wikidata.org/w/api.php"),
    "commons": Project("commons", "Wikimedia Commons", "https://commons.wikimedia.org/w/api.php"),
}

NAMESPACE_LABELS = {
    0: "main/article or item",
    1: "talk",
    2: "user",
    3: "user talk",
    4: "project",
    5: "project talk",
    6: "file",
    7: "file talk",
    10: "template",
    11: "template talk",
    14: "category",
    15: "category talk",
    120: "property",
    121: "property talk",
    828: "module",
    829: "module talk",
}


def api_get(endpoint: str, params: dict[str, str], retries: int = 5) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(endpoint + "?" + query, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if exc.code == 429 and retry_after:
                try:
                    wait = max(float(retry_after), 10.0)
                except ValueError:
                    wait = 30.0
            else:
                wait = min(60.0, 2 ** attempt)
            if attempt == retries - 1:
                raise
            print(f"[wikimedia] transient API error: {exc}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:
            if attempt == retries - 1:
                raise
            wait = min(60.0, 2 ** attempt)
            print(f"[wikimedia] transient API error: {exc}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def fetch_user_info(project: Project, username: str) -> dict[str, Any]:
    data = api_get(
        project.endpoint,
        {
            "action": "query",
            "list": "users",
            "ususers": username,
            "usprop": "registration|editcount|groups",
            "format": "json",
        },
    )
    return (data.get("query", {}).get("users") or [{}])[0]


def fetch_contributions(project: Project, username: str, sleep: float = 0.05) -> Iterable[dict[str, Any]]:
    params = {
        "action": "query",
        "list": "usercontribs",
        "ucuser": username,
        "uclimit": "500",
        "ucdir": "newer",
        "ucprop": "ids|title|timestamp|comment|size|sizediff|flags|tags",
        "format": "json",
        "formatversion": "2",
    }
    continue_params: dict[str, str] = {}
    while True:
        data = api_get(project.endpoint, params | continue_params)
        for row in data.get("query", {}).get("usercontribs", []):
            yield row
        cont = data.get("continue", {})
        if "uccontinue" not in cont:
            break
        continue_params = {"uccontinue": cont["uccontinue"], "continue": cont.get("continue", "-||")}
        if sleep:
            time.sleep(sleep)


def classify(project_code: str, ns: int, comment: str, sizediff: int, is_new: bool, is_minor: bool) -> str:
    low = (comment or "").lower()
    if project_code == "wikidata":
        return "structured_data_work"
    if ns == 6:
        return "media_or_file_work"
    if ns == 14:
        return "category_work"
    if ns == 10:
        return "template_work"
    if ns % 2 == 1:
        return "talk_page_discussion"
    if ns in (2, 3, 4, 12):
        return "project_maintenance"
    if is_new:
        return "article_creation"
    if any(word in low for word in ("revert", "undo", "undid")):
        return "revert_or_undo"
    if any(word in low for word in ("cite", "ref", "citation", "source")):
        return "reference_or_citation_work"
    if any(word in low for word in ("infobox", "ibox")):
        return "infobox_update"
    if any(word in low for word in ("lead", "intro", "lede")):
        return "lead_rewrite"
    if any(word in low for word in ("update", "current", "history", "year", "season")):
        return "chronology_update"
    if any(word in low for word in ("copyedit", "grammar", "typo", "spelling", "cleanup")) or low == "ce":
        return "copyedit_cleanup"
    if sizediff > 1500:
        return "article_expansion"
    if is_minor or (0 <= sizediff < 200 and not low):
        return "minor_polish"
    return "manual_review_required"


def normalize(project: Project, username: str, row: dict[str, Any]) -> dict[str, Any]:
    ns = int(row.get("ns", 0) or 0)
    sizediff = int(row.get("sizediff", 0) or 0)
    is_new = bool(row.get("new", False))
    is_minor = bool(row.get("minor", False))
    comment = row.get("comment", "") or ""
    return {
        "project": project.code,
        "project_label": project.label,
        "username": username,
        "timestamp": row.get("timestamp", ""),
        "page": {
            "page_id": row.get("pageid", 0),
            "title": row.get("title", ""),
            "namespace_id": ns,
            "namespace_label": NAMESPACE_LABELS.get(ns, f"namespace_{ns}"),
        },
        "revid": row.get("revid", 0),
        "parentid": row.get("parentid", 0),
        "size": row.get("size", 0),
        "sizediff": sizediff,
        "comment": comment,
        "is_minor": is_minor,
        "is_new": is_new,
        "tags": row.get("tags", []),
        "classification": classify(project.code, ns, comment, sizediff, is_new, is_minor),
    }


def bucket_domain(title: str, comment: str) -> str:
    text = f"{title} {comment}".lower()
    rules = [
        ("washington_commanders_nfl", ["washington commanders", "commanders", "redskins", "jayden daniels", "nfl", "football", "stadium"]),
        ("dota_esports", ["dota", "the international", "esports", "valve"]),
        ("video_games", ["video game", "nintendo", "sega", "sonic", "mega man", "persona", "dark souls", "elden ring", "fromsoftware"]),
        ("vgm_music", ["composer", "soundtrack", "nobuo", "uematsu", "yuzo", "koshiro", "mitsuda", "shimomura", "soken"]),
        ("templates_infoboxes", ["template:", "infobox", "navbox", "module:"]),
        ("biography", ["birth", "death", "businessman", "player", "actor", "composer"]),
        ("commons_media", ["file:", "photo", "image", "logo", "svg"]),
        ("wikidata_structured_data", ["q", "wikidata"]),
    ]
    for label, needles in rules:
        if any(n in text for n in needles):
            return label
    return "other"


def compact_examples(counter: Counter[str], limit: int = 30) -> list[dict[str, Any]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def analyze_history(normalized_path: Path, user_info: dict[str, Any]) -> dict[str, Any]:
    by_project: Counter[str] = Counter()
    by_namespace: Counter[str] = Counter()
    by_classification: Counter[str] = Counter()
    by_year: Counter[str] = Counter()
    by_domain_bucket: Counter[str] = Counter()
    top_pages: Counter[str] = Counter()
    top_main_pages: Counter[str] = Counter()
    top_template_pages: Counter[str] = Counter()
    top_comments: Counter[str] = Counter()
    first_edits: list[dict[str, Any]] = []
    latest_edits: list[dict[str, Any]] = []
    first_ts: str | None = None
    last_ts: str | None = None
    total = 0
    net_bytes = 0
    positive = 0
    negative = 0
    project_years: dict[str, Counter[str]] = defaultdict(Counter)

    with normalized_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            edit = json.loads(line)
            total += 1
            project = edit["project"]
            page = edit["page"]
            title = page["title"]
            ns = page["namespace_id"]
            ts = edit.get("timestamp", "")
            comment = edit.get("comment", "")
            sizediff = int(edit.get("sizediff", 0) or 0)
            cls = edit.get("classification", "unknown")

            by_project[project] += 1
            by_namespace[f"{ns}:{page.get('namespace_label', '')}"] += 1
            by_classification[cls] += 1
            if ts:
                by_year[ts[:4]] += 1
                project_years[project][ts[:4]] += 1
                first_ts = ts if first_ts is None else min(first_ts, ts)
                last_ts = ts if last_ts is None else max(last_ts, ts)
            by_domain_bucket[bucket_domain(title, comment)] += 1
            top_pages[f"{project}:{title}"] += 1
            if ns == 0:
                top_main_pages[f"{project}:{title}"] += 1
            if ns == 10:
                top_template_pages[f"{project}:{title}"] += 1
            if comment.strip():
                top_comments[comment.strip()] += 1
            net_bytes += sizediff
            if sizediff > 0:
                positive += sizediff
            elif sizediff < 0:
                negative += sizediff

            compact = {
                "project": project,
                "timestamp": ts,
                "title": title,
                "namespace": ns,
                "classification": cls,
                "sizediff": sizediff,
                "comment": comment[:140],
            }
            if len(first_edits) < 20:
                first_edits.append(compact)
            latest_edits.append(compact)
            if len(latest_edits) > 20:
                latest_edits.pop(0)

    return {
        "dataset": "dissident93_wikimedia_full_history_profile",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": user_info,
        "record_count": total,
        "date_range": {"first": first_ts, "last": last_ts},
        "by_project": dict(by_project.most_common()),
        "by_namespace": dict(by_namespace.most_common()),
        "by_classification": dict(by_classification.most_common()),
        "by_year": dict(sorted(by_year.items())),
        "by_project_year": {k: dict(sorted(v.items())) for k, v in sorted(project_years.items())},
        "by_domain_bucket": dict(by_domain_bucket.most_common()),
        "byte_change": {
            "net": net_bytes,
            "positive_added": positive,
            "negative_removed": negative,
        },
        "top_pages": compact_examples(top_pages, 100),
        "top_mainspace_pages": compact_examples(top_main_pages, 100),
        "top_template_pages": compact_examples(top_template_pages, 60),
        "top_repeated_comments": compact_examples(top_comments, 60),
        "first_edits_sample": first_edits,
        "latest_edits_sample": latest_edits,
        "interpretive_profile": build_interpretive_profile(by_domain_bucket, by_classification, by_namespace, top_main_pages, top_template_pages),
    }


def build_interpretive_profile(
    domains: Counter[str],
    classes: Counter[str],
    namespaces: Counter[str],
    top_main: Counter[str],
    top_templates: Counter[str],
) -> dict[str, Any]:
    dominant_domains = [name for name, _ in domains.most_common(8)]
    dominant_classes = [name for name, _ in classes.most_common(8)]
    return {
        "plain_language_summary": [
            "Dissident93 edits like an infrastructure maintainer: repeated work on pages, templates, data, images, and page architecture rather than one-off opinion writing.",
            "The account history is especially concentrated around NFL/Washington Commanders work, video games/esports, VGM/composer material, templates/infoboxes, structured data, and Commons media.",
            "High-volume repeated edits suggest long-horizon stewardship: returning to the same objects over years, keeping them current, structural, and machine-readable.",
        ],
        "dominant_domain_buckets": dominant_domains,
        "dominant_work_modes": dominant_classes,
        "llm_reading_guidance": [
            "Treat page choices as evidence of object-field attachment: the operator repeatedly maintains public knowledge objects that connect to larger worlds.",
            "Do not reduce the wiki pattern to fandom. The recurrent behavior is public structure repair, data hygiene, template logic, and continuity maintenance.",
            "Template, infobox, Wikidata, and Commons work should be read as externalized cognition: making public information more addressable and reusable.",
            "Early VGM/video-game edits matter because they show the account began through music/game evidence surfaces before expanding into wider public knowledge architecture.",
        ],
        "top_mainspace_signal": [name for name, _ in top_main.most_common(15)],
        "top_template_signal": [name for name, _ in top_templates.most_common(15)],
        "namespace_signal": [name for name, _ in namespaces.most_common(10)],
    }


def write_report(path: Path, profile: dict[str, Any], normalized_path: Path, profile_path: Path) -> None:
    user = profile["user"]
    project_rows = "\n".join(f"| `{k}` | {v:,} |" for k, v in profile["by_project"].items())
    year_rows = "\n".join(f"| {k} | {v:,} |" for k, v in profile["by_year"].items())
    domain_rows = "\n".join(f"| `{k}` | {v:,} |" for k, v in profile["by_domain_bucket"].items())
    class_rows = "\n".join(f"| `{k}` | {v:,} |" for k, v in list(profile["by_classification"].items())[:20])
    page_rows = "\n".join(f"| {x['name']} | {x['count']:,} |" for x in profile["top_mainspace_pages"][:25])
    first_rows = "\n".join(
        f"- {x['timestamp']} — `{x['project']}` — {x['title']} ({x['classification']})"
        for x in profile["first_edits_sample"][:10]
    )
    guidance = "\n".join(f"- {x}" for x in profile["interpretive_profile"]["llm_reading_guidance"])
    summary = "\n".join(f"- {x}" for x in profile["interpretive_profile"]["plain_language_summary"])
    content = f"""# Dissident93 Wiki Habits Profile

## Scope

- Account: `Dissident93`
- Registration: {user.get('registration')}
- Current API editcount by project: {user.get('project_editcounts')}
- Full normalized local history: `{normalized_path.relative_to(ROOT).as_posix()}`
- Compact machine profile: `{profile_path.relative_to(ROOT).as_posix()}`
- Records ingested: {profile['record_count']:,}
- Date range: {profile['date_range']['first']} to {profile['date_range']['last']}

## LLM Summary

{summary}

## How To Read This Evidence

{guidance}

## Project Split

| Project | Edits |
|---|---:|
{project_rows}

## Activity By Year

| Year | Edits |
|---|---:|
{year_rows}

## Work Modes

| Mode | Edits |
|---|---:|
{class_rows}

## Domain Buckets

| Bucket | Edits |
|---|---:|
{domain_rows}

## Top Mainspace / Item Pages

| Page | Edits |
|---|---:|
{page_rows}

## Earliest Local Contributions

{first_rows}

## Candidate DISSONANCE.md Sharpening

- Wiki evidence should be framed as public knowledge architecture and continuity maintenance across years, not as generic editing volume.
- The 2012 origin through VGM/video-game pages is important: wiki work begins as object-field attachment, then expands into templates, sports infrastructure, structured data, and Commons media.
- Repeated edits to the same public objects are evidence of return, repair, stewardship, and externalized cognition.
"""
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch full Wikimedia contribution history for Dissident93.")
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--projects", default="enwiki,wikidata,commons", help="Comma-separated project codes.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_NORMALIZED)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    selected = [PROJECTS[p.strip()] for p in args.projects.split(",") if p.strip()]
    user_info: dict[str, Any] = {"name": args.username, "projects": {}, "project_editcounts": {}}
    for project in selected:
        info = fetch_user_info(project, args.username)
        user_info["projects"][project.code] = info
        user_info["project_editcounts"][project.code] = info.get("editcount")
        user_info.setdefault("registration", info.get("registration"))

    normalized_path = args.out_dir / "dissident93_wikimedia_full_history.jsonl"
    count_by_project: Counter[str] = Counter()
    with normalized_path.open("w", encoding="utf-8", newline="\n") as f:
        for project in selected:
            print(f"[wikimedia] fetching full history for {project.code}", file=sys.stderr)
            for row in fetch_contributions(project, args.username, sleep=args.sleep):
                record = normalize(project, args.username, row)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count_by_project[project.code] += 1
                if count_by_project[project.code] % 10000 == 0:
                    print(f"[wikimedia] {project.code}: {count_by_project[project.code]:,} records", file=sys.stderr)
            print(f"[wikimedia] finished {project.code}: {count_by_project[project.code]:,} records", file=sys.stderr)

    profile = analyze_history(normalized_path, user_info)
    profile["fetch_counts"] = dict(count_by_project)
    profile_path = args.out_dir / "dissident93_wikimedia_full_history_profile.json"
    report_path = args.reports_dir / "dissident93_wiki_habits_profile.md"
    write_json(profile_path, profile)
    write_report(report_path, profile, normalized_path, profile_path)

    print(
        json.dumps(
            {
                "records": profile["record_count"],
                "date_range": profile["date_range"],
                "normalized_jsonl": str(normalized_path),
                "profile_json": str(profile_path),
                "report": str(report_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
