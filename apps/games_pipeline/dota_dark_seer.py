"""
Games Domain — Dark Seer Match → TrajectoryLog
domains/games/ingestion/dota_dark_seer.py

Converts an OpenDota parsed match (Dark Seer) into a TrajectoryLog
for DCP analysis. Each teamfight is one trajectory step.

WHY TEAMFIGHTS AS STEPS:
    The DCP event of interest is spatial compression via Vacuum + Wall of Replica.
    Teamfights are the natural unit — they define the windows where enemies have
    the option to spread, escape, or commit. Dark Seer's combo compresses that
    option set to a single point, then locks it.

    A per-minute gold-advantage trajectory could also be used for macro DCP
    (tension accumulation → team-fight pivots → game over), but that requires
    significantly more context about the match state. Teamfight trajectory is
    the direct signal: we can see exactly when Vacuum/Wall fired and what happened.

TRAJECTORY STRUCTURE:
    Step i = i-th teamfight in the match (chronological)
    possibility_breadth  = enemy survivors / 5
                           (fraction of enemy team NOT killed in this fight)
    constraint_proxy     = normalized Vacuum uses in this fight
                           (0.0 = no vacuum; 1.0 = at least one vacuum used)
    tension_proxy        = cumulative constraint buildup (running avg before collapse)
    collapse_flag        = True when Vacuum + Wall both used in same fight
    post_collapse        = mean enemy deaths per fight after collapse

ENEMY TEAM INDEXING:
    In the 10-player teamfight.players array:
        Radiant: indices 0-4  (player_slot 0-4)
        Dire:    indices 5-9  (player_slot 128-132)
    If Dark Seer is Dire (typical), enemies are indices 0-4.
    If Dark Seer is Radiant, enemies are indices 5-9.

LIMITATIONS:
    - Spatial positions not available from API (would need replay file)
    - Enemy action counts per second not available
    - Some matches are unscored (no ability_uses) — these are excluded
    - Teamfight player array ordering assumes standard OpenDota slot mapping
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

from domains.self.analysis.trajectory import (
    TrajectoryEvent, TrajectoryLog, make_run_id,
    EVENT_SCHEMA_VERSION, LOG_SCHEMA_VERSION,
)
from domains.self.analysis.probes import (
    estimate_tension,
    detect_collapse,
    estimate_post_collapse_narrowing,
    compute_qualification_status,
)
from domains.self.analysis.morphology_classifier import classify_morphology

_DARK_SEER_HERO_ID = 55
_VACUUM_KEY        = "dark_seer_vacuum"
_WALL_KEY          = "dark_seer_wall_of_replica"
_FIXTURE_ID        = "games_dota_dark_seer"


def _enemy_indices(is_radiant: bool) -> range:
    """Return the teamfight.players indices for the enemy team."""
    if is_radiant:
        return range(5, 10)   # Dark Seer is Radiant → enemies are Dire (5-9)
    return range(0, 5)        # Dark Seer is Dire → enemies are Radiant (0-4)


def extract_trajectory(
    match_data: dict,
    account_id: int,
    collapse_threshold: float = 0.30,
) -> Optional[TrajectoryLog]:
    """
    Build a TrajectoryLog from a parsed Dark Seer match.

    Returns None if:
        - account_id not found in match
        - hero is not Dark Seer
        - match has no teamfight data (unscored)
        - fewer than 2 teamfights (insufficient temporal resolution)

    Args:
        match_data:         Full match dict from OpenDota /matches/{id}
        account_id:         32-bit OpenDota account ID for the Dark Seer player
        collapse_threshold: Breadth fraction below which collapse fires (default 0.30)

    Returns:
        TrajectoryLog using the cognition domain schema, with games-specific
        state_summary fields. Compatible with games.analysis.dcp.extract_dcp_event().
    """
    # ── Locate player ─────────────────────────────────────────────────────────
    player = None
    for p in match_data.get("players", []):
        if p.get("account_id") == account_id:
            player = p
            break
    if player is None:
        return None

    if player.get("hero_id") != _DARK_SEER_HERO_ID:
        return None

    # ── Match metadata ────────────────────────────────────────────────────────
    player_slot  = player["player_slot"]
    radiant      = player_slot < 128
    radiant_win  = match_data.get("radiant_win", False)
    win          = (radiant_win and radiant) or (not radiant_win and not radiant)
    duration_s   = match_data.get("duration", 0)
    match_id     = match_data["match_id"]

    # ── Teamfights ────────────────────────────────────────────────────────────
    teamfights = match_data.get("teamfights", [])
    if not teamfights or len(teamfights) < 2:
        return None

    total_vacuum = (player.get("ability_uses") or {}).get(_VACUUM_KEY, 0)
    total_wall   = (player.get("ability_uses") or {}).get(_WALL_KEY, 0)
    enemy_idx    = _enemy_indices(radiant)

    # ── Build per-step events ─────────────────────────────────────────────────
    events:        list[TrajectoryEvent] = []
    breadth_series: list[float]          = []

    for step, tf in enumerate(teamfights):
        tf_players = tf.get("players", [])
        if not tf_players:
            continue

        # Count enemy deaths in this fight
        enemy_deaths = sum(
            tf_players[i].get("deaths", 0)
            for i in enemy_idx
            if i < len(tf_players)
        )
        enemy_deaths = min(enemy_deaths, 5)    # cap at full team wipe

        # Check Dark Seer ability usage in this fight
        ds_player_idx = 5 + (player_slot - 128) if not radiant else player_slot
        ds_tf = tf_players[ds_player_idx] if ds_player_idx < len(tf_players) else {}
        tf_abilities = ds_tf.get("ability_uses", {}) or {}
        vacuum_used  = tf_abilities.get(_VACUUM_KEY, 0)
        wall_used    = tf_abilities.get(_WALL_KEY, 0)

        # possibility_breadth = fraction of enemy team not killed
        # 1.0 = enemy survived intact; 0.0 = full enemy team wiped
        breadth = max(0.0, (5 - enemy_deaths) / 5.0)

        # constraint_proxy = 1.0 if vacuum used, 0.0 otherwise
        # (vacuum is the compression mechanism — pulling enemies to a point)
        constraint = 1.0 if vacuum_used > 0 else 0.0

        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        events.append(TrajectoryEvent(
            step                = step,
            possibility_breadth = round(breadth, 4),
            constraint_proxy    = round(constraint, 4),
            tension_proxy       = round(tension, 4),
            state_summary={
                "match_id":        match_id,
                "fight_start_s":   tf.get("start", 0),
                "fight_end_s":     tf.get("end", 0),
                "fight_deaths":    tf.get("deaths", 0),
                "enemy_deaths":    enemy_deaths,
                "vacuum_used":     vacuum_used,
                "wall_used":       wall_used,
                "combo":           bool(vacuum_used and wall_used),
                "constraint_class": "external",
                "fixture":         _FIXTURE_ID,
            },
            schema_version=EVENT_SCHEMA_VERSION,
        ))

    if len(events) < 2:
        return None

    # ── Collapse detection ────────────────────────────────────────────────────
    # Primary: first teamfight where Vacuum + Wall both used
    combo_step = next(
        (i for i, e in enumerate(events)
         if e.state_summary.get("combo")),
        None,
    )
    # Fallback: breadth-threshold detection (standard probe)
    probe_collapse = detect_collapse(breadth_series, threshold=collapse_threshold)

    # Use combo step if detected; breadth-based detection as fallback
    collapse_step = combo_step if combo_step is not None else probe_collapse

    post_narrowing = estimate_post_collapse_narrowing(breadth_series, collapse_step)
    morphology     = classify_morphology(breadth_series, collapse_step, initial_breadth=1.0)

    if collapse_step is not None:
        e = events[collapse_step]
        e.collapse_flag           = True
        e.collapse_morphology     = morphology.value
        e.post_collapse_narrowing = post_narrowing

    # ── Qualification ─────────────────────────────────────────────────────────
    qualification = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = any(e.constraint_proxy > 0 for e in events),
        has_tension_proxy     = any(e.tension_proxy > 0 for e in events),
        has_collapse_proxy    = (collapse_step is not None),
        has_post_collapse     = (post_narrowing is not None),
    )

    return TrajectoryLog(
        fixture_id           = _FIXTURE_ID,
        fixture_type         = "Dota 2 Dark Seer Match (OpenDota)",
        run_id               = make_run_id(_FIXTURE_ID, int(match_id % 2**31)),
        seed                 = int(match_id % 2**31),
        config               = {
            "account_id":          account_id,
            "match_id":            match_id,
            "hero_id":             _DARK_SEER_HERO_ID,
            "hero":                "Dark Seer",
            "win":                 win,
            "duration_s":          duration_s,
            "player_slot":         player_slot,
            "total_vacuum":        total_vacuum,
            "total_wall":          total_wall,
            "combo_step":          combo_step,
            "collapse_threshold":  collapse_threshold,
        },
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = morphology.value,
        qualification_status = qualification,
        schema_version       = LOG_SCHEMA_VERSION,
    )


def extract_batch(
    match_data_dict: dict[int, dict],
    account_id: int,
    collapse_threshold: float = 0.30,
    verbose: bool = True,
) -> list[TrajectoryLog]:
    """
    Extract TrajectoryLogs from a dict of match_id → match_data.
    Silently skips unscored or ineligible matches.
    """
    logs = []
    for match_id, data in match_data_dict.items():
        log = extract_trajectory(data, account_id, collapse_threshold)
        if log is not None:
            logs.append(log)
            if verbose:
                cfg = log.config
                print(
                    f"  [{match_id}] win={cfg['win']} vac={cfg['total_vacuum']} "
                    f"wall={cfg['total_wall']} combo={cfg['combo_step'] is not None} "
                    f"collapse_step={log.collapse_step} qual={log.qualification_status}"
                )
        else:
            if verbose:
                print(f"  [{match_id}] skipped (unscored or <2 teamfights)")
    return logs
