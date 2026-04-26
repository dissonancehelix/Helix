"""
Commanders EIP Probe
core/probes/commanders_eip_probe.py

Encodes the Washington Commanders stadium decision as an Epistemic Irreversibility
Point (EIP) timeline. EIP = a decision point after which some trajectories become
permanently unavailable.

Two TrajectoryLogs are built:
    1. Stadium trajectory: timeline of site-narrowing events
       possibility_breadth = n_viable_sites / 6.0
       constraint_proxy    = years since search / total years

    2. Harris acquisition chain: each major acquisition by Josh Harris
       possibility_breadth = 1 - (n_sports_teams / 4)
       constraint_proxy    = capital_committed_b / 7.0

The critical EIP event = Biden signing the RFK Stadium Revitalization Act
(2025-01-06 per Wikipedia; modeled here as the "eip_collapse" stage).

Sources: Josh_Harris_(businessman).pdf, New_Commanders_Stadium.pdf (Wikipedia)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

from domains.self.analysis.trajectory import (
    TrajectoryEvent, TrajectoryLog,
    EVENT_SCHEMA_VERSION, LOG_SCHEMA_VERSION,
)
from domains.self.analysis.probes import (
    estimate_tension,
    estimate_post_collapse_narrowing,
    compute_qualification_status,
)
from domains.games.analysis.dcp import extract_dcp_event

# ---------------------------------------------------------------------------
# Hardcoded timeline data
# (sourced from New_Commanders_Stadium.pdf + Josh_Harris_(businessman).pdf)
# ---------------------------------------------------------------------------

STADIUM_TIMELINE = [
    {
        "date": "2012-01-01",
        "event": "Commanders begin new stadium search",
        "stage": "search_open",
        "n_viable_sites": 6,
    },
    {
        "date": "2013-06-01",
        "event": "Oxon Cove Park (Maryland) rejected",
        "stage": "site_elimination",
        "n_viable_sites": 5,
    },
    {
        "date": "2015-01-01",
        "event": "Virginia sites (Sterling, Dumfries, Woodbridge) considered",
        "stage": "site_evaluation",
        "n_viable_sites": 4,
    },
    {
        "date": "2017-01-01",
        "event": "RFK site identified as primary desire",
        "stage": "site_preference",
        "n_viable_sites": 2,
    },
    {
        "date": "2019-01-01",
        "event": "RFK Stadium closes",
        "stage": "constraint_increasing",
        "n_viable_sites": 2,
    },
    {
        "date": "2021-01-01",
        "event": "Land transfer bill first proposed in Congress",
        "stage": "legislation_attempt",
        "n_viable_sites": 2,
    },
    {
        "date": "2022-06-01",
        "event": "FedExField lease extension signed (committed to Landover through 2027)",
        "stage": "lock_partial",
        "n_viable_sites": 2,
    },
    {
        "date": "2023-07-21",
        "event": "Josh Harris group purchases Commanders ($6.05B) — new ownership committed to DC return",
        "stage": "ownership_change",
        "n_viable_sites": 1,
    },
    {
        "date": "2024-02-28",
        "event": "House passes RFK Stadium site transfer bill",
        "stage": "legislation_passed",
        "n_viable_sites": 1,
    },
    {
        "date": "2025-01-06",
        "event": "Biden signs RFK Stadium Revitalization Act",
        "stage": "eip_collapse",
        "n_viable_sites": 1,
    },
    {
        "date": "2025-01-01",
        "event": "RFK Stadium deconstruction begins",
        "stage": "post_eip_committed",
        "n_viable_sites": 1,
    },
    {
        "date": "2026-01-01",
        "event": "New stadium groundbreaking (projected)",
        "stage": "construction_start",
        "n_viable_sites": 1,
    },
    {
        "date": "2030-01-01",
        "event": "Projected stadium opening",
        "stage": "completion",
        "n_viable_sites": 1,
    },
]

HARRIS_ACQUISITIONS = [
    {
        "date": "1990-01-01",
        "entity": "Apollo Global Management founded",
        "capital_committed_b": 0.0,
        "n_sports_teams": 0,
    },
    {
        "date": "2011-01-01",
        "entity": "Philadelphia 76ers (NBA)",
        "capital_committed_b": 0.28,
        "n_sports_teams": 1,
    },
    {
        "date": "2013-01-01",
        "entity": "New Jersey Devils (NHL)",
        "capital_committed_b": 0.56,
        "n_sports_teams": 2,
    },
    {
        "date": "2015-01-01",
        "entity": "Crystal Palace (EPL, minority stake)",
        "capital_committed_b": 0.63,
        "n_sports_teams": 3,
    },
    {
        "date": "2022-01-01",
        "entity": "Left Apollo, formed 26North",
        "capital_committed_b": 0.63,
        "n_sports_teams": 3,
    },
    {
        "date": "2023-07-21",
        "entity": "Washington Commanders (NFL)",
        "capital_committed_b": 6.68,
        "n_sports_teams": 4,
    },
]

_MAX_SITES = 6
_MAX_TEAMS = 4
_MAX_CAPITAL_B = 7.0
_SEARCH_START = datetime(2012, 1, 1)
_SEARCH_END   = datetime(2030, 1, 1)
_TOTAL_YEARS  = (_SEARCH_END - _SEARCH_START).days / 365.25

_HARRIS_START = datetime(1990, 1, 1)
_HARRIS_END   = datetime(2023, 7, 21)
_HARRIS_TOTAL_YEARS = (_HARRIS_END - _HARRIS_START).days / 365.25


def _years_since(start: datetime, current: datetime) -> float:
    return max(0.0, (current - start).days / 365.25)


def build_stadium_trajectory() -> TrajectoryLog:
    """
    Build a TrajectoryLog for the stadium site-selection timeline.

    possibility_breadth = n_viable_sites / 6.0  (normalized)
    constraint_proxy    = years since search / total years to projected open
    EIP collapse at Biden bill signing (stage='eip_collapse')
    """
    events: list[TrajectoryEvent] = []
    breadth_series: list[float]    = []
    collapse_step: Optional[int]   = None

    for step, entry in enumerate(STADIUM_TIMELINE):
        dt = datetime.strptime(entry["date"], "%Y-%m-%d")

        breadth    = max(0.0, min(1.0, entry["n_viable_sites"] / _MAX_SITES))
        years_in   = _years_since(_SEARCH_START, dt)
        constraint = max(0.0, min(1.0, years_in / _TOTAL_YEARS))

        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        is_collapse = (entry["stage"] == "eip_collapse")
        if is_collapse:
            collapse_step = step

        morphology_str: Optional[str] = None
        if is_collapse:
            morphology_str = "TRANSFORMATIVE"  # irreversible lock-in to new coherent structure

        events.append(TrajectoryEvent(
            step                = step,
            possibility_breadth = round(breadth, 4),
            constraint_proxy    = round(constraint, 4),
            tension_proxy       = round(tension, 4),
            state_summary       = {
                "date":           entry["date"],
                "event":          entry["event"],
                "stage":          entry["stage"],
                "n_viable_sites": entry["n_viable_sites"],
                "constraint_class": "mixed",
                "fixture":        "eip_stadium",
            },
            collapse_flag       = is_collapse,
            collapse_morphology = morphology_str,
            schema_version      = EVENT_SCHEMA_VERSION,
        ))

    # Post-collapse narrowing
    if collapse_step is not None:
        pcn = estimate_post_collapse_narrowing(breadth_series, collapse_step)
        events[collapse_step].post_collapse_narrowing = pcn

    qualification = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = True,
        has_tension_proxy     = any(e.tension_proxy > 0 for e in events),
        has_collapse_proxy    = collapse_step is not None,
        has_post_collapse     = (collapse_step is not None and
                                 events[collapse_step].post_collapse_narrowing is not None),
    )

    return TrajectoryLog(
        fixture_id           = "eip_stadium",
        fixture_type         = "EIP Timeline — New Commanders Stadium",
        run_id               = "eip_stadium_rfk_2012_2030",
        seed                 = 2024,
        config               = {
            "source":       "New_Commanders_Stadium.pdf (Wikipedia)",
            "search_start": "2012-01-01",
            "eip_event":    "Biden signs RFK Stadium Revitalization Act",
            "eip_date":     "2025-01-06",
            "n_steps":      len(events),
        },
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = "TRANSFORMATIVE",
        qualification_status = qualification,
        schema_version       = LOG_SCHEMA_VERSION,
    )


def build_harris_trajectory() -> TrajectoryLog:
    """
    Build a TrajectoryLog for Josh Harris's sports acquisition chain.

    possibility_breadth = 1 - (n_sports_teams / 4)
    constraint_proxy    = capital_committed_b / 7.0
    Collapse = Commanders acquisition (full capital commitment, 4/4 teams)
    """
    events: list[TrajectoryEvent] = []
    breadth_series: list[float]    = []
    collapse_step: Optional[int]   = None

    for step, entry in enumerate(HARRIS_ACQUISITIONS):
        dt = datetime.strptime(entry["date"], "%Y-%m-%d")

        breadth    = max(0.0, min(1.0, 1.0 - (entry["n_sports_teams"] / _MAX_TEAMS)))
        constraint = max(0.0, min(1.0, entry["capital_committed_b"] / _MAX_CAPITAL_B))

        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        # Collapse = Commanders acquisition (final, largest, full commitment)
        is_collapse = (entry["entity"] == "Washington Commanders (NFL)")
        if is_collapse:
            collapse_step = step

        morphology_str: Optional[str] = None
        if is_collapse:
            morphology_str = "TRANSFORMATIVE"

        events.append(TrajectoryEvent(
            step                = step,
            possibility_breadth = round(breadth, 4),
            constraint_proxy    = round(constraint, 4),
            tension_proxy       = round(tension, 4),
            state_summary       = {
                "date":               entry["date"],
                "entity":             entry["entity"],
                "capital_committed_b": entry["capital_committed_b"],
                "n_sports_teams":     entry["n_sports_teams"],
                "constraint_class":   "internal",
                "fixture":            "eip_harris_acquisitions",
            },
            collapse_flag       = is_collapse,
            collapse_morphology = morphology_str,
            schema_version      = EVENT_SCHEMA_VERSION,
        ))

    if collapse_step is not None:
        pcn = estimate_post_collapse_narrowing(breadth_series, collapse_step)
        events[collapse_step].post_collapse_narrowing = pcn

    qualification = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = True,
        has_tension_proxy     = any(e.tension_proxy > 0 for e in events),
        has_collapse_proxy    = collapse_step is not None,
        has_post_collapse     = (collapse_step is not None and
                                 events[collapse_step].post_collapse_narrowing is not None),
    )

    return TrajectoryLog(
        fixture_id           = "eip_harris_acquisitions",
        fixture_type         = "EIP Timeline — Josh Harris Sports Acquisitions",
        run_id               = "eip_harris_1990_2023",
        seed                 = 2023,
        config               = {
            "source":     "Josh_Harris_(businessman).pdf (Wikipedia)",
            "start":      "1990-01-01",
            "end":        "2023-07-21",
            "n_steps":    len(events),
        },
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = "TRANSFORMATIVE",
        qualification_status = qualification,
        schema_version       = LOG_SCHEMA_VERSION,
    )


def print_trajectory(log: TrajectoryLog, title: str) -> None:
    """Print a TrajectoryLog in a human-readable format."""
    print(f"\n{'='*70}")
    print(f"=== {title} ===")
    print(f"{'='*70}")
    print(f"  fixture_id:  {log.fixture_id}")
    print(f"  run_id:      {log.run_id}")
    print(f"  n_steps:     {len(log.events)}")
    print(f"  collapse_at: step {log.collapse_step}")
    print(f"  morphology:  {log.final_morphology}")
    print(f"  qual_status: {log.qualification_status}")

    print()
    print(f"  {'Step':<5} {'Date':<12} {'breadth':>8} {'constraint':>11} {'tension':>8} {'collapse':>9}  Description")
    print(f"  {'-'*5} {'-'*12} {'-'*8} {'-'*11} {'-'*8} {'-'*9}  {'-'*40}")

    for e in log.events:
        ss   = e.state_summary
        date = ss.get("date", "?")
        desc = ss.get("event") or ss.get("entity") or ""
        collapse_flag = " <<< EIP" if e.collapse_flag else ""
        print(
            f"  {e.step:<5} {date:<12} {e.possibility_breadth:>8.4f} "
            f"{e.constraint_proxy:>11.4f} {e.tension_proxy:>8.4f} "
            f"{str(e.collapse_flag):>9}{collapse_flag}  {desc[:50]}"
        )


def print_dcp(dcp, title: str) -> None:
    """Print DCPEvent summary."""
    print(f"\n--- DCP Event: {title} ---")
    print(f"  possibility_space: {dcp.possibility_space_proxy}")
    print(f"  constraint:        {dcp.constraint_proxy}")
    print(f"  tension:           {dcp.tension_proxy}")
    print(f"  collapse:          {dcp.collapse_proxy}")
    print(f"  post_narrowing:    {dcp.post_collapse_narrowing}")
    print(f"  morphology:        {dcp.collapse_morphology}")
    print(f"  constraint_class:  {dcp.constraint_class}")
    print(f"  confidence:        {dcp.confidence}")
    print(f"  qualification:     {dcp.qualification_status()}")
    print(f"  dcp_composite:     {dcp.domain_metadata.get('dcp_composite', 0.0):.4f}")


def main() -> None:
    print("Building Stadium Timeline TrajectoryLog...")
    stadium_log = build_stadium_trajectory()
    stadium_dcp = extract_dcp_event(stadium_log)

    print("Building Harris Acquisition Chain TrajectoryLog...")
    harris_log  = build_harris_trajectory()
    harris_dcp  = extract_dcp_event(harris_log)

    print_trajectory(stadium_log, "STADIUM SITE SELECTION — EIP TIMELINE")
    print_dcp(stadium_dcp, "Stadium EIP")

    print_trajectory(harris_log, "JOSH HARRIS SPORTS ACQUISITIONS")
    print_dcp(harris_dcp, "Harris Acquisition Chain")

    print("\n\n=== CROSS-TRAJECTORY COMPARISON ===")
    print(f"  {'Trajectory':<40} {'DCP Score':>10} {'Qual Status':<15} {'Collapse Step':>14}")
    print(f"  {'-'*40} {'-'*10} {'-'*15} {'-'*14}")
    for log, dcp, name in [
        (stadium_log, stadium_dcp, "Stadium Site Selection"),
        (harris_log,  harris_dcp,  "Harris Acquisition Chain"),
    ]:
        score = dcp.domain_metadata.get("dcp_composite", 0.0)
        print(
            f"  {name:<40} {score:>10.4f} {dcp.qualification_status():<15} "
            f"{str(log.collapse_step):>14}"
        )

    print("\nKey observation:")
    print("  Stadium trajectory: site space collapses from 6→1 viable sites over 13 years.")
    print("  The EIP (Biden bill signing) makes the RFK site legally irreversible.")
    print("  Harris trajectory: capital commitment jumps 10x at Commanders acquisition,")
    print("  collapsing remaining portfolio optionality (4/4 target sports teams reached).")
    print("  Both are TRANSFORMATIVE collapses: new coherent structure post-EIP.")


if __name__ == "__main__":
    main()
