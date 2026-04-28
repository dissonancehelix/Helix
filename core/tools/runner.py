"""
Helix Games Domain — Phase 1: Platform Traces
Runner CLI for extracting operator behaviors from Steam and PSN.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from domains.games.tools.games_pipeline.platforms import (
    SteamClient, PSNClient, build_games_corpus
)

_ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="games_trace_ingest",
        description="Helix Games Domain Phase 1 Platform Ingestion"
    )
    
    parser.add_argument("--steam-id", type=str,
                        help="SteamID64 or vanity url string for extraction.")
    parser.add_argument("--psn-id", type=str,
                        help="PSN online ID for PSN extraction.")
    parser.add_argument("--psn-fallback", type=str,
                        help="Path to an offline Sony Data Request JSON if live PSN fails.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Connect, fetch and parse, but do not write output JSON")
    
    return parser


def _run_ingest(args: argparse.Namespace) -> int:
    """Orchestrates Games Domain metadata trace pulling."""
    run_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = _ARTIFACTS_DIR / run_id
    
    if not args.dry_run:
        run_dir.mkdir(parents=True, exist_ok=True)
        
    print(f"\n[games] Starting Games Domain Trace Extraction")
    print(f"[games] Run ID: {run_id}\n")
    
    run_log = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "args": vars(args),
        "source_success": {},
        "errors": []
    }
    
    records = []
    
    # ── 1. Steam Ingestion ──
    print("── Steam ──")
    steam = SteamClient()
    
    if args.steam_id:
        target_id = args.steam_id
        if not target_id.isdigit():
            print(f"[steam] Resolving vanity constraint '{target_id}'...")
            res = steam.resolve_vanity(target_id)
            if res:
                   target_id = res
        
        # Pull records
        s_acc = steam.get_summary(target_id)
        if s_acc:
             print(f"   [+] Profile Located: {s_acc.persona_name} (Visibility: {s_acc.visibility_state})")
             if s_acc.visibility_state != "private":
                 steam_games = steam.get_owned_games(target_id)
                 print(f"   [+] Extracted {len(steam_games)} trace records from Steam library.")
                 records.extend(steam_games)
                 run_log["source_success"]["steam"] = len(steam_games)
             else:
                 print("   [!] Privacy Blocked. Cannot fetch explicit library sizes.")
                 run_log["source_success"]["steam"] = "privacy_blocked"
        else:
             print("   [!] Could not locate explicit identity or authenticate correctly.")
             run_log["source_success"]["steam"] = "auth_failed_or_missing"
    else:
        print("   [i] Skipped (no --steam-id provided).")

    # ── 2. PSN Ingestion ──
    print("\n── PSN ──")
    psn = PSNClient()
    if args.psn_fallback:
        psn.set_fallback(Path(args.psn_fallback))
        
    if args.psn_id:
        p_acc = psn.get_summary(args.psn_id)
        if p_acc:
            print(f"   [+] Profile Located: {p_acc.persona_name}")
            psn_games = psn.get_owned_games(args.psn_id)
            print(f"   [+] Extracted {len(psn_games)} trace records from PSN registry.")
            records.extend(psn_games)
            run_log["source_success"]["psn"] = len(psn_games)
        else:
            if psn.fallback_file:
                psn_games = psn.get_owned_games("OFFLINE_EXPORT")
                print(f"   [+] Extracted {len(psn_games)} structural traces from fallback export.")
                records.extend(psn_games)
                run_log["source_success"]["psn_fallback"] = len(psn_games)
            else:
                print("   [!] Could not locate or authenticate PSNAWP profile.")
                run_log["source_success"]["psn"] = "auth_failed_or_missing"
    else:
        print("   [i] Skipped (no --psn-id provided).")


    # ── 3. Corpus Aggregation ──
    print("\n[games] ── AGGREGATING CORPOREAL ARTIFACTS ──")
    artifacts = build_games_corpus(records)
    run_log["outputs_written"] = []
    
    for key, data in artifacts.items():
        if not args.dry_run:
            ext = "jsonl" if "entities" in key else "json"
            out_file = run_dir / f"{key}.{ext}"
            
            if ext == "jsonl":
                 with open(out_file, "w", encoding="utf-8") as f:
                     for r in data:
                         f.write(json.dumps(r) + "\n")
            else:
                 with open(out_file, "w", encoding="utf-8") as f:
                     json.dump(data, f, indent=2)
                     
            run_log["outputs_written"].append(out_file.name)
        
        # Verbose prints
        if key == "games_platform_summary":
            print(f"   Generated Platform Trace Map across {data['total_records']} total identities.")
        elif key == "games_engagement_summary":
            print(f"   Generated Engagement Matrix aggregating {data.get('total_playtime_hours_tracked', 0):,} operator hours.")
    
    if not args.dry_run:
        # Write Log + Manifest
        mf_path = run_dir / "games_ingest_manifest.json"
        with open(mf_path, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": run_id, 
                "total_records": len(records),
                "auth_states": run_log["source_success"]
            }, f, indent=2)
            
        (run_dir / "run_log.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")
        _write_phase1_summary(run_dir, run_id, run_log, artifacts)
            
        print(f"\n[games] Trace Extraction Routine Complete!")
        print(f"   Artifacts safely stored to: {run_dir}")
        
    return 0


def _write_phase1_summary(run_dir: Path, run_id: str, run_log: dict, artifacts: dict) -> None:
    lines = [
        "# Helix Games Phase 1: Trace Ingestion Summary",
        f"Run ID: `{run_id}`",
        f"Generated: {run_log['timestamp']}",
        "",
        "---",
        "",
        "## Source Traces",
        "| Platform | Extracted Records |",
        "|----------|-------------------|"
    ]
    for p, c in run_log["source_success"].items():
        lines.append(f"| `{p}` | {c} |")
        
    lines += [
        "",
        "## Overall Action Classification",
        "| Edit Bucket | Count |",
        "|-------------|-------|"
    ]
    
    cls_dist = artifacts.get("games_classifications", {}).get("distribution", {})
    for bucket, count in cls_dist.items():
        lines.append(f"| `{bucket}` | {count:,} |")
        
    lines += [
        "",
        "## Output Artifacts",
        "| File | Purpose |",
        "|------|---------|",
        "| `games_ingest_manifest.json` | Master index of ingest run parameters and success state |",
        "| `games_normalized_entities.jsonl` | Helix normalized raw event schema map |",
        "| `games_platform_summary.json` | Ownership dispersion segregated by origin platform |",
        "| `games_engagement_summary.json` | High-density usage trace reporting metrics (hours tracking) |",
        "| `run_log.json` | Trace execution history details |"
    ]
    
    (run_dir / "games_phase1_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(_run_ingest(args))

if __name__ == "__main__":
    main()

