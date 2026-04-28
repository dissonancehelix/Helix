#!/usr/bin/env python3
"""
run_manual_scoring.py

Reads example_items.jsonl and writes a blank scoring template JSONL to
labs/research/personal_ontology/tests/runs/.

Output: runs/scoring_YYYYMMDD.jsonl
Each entry is a blank ScoreRecord conforming to personal_ontology_test_schema.json.
Fill in the 'scores' block manually after the file is generated.

Usage:
    python run_manual_scoring.py
    python run_manual_scoring.py --filter ont_001_friction
    python run_manual_scoring.py --scorer operator --state REST

No external dependencies. Stdlib only. Output directory is gitignored.
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
INPUT_FILE = SCRIPT_DIR / "example_items.jsonl"
RUNS_DIR = SCRIPT_DIR / "runs"

SCORE_DIMENSIONS = [
    "useful_friction",
    "waste_friction",
    "channel_convergence",
    "interior_signal",
    "boundary_clarity",
    "continuity_preservation",
    "transformation_tolerance",
    "artificiality_penalty",
    "inspection_deepening",
    "inspection_collapse",
    "overall_response",
]

VALID_TEST_IDS = {
    "ont_001_friction",
    "ont_002_convergence",
    "ont_003_inspection",
    "ont_004_boundary",
    "ont_005_continuity",
    "ont_006_bridge",
}

VALID_STATES = {"REST", "THRESHOLD", "MIXED", "NONE"}


def load_items(path: Path, test_filter: str | None) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping line {i+1} — JSON parse error: {e}", file=sys.stderr)
                continue
            if test_filter and item.get("test_id") != test_filter:
                continue
            items.append(item)
    return items


def make_item_id(item: dict, index: int) -> str:
    """Generate a stable item identifier from the stimulus string."""
    stimulus = item.get("stimulus", "")
    slug = stimulus[:40].lower()
    slug = "".join(c if c.isalnum() else "_" for c in slug).strip("_")
    slug = "_".join(s for s in slug.split("_") if s)[:30]
    return f"{item.get('test_id', 'unknown')}_{index:03d}_{slug}"


def blank_scores(item: dict) -> dict:
    """Return blank score block. Copy predicted_scores as hints if present."""
    predicted = item.get("predicted_scores", {})
    scores = {}
    for dim in SCORE_DIMENSIONS:
        if dim in predicted:
            scores[dim] = f"__FILL__ (predicted: {predicted[dim]})"
        else:
            scores[dim] = "__FILL__"
    # overall_response is required — always include it
    if "overall_response" not in scores:
        scores["overall_response"] = "__FILL__"
    return scores


def make_score_record(item: dict, index: int, scorer: str, state: str, run_date: str) -> dict:
    return {
        "record_type": "score_record",
        "test_id": item.get("test_id", "unknown"),
        "item_id": make_item_id(item, index),
        "stimulus": item.get("stimulus", ""),
        "domain": item.get("domain", ""),
        "run_date": run_date,
        "scorer": scorer,
        "operator_state": state,
        "scores": blank_scores(item),
        "predicted_scores": item.get("predicted_scores", {}),
        "result": "__FILL__  # one of: confirmed / sharpening_required / anomaly / ambiguous",
        "notes": "",
        "falsification_evidence": "",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate blank scoring template from example_items.jsonl")
    parser.add_argument(
        "--filter",
        metavar="TEST_ID",
        help=f"Only include items for this test ID. Valid: {', '.join(sorted(VALID_TEST_IDS))}",
    )
    parser.add_argument(
        "--scorer",
        default="operator",
        help="Who is scoring. Default: operator",
    )
    parser.add_argument(
        "--state",
        default="NONE",
        choices=sorted(VALID_STATES),
        help="Operator state at time of scoring. Default: NONE",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Override output file path. Default: runs/scoring_YYYYMMDD.jsonl",
    )
    args = parser.parse_args()

    if args.filter and args.filter not in VALID_TEST_IDS:
        print(f"Error: unknown test_id '{args.filter}'. Valid: {', '.join(sorted(VALID_TEST_IDS))}", file=sys.stderr)
        sys.exit(1)

    if not INPUT_FILE.exists():
        print(f"Error: input file not found: {INPUT_FILE}", file=sys.stderr)
        sys.exit(1)

    items = load_items(INPUT_FILE, args.filter)
    if not items:
        print("No items found (check --filter value or input file).", file=sys.stderr)
        sys.exit(1)

    run_date = date.today().isoformat()

    if args.output:
        output_path = Path(args.output)
    else:
        RUNS_DIR.mkdir(exist_ok=True)
        suffix = f"_{args.filter}" if args.filter else ""
        output_path = RUNS_DIR / f"scoring_{run_date.replace('-', '')}{suffix}.jsonl"

    records = [
        make_score_record(item, i, args.scorer, args.state, run_date)
        for i, item in enumerate(items)
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Generated {len(records)} blank scoring records.")
    print(f"Output: {output_path}")
    print(f"Fill in 'scores' blocks and set 'result' for each item.")
    print(f"Replace __FILL__ values with integers 0-5.")


if __name__ == "__main__":
    main()

