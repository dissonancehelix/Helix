"""
Dota 2 Dark Seer — DCP Probe
core/probes/dota_ds_probe.py

Fetches dissonance's Dark Seer match history from OpenDota, extracts
per-match DCP trajectories, and compares combo matches (Vacuum + Wall)
against non-combo matches.

Usage:
    python -m applications.labs.dota_ds_probe

Account:
    dissonance / disidente
    Steam: STEAM_0:0:45789161
    OpenDota account_id: 91578322

Output:
    - Fetches up to 100 Dark Seer matches (cached to core/probes/.cache/dota/)
    - Extracts trajectories from parsed matches (version != None)
    - Splits into combo (Vacuum+Wall together) vs. no-combo groups
    - Prints DCP comparison table
    - Prints per-match summary
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

from domains.games.ingestion.opendota_client import (
    fetch_player_matches,
    fetch_and_cache,
    is_parsed,
)
from domains.games.ingestion.dota_dark_seer import extract_batch
from domains.games.analysis.dcp import extract_dcp_event

_ACCOUNT_ID   = 91578322      # dissonance
_DARK_SEER_ID = 55
_CACHE_DIR    = ROOT / "domains" / "games" / "data" / ".cache" / "dota"
_MATCH_LIMIT  = 100


def _fetch_matches() -> dict[int, dict]:
    print(f"Fetching Dark Seer match list (limit={_MATCH_LIMIT})...")
    matches = fetch_player_matches(
        _ACCOUNT_ID,
        hero_id=_DARK_SEER_ID,
        limit=_MATCH_LIMIT,
        significant=0,
    )
    match_ids = [m["match_id"] for m in matches]
    print(f"  {len(match_ids)} matches in history")

    print(f"\nFetching full match data (cached to {_CACHE_DIR.relative_to(ROOT)})...")
    all_data = fetch_and_cache(match_ids, _CACHE_DIR, verbose=True)

    parsed = {mid: d for mid, d in all_data.items() if is_parsed(d)}
    print(f"\n  {len(parsed)}/{len(all_data)} matches have parse data")
    return parsed


def _split_groups(logs):
    """Split TrajectoryLogs into combo vs. no-combo groups."""
    combo    = [l for l in logs if l.config.get("combo_step") is not None]
    no_combo = [l for l in logs if l.config.get("combo_step") is None]
    return combo, no_combo


def _group_stats(logs, label: str) -> dict:
    if not logs:
        return {"label": label, "n": 0}

    dcp_events  = [extract_dcp_event(l) for l in logs]
    qual_full   = sum(1 for l in logs if l.qualification_status == "FULL")
    collapses   = sum(1 for l in logs if l.collapse_step is not None)
    tensions    = [e.tension_proxy for e in dcp_events if e.tension_proxy is not None]
    dcp_scores  = [e.confidence for e in dcp_events]
    wins        = sum(1 for l in logs if l.config.get("win"))

    def _mean(xs):
        return round(sum(xs) / len(xs), 3) if xs else 0.0

    return {
        "label":         label,
        "n":             len(logs),
        "wins":          wins,
        "win_rate":      round(wins / len(logs), 2),
        "qual_full":     qual_full,
        "collapses":     collapses,
        "mean_tension":  _mean(tensions),
        "mean_dcp":      _mean(dcp_scores),
        "max_dcp":       round(max(dcp_scores), 3) if dcp_scores else 0.0,
    }


def _print_table(stats_list: list[dict]) -> None:
    header = (
        f"{'Group':<18} {'N':>4} {'W/L':>6} {'WR':>5} "
        f"{'FULL':>5} {'Collapse':>8} {'T̄':>6} {'DCP̄':>6} {'DCPmax':>7}"
    )
    sep = "-" * len(header)
    print(f"\n{sep}")
    print(header)
    print(sep)
    for s in stats_list:
        if s["n"] == 0:
            print(f"  {s['label']:<16} — no data")
            continue
        wl = f"{s['wins']}/{s['n'] - s['wins']}"
        print(
            f"  {s['label']:<16} {s['n']:>4} {wl:>6} {s['win_rate']:>5.0%} "
            f"{s['qual_full']:>5} {s['collapses']:>8} "
            f"{s['mean_tension']:>6.3f} {s['mean_dcp']:>6.3f} {s['max_dcp']:>7.3f}"
        )
    print(sep)


def _print_match_log(logs, label: str) -> None:
    if not logs:
        return
    print(f"\n{label} ({len(logs)} matches):")
    for l in sorted(logs, key=lambda x: x.config.get("match_id", 0)):
        cfg  = l.config
        ev   = extract_dcp_event(l)
        vac  = cfg.get("total_vacuum", 0)
        wall = cfg.get("total_wall", 0)
        win  = "W" if cfg.get("win") else "L"
        print(
            f"  {cfg['match_id']} {win}  "
            f"vac={vac} wall={wall}  "
            f"steps={len(l.events)}  "
            f"collapse={l.collapse_step}  "
            f"qual={l.qualification_status:<12}  "
            f"dcp={ev.confidence:.3f}"
        )


def main() -> None:
    parsed_data = _fetch_matches()

    print("\nExtracting Dark Seer trajectories...")
    logs = extract_batch(parsed_data, _ACCOUNT_ID, verbose=True)

    if not logs:
        print("\nNo usable trajectories extracted.")
        print("Most Dark Seer matches are not yet parsed by OpenDota.")
        print(
            "To request parsing: POST https://api.opendota.com/api/request/{match_id}\n"
            "Then re-run this probe after ~10 min."
        )
        return

    combo, no_combo = _split_groups(logs)

    print(f"\n{'='*60}")
    print("Dark Seer DCP Probe — dissonance / disidente")
    print(f"Parsed matches: {len(logs)}  |  Combo: {len(combo)}  |  No-combo: {len(no_combo)}")

    stats = [
        _group_stats(combo,    "Vacuum+Wall combo"),
        _group_stats(no_combo, "No combo"),
        _group_stats(logs,     "All DS matches"),
    ]
    _print_table(stats)

    _print_match_log(combo,    "Combo matches")
    _print_match_log(no_combo, "No-combo matches")

    # Interpretation
    if combo and no_combo:
        delta_dcp = stats[0]["mean_dcp"] - stats[1]["mean_dcp"]
        delta_wr  = stats[0]["win_rate"]  - stats[1]["win_rate"]
        print(f"\nDCP delta (combo vs no-combo): {delta_dcp:+.3f}")
        print(f"Win rate delta:                {delta_wr:+.0%}")
        if delta_dcp > 0.05:
            print("→ Combo fights show higher DCP score: spatial compression signal detected.")
        elif delta_dcp < -0.05:
            print("→ No-combo fights score higher: combo may not be the primary DCP driver here.")
        else:
            print("→ DCP scores comparable: insufficient separation with current sample.")


if __name__ == "__main__":
    main()
