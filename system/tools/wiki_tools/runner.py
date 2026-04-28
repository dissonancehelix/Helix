"""
Helix Language Domain — Phase 1: Wikimedia Trace Ingestion
Runner CLI for ingesting user contributions from multiple Wikimedia APIs.

Provides an operator-facing ingest and classification layer.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from model.domains.language.ingestion.wikimedia import (
    WikimediaClient, WikiProjectSource, normalize_contribution,
    classify_edit, EditClassification, build_corpus_artifacts
)

_ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


# ---------------------------------------------------------------------------
# Project Targets Supported in Phase 1
# ---------------------------------------------------------------------------
SUPPORTED_PROJECTS = {
    "enwiki": WikiProjectSource(
        domain="en.wikipedia.org",
        shortcode="enwiki",
        api_endpoint="https://en.wikipedia.org/w/api.php",
    ),
    "wikidata": WikiProjectSource(
        domain="www.wikidata.org",
        shortcode="wikidata",
        api_endpoint="https://www.wikidata.org/w/api.php",
    ),
    "commons": WikiProjectSource(
        domain="commons.wikimedia.org",
        shortcode="commons",
        api_endpoint="https://commons.wikimedia.org/w/api.php",
    )
}

# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wikimedia_ingest",
        description="Helix Wikimedia Ingestion (Language Domain Phase 1)"
    )
    
    parser.add_argument("--username", type=str, required=True,
                        help="Wikimedia username to ingest (e.g., Dissident93)")
    parser.add_argument("--project", type=str, default="all",
                        choices=["enwiki", "wikidata", "commons", "all"],
                        help="Target project to ingest from (default: all)")
    parser.add_argument("--limit", type=int, default=5000,
                        help="Maximum total records per project to pull (default: 5000)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Connect and parse, but do not write output JSON")
    
    return parser


# ---------------------------------------------------------------------------
# Core Runner Logic
# ---------------------------------------------------------------------------

def _run_ingest(args: argparse.Namespace) -> int:
    """Execute Wikimedia trace ingestion and classification."""
    targets = list(SUPPORTED_PROJECTS.values()) if args.project == "all" else [SUPPORTED_PROJECTS[args.project]]
    
    run_id = f"wiki_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = _ARTIFACTS_DIR / run_id
    
    if not args.dry_run:
        run_dir.mkdir(parents=True, exist_ok=True)
    
    # Run Log accumulation 
    run_log = {
        "run_id": run_id,
        "username": args.username,
        "timestamp": datetime.now().isoformat(),
        "args": vars(args),
        "source_endpoints_used": [t.api_endpoint for t in targets],
        "record_counts": {},
        "errors": [],
    }
    
    all_classified: list[EditClassification] = []
    
    print(f"\n[wikimedia] Starting Language Domain Trace Ingestion")
    print(f"[wikimedia] Target User: {args.username}")
    print(f"[wikimedia] Run ID:    {run_id}\n")

    for project in targets:
        print(f"── Ingesting: {project.shortcode} ({project.api_endpoint})")
        client = WikimediaClient(project.api_endpoint)
        
        pulled = 0
        project_classifications = []
        for batch in client.get_user_contributions(args.username):
            for raw_record in batch:
                if pulled >= args.limit:
                    break
                    
                # 1. Normalize Trace
                event = normalize_contribution(raw_record, project, args.username)
                
                # 2. Assign Structural Classification
                category = classify_edit(event)
                
                ce = EditClassification(event, category)
                project_classifications.append(ce)
                pulled += 1
                
            print(f"   [+] Retreived {pulled} records from {project.shortcode}...")
            if pulled >= args.limit:
                break
        
        all_classified.extend(project_classifications)
        run_log["record_counts"][project.shortcode] = len(project_classifications)
        print(f"   Finished {project.shortcode}: {len(project_classifications)} traces normalized.\n")

    print("[wikimedia] ── BUILDING ARTIFACTS ──")
    
    # 3. Aggregation & Corpus generation
    artifacts_data = build_corpus_artifacts(all_classified)
    run_log["outputs_written"] = []
    
    for key, data in artifacts_data.items():
        if not args.dry_run:
            ext = "jsonl" if key == "wikimedia_normalized_edits" else "json"
            out_file = run_dir / f"{key}.{ext}"
            
            if ext == "jsonl":
                with open(out_file, "w", encoding="utf-8") as f:
                    for line in data:
                        f.write(json.dumps(line) + "\n")
            else:
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                    
            run_log["outputs_written"].append(str(out_file.name))
        
        # Verbose explicit count logging
        if isinstance(data, dict) and "total_edits" in data:
            print(f"   Generated {key}: {data['total_edits']} records processed.")
        elif isinstance(data, dict) and "total_unique_main_pages" in data:
             print(f"   Generated {key}: {data['total_unique_main_pages']} unique mainspace pages.")
    
    # Manifest writing
    if not args.dry_run:
        manifest_path = run_dir / "wikimedia_ingest_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": run_id,
                "project_counts": run_log["record_counts"],
                "total_records": sum(run_log["record_counts"].values())
            }, f, indent=2)
        run_log["outputs_written"].append(manifest_path.name)
        
        log_path = run_dir / "run_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(run_log, f, indent=2)

        _write_phase1_summary(run_dir, run_id, run_log, artifacts_data)

    print(f"\n[wikimedia] Ingestion Complete!")
    if not args.dry_run:
        print(f"   Artifacts saved to: {run_dir}")
    else:
        print(f"   Dry run completed -- No artifacts were saved.")
        
    return 0


# ---------------------------------------------------------------------------
# Phase 1 Summary Markdown Generation
# ---------------------------------------------------------------------------

def _write_phase1_summary(run_dir: Path, run_id: str, run_log: dict, artifacts: dict) -> None:
    lines = [
        "# Helix Language Phase 1: Wikimedia Trace Ingestion Summary",
        f"Run ID: `{run_id}`",
        f"Generated: {run_log['timestamp']}",
        f"User Identity: `@{run_log['username']}`",
        "",
        "---",
        "",
        "## Source Ingestion & Project Split",
        "| Project | Extracted Traces |",
        "|---------|------------------|"
    ]
    total = sum(run_log["record_counts"].values())
    for p, count in run_log["record_counts"].items():
        lines.append(f"| `{p}` | {count:,} |")
    lines.append(f"| **Total** | **{total:,}** |")
    
    lines += [
        "",
        "## Overall Action Classification",
        "| Edit Bucket | Count |",
        "|-------------|-------|"
    ]
    
    cls_dist = artifacts.get("wikimedia_edit_classification", {}).get("distribution", {})
    for bucket, count in cls_dist.items():
        lines.append(f"| `{bucket}` | {count:,} |")
        
    lines += [
        "",
        "## Output Artifacts",
        "| File | Purpose |",
        "|------|---------|",
        "| `wikimedia_ingest_manifest.json` | High-level index of source runs |",
        "| `wikimedia_normalized_edits.jsonl` | Helix normalized raw event schema map |",
        "| `wikimedia_project_summary.json` | Top level counts bounded by project authority |",
        "| `wikimedia_edit_classification.json` | Structural inferences across history |",
        "| `wikimedia_namespace_distribution.json` | Focus metrics grouped by Wikimedia semantic domain |",
        "| `wikimedia_yearly_activity.json` | Contribution velocity over time |",
        "| `wikimedia_page_focus_report.json` | Main-space corpus density mappings |",
        "| `run_log.json` | Trace execution history |"
    ]
    
    (run_dir / "language_phase1_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(_run_ingest(args))

if __name__ == "__main__":
    main()

