"""
Games Domain — NFL Play-by-Play → TrajectoryLog
system/tools/games_pipeline/nfl_pbp_parser.py

Converts NFL play-by-play data (from nfl_data_py) into TrajectoryLogs.
Each drive = one TrajectoryLog; each play within a drive = one TrajectoryEvent.

TRAJECTORY STRUCTURE:
    Step i  = i-th play in the drive (sorted by order_sequence)
    possibility_breadth = wp (win probability from possession team's perspective)
                          For defensive drives: def_wp = 1 - opponent's wp
    constraint_proxy    = max(score_constraint, time_constraint)
                          score_constraint = max(0, min(1, -score_diff / 21))
                          time_constraint  = max(0, 1 - seconds_remaining / 3600)
    collapse_step       = index of the last play in the drive
    Morphology mapping from fixed_drive_result:
        'Touchdown'         → TRANSFORMATIVE
        'Field goal'        → CIRCULAR
        'Punt', 'Turnover', 'Turnover on downs',
        'End of half', 'End of game',
        'Opp touchdown'     → DISSOLUTIVE

LIMITATIONS:
    - wp is possession-team perspective; we use def_wp for defensive reads
    - score_differential sign convention: positive = posteam leading
    - Kickoffs, timeouts, PATs are filtered (play != 1 rows)
    - Drives with fewer than 2 qualifying plays are skipped
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

from model.domains.self.analysis.trajectory import (
    TrajectoryEvent, TrajectoryLog,
    EVENT_SCHEMA_VERSION, LOG_SCHEMA_VERSION,
)
from model.domains.self.analysis.probes import (
    estimate_tension,
    estimate_post_collapse_narrowing,
    compute_qualification_status,
)

_FIXTURE_ID   = "nfl_drive"
_FIXTURE_TYPE = "NFL Drive (nfl_data_py)"

# Morphology labels by drive result
_MORPHOLOGY_MAP: dict[str, str] = {
    "Touchdown":          "TRANSFORMATIVE",
    "Field goal":         "CIRCULAR",
    "Punt":               "DISSOLUTIVE",
    "Turnover":           "DISSOLUTIVE",
    "Turnover on downs":  "DISSOLUTIVE",
    "End of half":        "DISSOLUTIVE",
    "End of game":        "DISSOLUTIVE",
    "Opp touchdown":      "DISSOLUTIVE",
}

# Plays we skip (non-action rows)
_SKIP_PLAY_TYPES = {"kickoff", "extra_point", "no_play", "qb_kneel", "qb_spike"}


def _constraint_proxy(score_differential: float, game_seconds_remaining: float) -> float:
    """Compute constraint proxy from score and time pressure."""
    score_constraint = max(0.0, min(1.0, -score_differential / 21.0))
    time_constraint  = max(0.0, 1.0 - game_seconds_remaining / 3600.0)
    return max(score_constraint, time_constraint)


def _nan_to_none(val):
    """Convert NaN/None to None, otherwise return value."""
    if val is None:
        return None
    try:
        import math
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        pass
    return val


def _safe_float(val, default: float = 0.0) -> float:
    """Convert to float, returning default on NaN/None."""
    if val is None:
        return default
    try:
        import math
        f = float(val)
        return default if math.isnan(f) else f
    except (TypeError, ValueError):
        return default


def drive_to_trajectory(
    drive_plays: pd.DataFrame,
    game_id: str,
    drive_id: int,
    posteam: str,
    label: str = "",
) -> Optional[TrajectoryLog]:
    """
    Build a TrajectoryLog from a single drive's plays.

    Args:
        drive_plays:  rows for a single drive, sorted by order_sequence
        game_id:      NFL game identifier (e.g. '2024_08_CHI_WAS')
        drive_id:     drive number within the game
        posteam:      possession team abbreviation (e.g. 'WAS')
        label:        optional annotation (e.g. 'Hail Maryland')

    Returns:
        TrajectoryLog, or None if drive has fewer than 2 qualifying plays.
    """
    # Filter to actual plays
    qualifying = drive_plays[
        ~drive_plays["play_type"].isin(_SKIP_PLAY_TYPES) &
        (drive_plays["play"] == 1)
    ].copy()

    if len(qualifying) < 2:
        return None

    qualifying = qualifying.sort_values("order_sequence").reset_index(drop=True)

    # Determine final morphology from drive result
    drive_result = str(qualifying["fixed_drive_result"].iloc[-1]) if "fixed_drive_result" in qualifying.columns else ""
    morphology_str = _MORPHOLOGY_MAP.get(drive_result, "DISSOLUTIVE")

    # Build events
    events: list[TrajectoryEvent] = []
    breadth_series: list[float] = []

    for step, row in qualifying.iterrows():
        step_idx = len(events)

        # possibility_breadth = win probability from posteam perspective
        wp_val = _safe_float(_nan_to_none(row.get("wp")), default=0.5)
        breadth = max(0.0, min(1.0, wp_val))

        # constraint proxy
        score_diff = _safe_float(_nan_to_none(row.get("score_differential")), 0.0)
        time_rem   = _safe_float(_nan_to_none(row.get("game_seconds_remaining")), 1800.0)
        constraint = _constraint_proxy(score_diff, time_rem)

        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        # State summary
        desc_raw = str(row.get("desc", "") or "")
        state_summary = {
            "game_id":              game_id,
            "drive":                int(drive_id),
            "down":                 _nan_to_none(row.get("down")),
            "ydstogo":              _nan_to_none(row.get("ydstogo")),
            "yardline_100":         _nan_to_none(row.get("yardline_100")),
            "ep":                   _nan_to_none(row.get("ep")),
            "epa":                  _nan_to_none(row.get("epa")),
            "wp":                   round(wp_val, 4),
            "play_type":            str(row.get("play_type", "") or ""),
            "desc":                 desc_raw[:80],
            "sack":                 int(_safe_float(row.get("sack"), 0.0)),
            "qb_hit":               int(_safe_float(row.get("qb_hit"), 0.0)),
            "pass_touchdown":       int(_safe_float(row.get("pass_touchdown"), 0.0)),
            "rush_touchdown":       int(_safe_float(row.get("rush_touchdown"), 0.0)),
            "interception":         int(_safe_float(row.get("interception"), 0.0)),
            "fumble_lost":          int(_safe_float(row.get("fumble_lost"), 0.0)),
            "third_down_converted": int(_safe_float(row.get("third_down_converted"), 0.0)),
            "third_down_failed":    int(_safe_float(row.get("third_down_failed"), 0.0)),
            "constraint_class":     "external",
            "fixture":              _FIXTURE_ID,
        }

        events.append(TrajectoryEvent(
            step                = step_idx,
            possibility_breadth = round(breadth, 4),
            constraint_proxy    = round(constraint, 4),
            tension_proxy       = round(tension, 4),
            state_summary       = state_summary,
            notes               = label if (step_idx == 0 and label) else None,
            schema_version      = EVENT_SCHEMA_VERSION,
        ))

    if len(events) < 2:
        return None

    # Collapse step = index of last play (drive ends there)
    collapse_step = len(events) - 1

    # Mark collapse event
    e = events[collapse_step]
    e.collapse_flag       = True
    e.collapse_morphology = morphology_str

    post_narrowing = estimate_post_collapse_narrowing(breadth_series, collapse_step)
    e.post_collapse_narrowing = post_narrowing

    # Qualification status
    qualification = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = any(ev.constraint_proxy > 0 for ev in events),
        has_tension_proxy     = any(ev.tension_proxy > 0 for ev in events),
        has_collapse_proxy    = True,
        has_post_collapse     = (post_narrowing is not None),
    )

    # ── Drive-level aggregates ─────────────────────────────────────────────────
    epa_vals = [
        ev.state_summary["epa"] for ev in events
        if ev.state_summary.get("epa") is not None
    ]
    epa_vals_f = [float(v) for v in epa_vals]
    mean_epa   = sum(epa_vals_f) / len(epa_vals_f) if epa_vals_f else 0.0
    epa_var    = (
        sum((v - mean_epa) ** 2 for v in epa_vals_f) / len(epa_vals_f)
        if len(epa_vals_f) > 1 else 0.0
    )
    max_epa    = max(epa_vals_f) if epa_vals_f else 0.0
    n_third    = sum(1 for ev in events if ev.state_summary.get("down") == 3)
    n_third_conv = sum(ev.state_summary.get("third_down_converted", 0) for ev in events)
    n_qb_hits  = sum(ev.state_summary.get("qb_hit", 0) for ev in events)
    n_sacks    = sum(ev.state_summary.get("sack", 0) for ev in events)

    run_id = f"nfl_drive_{game_id}_d{drive_id}"

    return TrajectoryLog(
        fixture_id           = _FIXTURE_ID,
        fixture_type         = _FIXTURE_TYPE,
        run_id               = run_id,
        seed                 = hash(run_id) % (2**31),
        config               = {
            "game_id":        game_id,
            "drive_id":       drive_id,
            "posteam":        posteam,
            "n_plays":        len(events),
            "drive_result":   drive_result,
            "label":          label,
            # drive-level aggregates
            "mean_epa":       round(mean_epa, 4),
            "epa_variance":   round(epa_var, 4),
            "max_epa":        round(max_epa, 4),
            "n_third_downs":  n_third,
            "n_third_conv":   n_third_conv,
            "third_down_rate": round(n_third_conv / n_third, 3) if n_third else None,
            "n_qb_hits":      n_qb_hits,
            "n_sacks":        n_sacks,
        },
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = morphology_str,
        qualification_status = qualification,
        schema_version       = LOG_SCHEMA_VERSION,
    )


def season_drives(
    pbp_df: pd.DataFrame,
    team: str,
    offensive_only: bool = True,
) -> list[TrajectoryLog]:
    """
    Build one TrajectoryLog per drive for a given team across a full season.

    Args:
        pbp_df:         Full season play-by-play DataFrame from nfl_data_py
        team:           Team abbreviation (e.g. 'WAS')
        offensive_only: If True, only include drives where team is posteam.
                        If False, also include defensive drives (team is defteam).

    Returns:
        List of TrajectoryLogs, one per qualifying drive.
    """
    logs: list[TrajectoryLog] = []

    if offensive_only:
        team_plays = pbp_df[pbp_df["posteam"] == team].copy()
    else:
        team_plays = pbp_df[
            (pbp_df["posteam"] == team) | (pbp_df["defteam"] == team)
        ].copy()

    # Get unique (game_id, fixed_drive) combinations
    drive_keys = (
        team_plays[["game_id", "fixed_drive", "posteam"]]
        .drop_duplicates()
        .values
        .tolist()
    )

    for game_id, drive_id, posteam in drive_keys:
        drive_mask = (
            (pbp_df["game_id"] == game_id) &
            (pbp_df["fixed_drive"] == drive_id) &
            (pbp_df["posteam"] == posteam)
        )
        drive_plays = pbp_df[drive_mask].sort_values("order_sequence")

        log = drive_to_trajectory(
            drive_plays=drive_plays,
            game_id=str(game_id),
            drive_id=int(drive_id),
            posteam=str(posteam),
        )
        if log is not None:
            logs.append(log)

    return logs

