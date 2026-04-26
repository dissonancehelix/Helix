"""
nfl_commanders_2024.py — 2024 Washington Commanders DCP Analysis
================================================================
Combined analysis of the 2024 Washington Commanders season through the
Helix DCP lens. Two sections sharing a single data load.

Part 1 — Team-Level Drive Analysis (from nfl_commanders_probe.py)
    Loads 2024 Washington Commanders play-by-play, builds per-drive
    TrajectoryLogs, runs extract_dcp_event() on each drive, and prints:
    - Hail Maryland (game_id='2024_08_CHI_WAS', drive 23) step-by-step log
    - Top 10 highest-DCP drives
    - Season arc: per-week mean DCP and win probability
    - Playoff arc: each playoff game's drives summarized
    - Situational EPA splits (DVOA proxy) by constraint bucket
    - Third-down tension resolution vs. accumulation per week
    - DCP vs. EPA divergence analysis

Part 2 — Jayden Daniels Deep Dive (from daniels_2024_probe.py)
    Detailed structural analysis of Jayden Daniels's 2024 rookie season:
    - Per-game box score log
    - Scramble signature (anti-DCP profile: pocket → escape → new space)
    - Constraint performance splits (clutch, red zone, third down, etc.)
    - NGS arc: weekly TTT, aggressiveness, CPAE, air yards
    - Play ceiling and floor (top/bottom EPA plays)
    - Comeback / game-winning drives
    - Season compression arc (weekly EPA trajectory)
    - Season as DCP macro-trajectory (each game = one TrajectoryEvent)

Core DCP framing for a dual-threat QB:
    Pass play:   pocket constrains options → throw or get sacked → outcome collapses
    Scramble:    pocket collapses → Daniels CREATES new possibility space by moving
                 → anti-DCP move: reverses a compression event instead of accepting it

Usage:
    python domains/games/probes/nfl_commanders_2024.py           # all sections
    python domains/games/probes/nfl_commanders_2024.py --section team
    python domains/games/probes/nfl_commanders_2024.py --section daniels
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

import nfl_data_py as nfl
import pandas as pd

from domains.games.ingestion.nfl_pbp_parser import drive_to_trajectory, season_drives
from domains.games.analysis.dcp import extract_dcp_event
from domains.self.analysis.trajectory import TrajectoryLog
from core.invariants.dcp.event import DCPEvent

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SEASON                = 2024
TEAM                  = "WAS"
QB                    = "J.Daniels"
HAIL_MARYLAND_GAME_ID = "2024_08_CHI_WAS"
HAIL_MARYLAND_DRIVE   = 23

# Games where Daniels missed / Mariota started — exclude from Daniels-specific analysis
_MARIOTA_WEEKS = {7, 18}

# ---------------------------------------------------------------------------
# Columns to load (superset of both probes — union with no duplicates)
# ---------------------------------------------------------------------------
COLS = [
    'game_id', 'posteam', 'defteam', 'season_type', 'week', 'play_type',
    'down', 'ydstogo', 'yardline_100', 'score_differential',
    'game_seconds_remaining', 'ep', 'epa', 'desc', 'game_date', 'drive',
    'td_team', 'touchdown', 'pass_touchdown', 'rush_touchdown',
    'field_goal_result', 'fumble_lost', 'interception', 'sack', 'qb_hit',
    'passer_player_name', 'receiver_player_name', 'rusher_player_name',
    'wp', 'def_wp', 'fixed_drive', 'fixed_drive_result', 'order_sequence',
    'play', 'first_down', 'yards_gained', 'cpoe',
    'third_down_converted', 'third_down_failed',
    'rushing_yards', 'passing_yards', 'qb_scramble',
    'air_yards', 'complete_pass', 'incomplete_pass',
    'qb_dropback', 'pass_attempt', 'rush_attempt',
    'home_team', 'away_team', 'result', 'away_score', 'home_score',
]


# =============================================================================
# Shared helpers
# =============================================================================

def _sf(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        import math
        f = float(val)
        return default if math.isnan(f) else f
    except (TypeError, ValueError):
        return default


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _sep(n=80):
    print("=" * n)


# =============================================================================
# Shared data load
# =============================================================================

def load_pbp() -> pd.DataFrame:
    """Load 2024 season play-by-play, both regular and postseason."""
    print(f"Loading {SEASON} play-by-play data via nfl_data_py...")
    pbp = nfl.import_pbp_data(years=[SEASON], columns=COLS, downcast=True, cache=False)
    print(f"  Loaded {len(pbp):,} rows, {pbp['game_id'].nunique()} games.")
    return pbp


# =============================================================================
# PART 1: TEAM-LEVEL DRIVE ANALYSIS
# =============================================================================

def build_was_drives(pbp: pd.DataFrame) -> list[tuple[TrajectoryLog, DCPEvent]]:
    """Build (TrajectoryLog, DCPEvent) pairs for all WAS offensive drives."""
    print(f"\nBuilding WAS offensive drive trajectories...")
    logs = season_drives(pbp, team=TEAM, offensive_only=True)
    print(f"  {len(logs)} qualifying drives found.")

    pairs = []
    for log in logs:
        dcp = extract_dcp_event(log)
        pairs.append((log, dcp))
    return pairs


def annotate_hail_maryland(pairs: list[tuple[TrajectoryLog, DCPEvent]], pbp: pd.DataFrame) -> None:
    """Print full step-by-step detail for the Hail Maryland drive."""
    print(f"\n{'='*70}")
    print(f"=== HAIL MARYLAND ({HAIL_MARYLAND_GAME_ID}, Drive {HAIL_MARYLAND_DRIVE}) ===")
    print(f"{'='*70}")

    hm_log: Optional[TrajectoryLog] = None
    hm_dcp: Optional[DCPEvent] = None
    for log, dcp in pairs:
        cfg = log.config
        if cfg["game_id"] == HAIL_MARYLAND_GAME_ID and cfg["drive_id"] == HAIL_MARYLAND_DRIVE:
            hm_log = log
            hm_dcp = dcp
            break

    if hm_log is None:
        print("  Drive not found in season_drives output — attempting direct extraction...")
        mask = (
            (pbp["game_id"] == HAIL_MARYLAND_GAME_ID) &
            (pbp["fixed_drive"] == HAIL_MARYLAND_DRIVE) &
            (pbp["posteam"] == TEAM)
        )
        drive_plays = pbp[mask].sort_values("order_sequence")
        if len(drive_plays) == 0:
            mask2 = (
                (pbp["game_id"] == HAIL_MARYLAND_GAME_ID) &
                (pbp["drive"] == HAIL_MARYLAND_DRIVE) &
                (pbp["posteam"] == TEAM)
            )
            drive_plays = pbp[mask2].sort_values("order_sequence")

        if len(drive_plays) == 0:
            print("  Could not find Hail Maryland drive plays. Available WAS drives in that game:")
            game_was = pbp[(pbp["game_id"] == HAIL_MARYLAND_GAME_ID) & (pbp["posteam"] == TEAM)]
            print(f"  fixed_drive values: {sorted(game_was['fixed_drive'].unique())}")
            print(f"  drive values: {sorted(game_was['drive'].unique())}")
            return

        hm_log = drive_to_trajectory(
            drive_plays=drive_plays,
            game_id=HAIL_MARYLAND_GAME_ID,
            drive_id=HAIL_MARYLAND_DRIVE,
            posteam=TEAM,
            label="Hail Maryland",
        )
        if hm_log is None:
            print("  Could not build TrajectoryLog from drive plays (< 2 qualifying plays).")
            return
        hm_dcp = extract_dcp_event(hm_log)

    for i, event in enumerate(hm_log.events):
        ss = event.state_summary
        down = ss.get("down")
        ytg  = ss.get("ydstogo")
        yl   = ss.get("yardline_100")
        wp   = ss.get("wp", event.possibility_breadth)
        desc = ss.get("desc", "")

        down_str = f"{int(down)}st" if down == 1 else (
                   f"{int(down)}nd" if down == 2 else (
                   f"{int(down)}rd" if down == 3 else
                   f"{int(down)}th" if down else "?"))
        ytg_str  = f"{int(ytg)}" if ytg is not None else "?"
        yl_str   = f"{int(yl)}" if yl is not None else "?"
        flags = []
        if ss.get("pass_touchdown"): flags.append("TOUCHDOWN")
        if ss.get("rush_touchdown"): flags.append("RUSH TD")
        if ss.get("sack"):          flags.append("SACK")
        if ss.get("interception"):  flags.append("INT")
        if ss.get("fumble_lost"):   flags.append("FUMBLE")
        flag_str = " | " + " ".join(flags) if flags else ""

        print(
            f"  Play {i+1}: {down_str} & {ytg_str} from own {yl_str} | "
            f"wp={wp:.3f} | breadth={event.possibility_breadth:.3f} | "
            f"constraint={event.constraint_proxy:.3f}{flag_str}"
        )
        if desc:
            print(f"         {desc}")

    print(f"\n  → collapse_step={hm_log.collapse_step} | {hm_log.final_morphology} | "
          f"DCP={hm_dcp.domain_metadata.get('dcp_composite', 0.0):.3f} | "
          f"qualification={hm_dcp.qualification_status()}")


def print_season_stats(pairs: list[tuple[TrajectoryLog, DCPEvent]]) -> None:
    """Print drive result type summary table."""
    print(f"\n{'='*70}")
    print("=== SEASON DRIVE STATS BY RESULT TYPE ===")
    print(f"{'='*70}")

    result_groups: dict[str, list[float]] = defaultdict(list)

    for log, dcp in pairs:
        result = log.config.get("drive_result", "Unknown")
        score  = dcp.domain_metadata.get("dcp_composite", 0.0)
        result_groups[result].append(score)

    rows = []
    for result, scores in sorted(result_groups.items()):
        rows.append({
            "Drive Result":  result,
            "Count":         len(scores),
            "Mean DCP":      round(sum(scores) / len(scores), 3),
            "Max DCP":       round(max(scores), 3),
        })
    rows.sort(key=lambda r: r["Mean DCP"], reverse=True)

    print(f"  {'Drive Result':<22} {'Count':>6} {'Mean DCP':>10} {'Max DCP':>10}")
    print(f"  {'-'*22} {'-'*6} {'-'*10} {'-'*10}")
    for row in rows:
        print(f"  {row['Drive Result']:<22} {row['Count']:>6} {row['Mean DCP']:>10.3f} {row['Max DCP']:>10.3f}")


def print_top_drives(pairs: list[tuple[TrajectoryLog, DCPEvent]], n: int = 10) -> None:
    """Print top N highest-DCP drives."""
    print(f"\n{'='*70}")
    print(f"=== TOP {n} HIGHEST-DCP WAS DRIVES ===")
    print(f"{'='*70}")

    scored = []
    for log, dcp in pairs:
        score = dcp.domain_metadata.get("dcp_composite", 0.0)
        scored.append((score, log, dcp))
    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"  {'Rank':<5} {'Game ID':<22} {'Drive':>6} {'Result':<22} {'DCP':>7} {'Morph':<18} {'Plays':>6}")
    print(f"  {'-'*5} {'-'*22} {'-'*6} {'-'*22} {'-'*7} {'-'*18} {'-'*6}")
    for rank, (score, log, dcp) in enumerate(scored[:n], 1):
        cfg = log.config
        print(
            f"  {rank:<5} {cfg['game_id']:<22} {cfg['drive_id']:>6} "
            f"{cfg['drive_result']:<22} {score:>7.3f} {str(log.final_morphology):<18} "
            f"{cfg['n_plays']:>6}"
        )


def print_playoff_arc(pairs: list[tuple[TrajectoryLog, DCPEvent]], pbp: pd.DataFrame) -> None:
    """Summarize playoff games."""
    print(f"\n{'='*70}")
    print("=== PLAYOFF ARC ===")
    print(f"{'='*70}")

    playoff_games = (
        pbp[(pbp["posteam"] == TEAM) & (pbp["season_type"] == "POST")]["game_id"]
        .unique()
        .tolist()
    )
    if not playoff_games:
        print("  No postseason games found for WAS in 2024.")
        return

    playoff_games.sort()
    for game_id in playoff_games:
        game_pairs = [
            (log, dcp) for log, dcp in pairs
            if log.config["game_id"] == game_id
        ]
        if not game_pairs:
            continue

        scores = [dcp.domain_metadata.get("dcp_composite", 0.0) for _, dcp in game_pairs]
        morphs = [log.final_morphology for log, _ in game_pairs]
        td_count = sum(1 for log, _ in game_pairs if log.config.get("drive_result") == "Touchdown")
        mean_breadth = sum(
            e.possibility_breadth
            for log, _ in game_pairs
            for e in log.events
        ) / max(1, sum(len(log.events) for log, _ in game_pairs))

        print(f"\n  Game: {game_id}")
        print(f"    Drives:          {len(game_pairs)}")
        print(f"    Touchdowns:      {td_count}")
        print(f"    Mean DCP:        {sum(scores)/len(scores):.3f}")
        print(f"    Max DCP:         {max(scores):.3f}")
        print(f"    Mean wp breadth: {mean_breadth:.3f}")
        from collections import Counter
        morph_counts = Counter(morphs)
        for morph, cnt in morph_counts.most_common():
            print(f"    {morph:<22}: {cnt}")


def print_season_arc(pairs: list[tuple[TrajectoryLog, DCPEvent]], pbp: pd.DataFrame) -> None:
    """Print per-week mean DCP and win probability."""
    print(f"\n{'='*70}")
    print("=== SEASON ARC (per week) ===")
    print(f"{'='*70}")

    game_week: dict[str, tuple[int, str]] = {}
    for _, row in pbp[pbp["posteam"] == TEAM][["game_id", "week", "season_type"]].drop_duplicates().iterrows():
        game_week[str(row["game_id"])] = (int(row["week"]), str(row["season_type"]))

    week_data: dict[tuple[int, str], list[float]] = defaultdict(list)
    week_wp:   dict[tuple[int, str], list[float]] = defaultdict(list)

    for log, dcp in pairs:
        gid = log.config["game_id"]
        if gid not in game_week:
            continue
        wk, stype = game_week[gid]
        score = dcp.domain_metadata.get("dcp_composite", 0.0)
        week_data[(wk, stype)].append(score)
        for e in log.events:
            week_wp[(wk, stype)].append(e.possibility_breadth)

    all_keys = sorted(week_data.keys(), key=lambda x: (0 if x[1] == "REG" else 1, x[0]))

    print(f"  {'Week':<6} {'Type':<6} {'Drives':>7} {'Mean DCP':>10} {'Mean WP':>10}")
    print(f"  {'-'*6} {'-'*6} {'-'*7} {'-'*10} {'-'*10}")
    for wk, stype in all_keys:
        scores = week_data[(wk, stype)]
        wps    = week_wp[(wk, stype)]
        print(
            f"  {wk:<6} {stype:<6} {len(scores):>7} "
            f"{sum(scores)/len(scores):>10.3f} "
            f"{sum(wps)/len(wps):>10.3f}"
        )


def print_ngs_daniels(pbp: pd.DataFrame, pairs: list[tuple[TrajectoryLog, DCPEvent]]) -> None:
    """
    NGS passing profile for Jayden Daniels — per week.

    avg_time_to_throw  : lower = defense collapsing the pocket faster = higher constraint
    aggressiveness     : % throws into tight windows — rises when options compress
    cpae               : completion % above expectation — positive = beating constraint
    avg_intended_air_yards: ambition of the throw (longer = more options being attempted)

    Cross-referenced with that week's mean DCP and drive count.
    """
    print(f"\n{'='*80}")
    print("=== JAYDEN DANIELS — NGS PASSING PROFILE (constraint lens) ===")
    print(f"{'='*80}")
    print("  avg_time_to_throw: lower → defense getting home faster → higher pocket constraint")
    print("  aggressiveness:    higher → more throws into tight windows → fewer open options")
    print("  cpae:              positive → exceeding expected completion despite constraint")
    print()

    ngs = nfl.import_ngs_data(years=[SEASON], stat_type='passing')
    daniels = ngs[
        (ngs['team_abbr'] == TEAM) &
        (ngs['player_last_name'] == 'Daniels')
    ].sort_values('week').reset_index(drop=True)

    # Build week → mean DCP lookup
    game_week: dict[str, int] = {}
    for _, row in pbp[pbp['posteam'] == TEAM][['game_id', 'week']].drop_duplicates().iterrows():
        game_week[str(row['game_id'])] = int(row['week'])

    week_dcp: dict[int, list[float]] = defaultdict(list)
    for log, dcp in pairs:
        wk = game_week.get(log.config['game_id'])
        if wk:
            week_dcp[wk].append(dcp.domain_metadata.get('dcp_composite', 0.0))

    hdr = f"  {'Wk':>3} {'TTT':>6} {'Aggr':>6} {'CPAE':>7} {'AirYds':>7} {'DCP\u0304':>6}  Note"
    print(hdr)
    print(f"  {'-'*3} {'-'*6} {'-'*6} {'-'*7} {'-'*7} {'-'*6}  {'-'*20}")

    for _, row in daniels.iterrows():
        wk   = int(row['week'])
        ttt  = row['avg_time_to_throw']
        aggr = row['aggressiveness']
        cpae = row['completion_percentage_above_expectation']
        ayd  = row['avg_intended_air_yards']
        wk_scores = week_dcp.get(wk, [])
        dcp_mean  = sum(wk_scores) / len(wk_scores) if wk_scores else 0.0

        notes = []
        if wk == 8:
            notes.append("<- HAIL MARYLAND")
        if ttt < 2.5:
            notes.append("short pocket")
        if aggr > 20:
            notes.append("high aggression")
        if cpae < -8:
            notes.append("below expected")
        elif cpae > 10:
            notes.append("above expected")

        print(
            f"  {wk:>3} {ttt:>6.2f} {aggr:>6.1f} {cpae:>+7.2f} {ayd:>7.2f} {dcp_mean:>6.3f}  {' | '.join(notes)}"
        )

    # Highlight: does shorter TTT correlate with lower DCP? (constraint forcing compression)
    ttt_vals  = [float(r['avg_time_to_throw']) for _, r in daniels.iterrows() if int(r['week']) in week_dcp]
    dcp_vals  = [sum(week_dcp[int(r['week'])]) / len(week_dcp[int(r['week'])]) for _, r in daniels.iterrows() if int(r['week']) in week_dcp]
    if len(ttt_vals) > 3:
        n     = len(ttt_vals)
        mx    = sum(ttt_vals) / n
        my    = sum(dcp_vals) / n
        cov   = sum((ttt_vals[i] - mx) * (dcp_vals[i] - my) for i in range(n)) / n
        std_x = (sum((v - mx) ** 2 for v in ttt_vals) / n) ** 0.5
        std_y = (sum((v - my) ** 2 for v in dcp_vals) / n) ** 0.5
        r_val = cov / (std_x * std_y) if std_x * std_y > 0 else 0.0
        print(f"\n  Pearson r(TTT, DCP): {r_val:+.3f}  "
              f"({'shorter TTT -> higher DCP' if r_val < -0.2 else 'shorter TTT -> lower DCP' if r_val > 0.2 else 'no clear correlation'})")


def print_situational_analysis(pbp: pd.DataFrame) -> None:
    """
    DVOA proxy: EPA by situational bucket for WAS offense.

    True DVOA (Football Outsiders) is subscription-only. This approximates it
    by splitting WAS offensive plays into situational buckets and comparing
    mean EPA — the same quantity DVOA is ultimately derived from.

    Buckets:
        late_and_close  : <=8 min remaining, score within 8 pts  -> maximum constraint
        two_minute      : <=2 min remaining, any score            -> time pressure ceiling
        red_zone        : opponent 20-yard line or closer         -> spatial compression
        third_down      : any 3rd down                           -> decision inflection
        normal          : everything else                        -> baseline
        garbage_time    : score margin > 24 pts                  -> minimal constraint
    """
    print(f"\n{'='*80}")
    print("=== SITUATIONAL EPA SPLITS (DVOA proxy) — WAS Offense 2024 ===")
    print(f"{'='*80}")
    print("  Higher EPA under constraint buckets = performs when compressed -> DCP-consistent")
    print()

    was = pbp[
        (pbp['posteam'] == TEAM) &
        (pbp['play'] == 1) &
        (~pbp['play_type'].isin({'kickoff', 'extra_point', 'no_play', 'qb_kneel', 'qb_spike'}))
    ].copy()

    def _bucket(row) -> str:
        t   = float(row['game_seconds_remaining']) if row['game_seconds_remaining'] == row['game_seconds_remaining'] else 1800.0
        sd  = float(row['score_differential'])     if row['score_differential']     == row['score_differential']     else 0.0
        yl  = float(row['yardline_100'])            if row['yardline_100']            == row['yardline_100']            else 50.0
        dn  = row['down']
        if abs(sd) > 24:
            return 'garbage_time'
        if t <= 120:
            return 'two_minute'
        if t <= 480 and abs(sd) <= 8:
            return 'late_and_close'
        if yl <= 20:
            return 'red_zone'
        if dn == 3:
            return 'third_down'
        return 'normal'

    was['bucket'] = was.apply(_bucket, axis=1)

    bucket_order = ['late_and_close', 'two_minute', 'red_zone', 'third_down', 'normal', 'garbage_time']
    bucket_label = {
        'late_and_close': 'Late & close   (<=8min, <=8pts)',
        'two_minute':     'Two-minute     (<=2min)',
        'red_zone':       'Red zone       (opp <=20)',
        'third_down':     'Third down     (all)',
        'normal':         'Normal         (baseline)',
        'garbage_time':   'Garbage time   (>24pt margin)',
    }

    print(f"  {'Situation':<32} {'Plays':>6} {'Mean EPA':>9} {'Total EPA':>10} {'EPA/Play':>9}")
    print(f"  {'-'*32} {'-'*6} {'-'*9} {'-'*10} {'-'*9}")

    for bk in bucket_order:
        sub = was[was['bucket'] == bk]['epa'].dropna()
        if len(sub) == 0:
            continue
        vals = [float(v) for v in sub]
        mean = sum(vals) / len(vals)
        total = sum(vals)
        print(f"  {bucket_label[bk]:<32} {len(vals):>6} {mean:>+9.3f} {total:>+10.2f} {mean:>+9.3f}")

    # Daniels rushing specifically — dual threat angle
    rush = was[(was['rusher_player_name'].str.contains('Daniels', na=False)) | (was['qb_scramble'] == 1)]
    if len(rush):
        rush_epa = [float(v) for v in rush['epa'].dropna()]
        print(f"\n  Daniels rushes/scrambles: {len(rush_epa)} plays | "
              f"mean EPA {sum(rush_epa)/len(rush_epa):+.3f} | "
              f"total EPA {sum(rush_epa):+.1f}")
        print("  -> Scramble = possibility space EXPANDS after pocket collapses (anti-DCP move)")


def print_third_down_analysis(pairs: list[tuple[TrajectoryLog, DCPEvent]], pbp: pd.DataFrame) -> None:
    """
    Third-down conversion as tension resolution metric.

    3rd down = the decision inflection point of every drive. Each conversion
    resets the possibility space (1st and 10 again). Each failure collapses
    it to near-zero (punt/turnover). Tracking conversion rate per week shows
    whether tension was repeatedly resolved or allowed to accumulate.
    """
    print(f"\n{'='*80}")
    print("=== THIRD-DOWN: TENSION RESOLUTION vs. ACCUMULATION ===")
    print(f"{'='*80}")
    print("  Conversion = breadth reset. Failure = constraint accumulates -> DCP tension spike.")
    print()

    plays = pbp[pbp['play'] == 1].copy()
    off_3rd = plays[(plays['posteam'] == TEAM) & (plays['down'] == 3)]
    def_3rd = plays[(plays['defteam'] == TEAM) & (plays['down'] == 3)]

    game_week: dict[str, tuple[int, str]] = {}
    for _, row in pbp[pbp['posteam'] == TEAM][['game_id', 'week', 'season_type']].drop_duplicates().iterrows():
        game_week[str(row['game_id'])] = (int(row['week']), str(row['season_type']))

    week_dcp: dict[int, list[float]] = defaultdict(list)
    for log, dcp in pairs:
        wk_info = game_week.get(log.config['game_id'])
        if wk_info:
            week_dcp[wk_info[0]].append(dcp.domain_metadata.get('dcp_composite', 0.0))

    weeks = sorted({v[0] for v in game_week.values()})

    print(f"  {'Wk':>3} {'Type':>4} {'Off 3rd':>8} {'Off Conv':>9} {'Def 3rd':>8} {'Def Conv':>9} {'DCP\u0304':>6}")
    print(f"  {'-'*3} {'-'*4} {'-'*8} {'-'*9} {'-'*8} {'-'*9} {'-'*6}")

    for wk in weeks:
        stype = next((v[1] for v in game_week.values() if v[0] == wk), 'REG')
        game_ids = {k for k, v in game_week.items() if v[0] == wk}

        o = off_3rd[off_3rd['game_id'].isin(game_ids)]
        d = def_3rd[def_3rd['game_id'].isin(game_ids)]

        o_att = len(o)
        o_conv = int(o['third_down_converted'].sum()) if o_att else 0
        d_att = len(d)
        d_conv = int(d['third_down_converted'].sum()) if d_att else 0

        wk_scores = week_dcp.get(wk, [])
        dcp_mean  = sum(wk_scores) / len(wk_scores) if wk_scores else 0.0

        o_rate = f"{o_conv}/{o_att} ({o_conv/o_att:.0%})" if o_att else "—"
        d_rate = f"{d_conv}/{d_att} ({d_conv/d_att:.0%})" if d_att else "—"
        print(f"  {wk:>3} {stype:>4} {o_att:>8} {o_rate:>9} {d_att:>8} {d_rate:>9} {dcp_mean:>6.3f}")

    # Season totals
    print()
    reg_games = {k for k, v in game_week.items() if v[1] == 'REG'}
    o_reg = off_3rd[off_3rd['game_id'].isin(reg_games)]
    d_reg = def_3rd[def_3rd['game_id'].isin(reg_games)]
    o_tot = len(o_reg); o_c = int(o_reg['third_down_converted'].sum())
    d_tot = len(d_reg); d_c = int(d_reg['third_down_converted'].sum())
    print(f"  Regular season: OFF {o_c}/{o_tot} ({o_c/o_tot:.0%})  DEF allowed {d_c}/{d_tot} ({d_c/d_tot:.0%})")


def print_dcp_vs_epa_divergence(pairs: list[tuple[TrajectoryLog, DCPEvent]]) -> None:
    """
    DCP vs. EPA divergence — where do they disagree and why?

    HIGH DCP / LOW EPA: long constrained drives that barely succeed or fail
    HIGH EPA / LOW DCP: garbage-time blowout scoring drives
    """
    print(f"\n{'='*80}")
    print("=== DCP vs. EPA DIVERGENCE ===")
    print(f"{'='*80}")
    print("  HIGH DCP / LOW EPA  -> constrained drive, compressed structure, weak outcome")
    print("  HIGH EPA / LOW DCP  -> easy scoring, minimal tension, no structural compression")
    print()

    records = []
    for log, dcp in pairs:
        cfg   = log.config
        score = dcp.domain_metadata.get('dcp_composite', 0.0)
        records.append({
            'game_id':      cfg['game_id'],
            'drive_id':     cfg['drive_id'],
            'result':       cfg['drive_result'],
            'dcp':          score,
            'mean_epa':     cfg.get('mean_epa', 0.0),
            'epa_var':      cfg.get('epa_variance', 0.0),
            'max_epa':      cfg.get('max_epa', 0.0),
            'n_plays':      cfg.get('n_plays', 0),
            'label':        cfg.get('label', ''),
            'morph':        log.final_morphology or '',
        })

    if not records:
        return

    dcp_sorted = sorted(r['dcp']      for r in records)
    epa_sorted = sorted(r['mean_epa'] for r in records)
    n = len(records)

    def _pctile(val, sorted_list):
        lo = 0
        rng = len(sorted_list)
        while lo < rng:
            mid = (lo + rng) // 2
            if sorted_list[mid] < val:
                lo = mid + 1
            else:
                rng = mid
        return lo / len(sorted_list)

    for r in records:
        r['dcp_pct'] = _pctile(r['dcp'],      dcp_sorted)
        r['epa_pct'] = _pctile(r['mean_epa'], epa_sorted)
        r['diverge'] = r['dcp_pct'] - r['epa_pct']

    high_dcp_low_epa = sorted(records, key=lambda r: r['diverge'], reverse=True)[:8]
    high_epa_low_dcp = sorted(records, key=lambda r: r['diverge'])[:8]
    high_var = sorted(records, key=lambda r: r['epa_var'], reverse=True)[:8]

    def _print_table(title, rows):
        print(f"  {title}")
        print(f"  {'Game':<22} {'Drv':>4} {'Result':<18} {'DCP':>6} {'mEPA':>7} {'EPAvar':>7} {'Plays':>5}  Note")
        print(f"  {'-'*22} {'-'*4} {'-'*18} {'-'*6} {'-'*7} {'-'*7} {'-'*5}  {'-'*20}")
        for r in rows:
            note = r['label'] if r['label'] else ''
            print(
                f"  {r['game_id']:<22} {r['drive_id']:>4} {r['result']:<18} "
                f"{r['dcp']:>6.3f} {r['mean_epa']:>+7.3f} {r['epa_var']:>7.3f} {r['n_plays']:>5}  {note}"
            )
        print()

    _print_table("HIGH DCP / LOW EPA  (structure without easy scoring):", high_dcp_low_epa)
    _print_table("HIGH EPA / LOW DCP  (easy scoring without compression):", high_epa_low_dcp)
    _print_table("HIGHEST EPA VARIANCE  (chaotic / walk-off type drives):", high_var)

    dcp_v = [r['dcp']      for r in records]
    epa_v = [r['mean_epa'] for r in records]
    mx, my = sum(dcp_v)/n, sum(epa_v)/n
    cov    = sum((dcp_v[i]-mx)*(epa_v[i]-my) for i in range(n)) / n
    sx     = (sum((v-mx)**2 for v in dcp_v)/n)**0.5
    sy     = (sum((v-my)**2 for v in epa_v)/n)**0.5
    r_dcp_epa = cov / (sx * sy) if sx * sy > 0 else 0.0
    print(f"  Pearson r(DCP, mean_EPA) across all drives: {r_dcp_epa:+.3f}")
    if abs(r_dcp_epa) < 0.3:
        print("  -> Weak correlation: DCP and EPA are measuring substantially different things.")
    elif r_dcp_epa > 0.5:
        print("  -> Strong positive: DCP and EPA largely agree — need more varied data to separate.")
    else:
        print(f"  -> Moderate correlation: partial overlap, {'DCP captures more constraint structure' if r_dcp_epa < 0 else 'EPA leads DCP'}.")


# =============================================================================
# PART 2: JAYDEN DANIELS DEEP DIVE
# =============================================================================

def load_ngs() -> pd.DataFrame:
    ngs = nfl.import_ngs_data(years=[SEASON], stat_type='passing')
    return ngs[
        (ngs['team_abbr'] == TEAM) &
        (ngs['player_last_name'] == 'Daniels')
    ].sort_values('week').reset_index(drop=True)


def print_game_log(pbp: pd.DataFrame) -> None:
    _sep()
    print("=== JAYDEN DANIELS 2024 — PER-GAME LOG ===")
    _sep()
    print("  Wk  Type  Opp   Result  Comp/Att    Yds   TD INT  Sck  RushAtt  RushYds  Scrm  EPA_tot  EPA/db")
    print(f"  {'-'*3} {'-'*4} {'-'*5} {'-'*7} {'-'*10} {'-'*5} {'-'*3} {'-'*3} {'-'*4} {'-'*8} {'-'*8} {'-'*4} {'-'*7} {'-'*6}")

    pass_plays = pbp[pbp['passer_player_name'] == QB].copy()
    rush_plays = pbp[pbp['rusher_player_name'] == QB].copy()

    game_meta: dict[str, dict] = {}
    for _, row in pbp[pbp['posteam'] == TEAM][
        ['game_id', 'week', 'season_type', 'defteam', 'away_team', 'home_team',
         'away_score', 'home_score', 'result', 'posteam']
    ].drop_duplicates('game_id').iterrows():
        gid = str(row['game_id'])
        wk  = int(row['week'])
        if wk in _MARIOTA_WEEKS:
            continue
        opp = str(row['defteam']) if str(row['posteam']) == TEAM else str(row['posteam'])
        home = str(row['home_team']) == TEAM
        score_for  = int(_sf(row['home_score'] if home else row['away_score']))
        score_opp  = int(_sf(row['away_score'] if home else row['home_score']))
        outcome    = 'W' if score_for > score_opp else 'L'
        game_meta[gid] = {
            'week': wk, 'stype': str(row['season_type']),
            'opp': opp, 'result': f"{outcome} {score_for}-{score_opp}",
        }

    season_epa: list[float] = []

    for gid, meta in sorted(game_meta.items(), key=lambda x: x[1]['week']):
        gpass = pass_plays[pass_plays['game_id'] == gid]
        grush = rush_plays[rush_plays['game_id'] == gid]
        gscr  = grush[grush['qb_scramble'] == 1]

        att  = int(gpass['pass_attempt'].sum())
        comp = int(gpass['complete_pass'].sum())
        yds  = int(_sf(gpass['passing_yards'].sum()))
        td   = int(gpass['pass_touchdown'].sum())
        ints = int(gpass['interception'].sum())
        sck  = int(gpass['sack'].sum())

        ratt = int(grush['rush_attempt'].sum())
        ryds = int(_sf(grush['rushing_yards'].sum()))
        scrm = len(gscr)

        epa_vals = (
            [_sf(v) for v in gpass['epa'].dropna()] +
            [_sf(v) for v in grush['epa'].dropna()]
        )
        epa_tot = sum(epa_vals)
        dbs     = att + int(grush['qb_scramble'].sum())
        epa_per = epa_tot / dbs if dbs else 0.0
        season_epa.extend(epa_vals)

        wk_str = f"{'*' if meta['stype']=='POST' else ' '}{meta['week']:>2}"
        print(
            f"  {wk_str} {meta['stype']:>4} {meta['opp']:>5} {meta['result']:>7}  "
            f"{comp:>3}/{att:<3}  {yds:>5} {td:>4} {ints:>3} {sck:>4} "
            f"{ratt:>8} {ryds:>8} {scrm:>4} {epa_tot:>+7.1f} {epa_per:>+6.3f}"
        )

    print(f"\n  Season total EPA (all Daniels plays): {sum(season_epa):+.1f}")
    print(f"  * = postseason")


def print_scramble_signature(pbp: pd.DataFrame) -> None:
    _sep()
    print("=== SCRAMBLE SIGNATURE — ANTI-DCP PROFILE ===")
    _sep()
    print("  Scramble = pocket compresses to near-zero -> Daniels escapes, creates new")
    print("  possibility space. This is the dual-threat anti-DCP move: reversing a")
    print("  compression event instead of accepting it (sack = accepting collapse).")
    print()

    rush = pbp[pbp['rusher_player_name'] == QB].copy()
    scrm = rush[rush['qb_scramble'] == 1].copy()
    designed = rush[rush['qb_scramble'] != 1].copy()
    sacks = pbp[(pbp['passer_player_name'] == QB) & (pbp['sack'] == 1)].copy()

    def _stats(df, label):
        if len(df) == 0:
            return
        epa_vals = [_sf(v) for v in df['epa'].dropna()]
        yds_vals = [_sf(v) for v in df['yards_gained'].dropna()]
        wp_vals  = [_sf(v) for v in df['wp'].dropna()]
        td_count = int(df['rush_touchdown'].sum()) if 'rush_touchdown' in df else 0
        print(f"  {label:<22} n={len(df):>4}  mean_EPA={_mean(epa_vals):>+6.3f}  "
              f"mean_yds={_mean(yds_vals):>5.1f}  TDs={td_count}  "
              f"mean_wp={_mean(wp_vals):.3f}")

    _stats(scrm,    "Scrambles")
    _stats(designed,"Designed runs")
    _stats(sacks,   "Sacks taken")

    print()
    print("  EPA comparison: scramble vs. sack (same situation, different response)")
    print(f"    Scramble mean EPA:     {_mean([_sf(v) for v in scrm['epa'].dropna()]):>+.3f}")
    print(f"    Sack mean EPA:         {_mean([_sf(v) for v in sacks['epa'].dropna()]):>+.3f}")
    s_epa = _mean([_sf(v) for v in scrm['epa'].dropna()])
    k_epa = _mean([_sf(v) for v in sacks['epa'].dropna()])
    print(f"    Delta (escape - accept): {s_epa - k_epa:>+.3f} EPA per play")

    print()
    print("  Scrambles by down:")
    for dn in [1, 2, 3, 4]:
        sub = scrm[scrm['down'] == dn]
        if len(sub) == 0:
            continue
        epa_v = [_sf(v) for v in sub['epa'].dropna()]
        print(f"    Down {dn}: {len(sub):>3} scrambles  mean_EPA={_mean(epa_v):>+.3f}")

    print()
    print("  Scrambles by game situation:")
    def _sit(row) -> str:
        t  = _sf(row.get('game_seconds_remaining'), 1800)
        sd = _sf(row.get('score_differential'), 0)
        if abs(sd) > 24: return 'garbage_time'
        if t <= 120:     return 'two_minute'
        if t <= 480 and abs(sd) <= 8: return 'late_and_close'
        if _sf(row.get('yardline_100'), 50) <= 20: return 'red_zone'
        return 'normal'

    sit_groups: dict[str, list[float]] = defaultdict(list)
    for _, row in scrm.iterrows():
        sit_groups[_sit(row)].append(_sf(row.get('epa'), 0.0))

    for sit in ['late_and_close', 'two_minute', 'red_zone', 'normal', 'garbage_time']:
        vals = sit_groups.get(sit, [])
        if vals:
            print(f"    {sit:<18}: {len(vals):>3}  mean_EPA={_mean(vals):>+.3f}")

    print()
    print("  Top 5 scrambles by EPA:")
    top_s = scrm.sort_values('epa', ascending=False).head(5)
    for _, r in top_s.iterrows():
        print(f"    wk{int(r['week'])} t={int(_sf(r['game_seconds_remaining']))}s  "
              f"diff={_sf(r['score_differential']):>+.0f}  epa={_sf(r['epa']):>+.3f}  "
              f"{str(r['desc'])[:70]}")


def print_constraint_performance(pbp: pd.DataFrame) -> None:
    _sep()
    print("=== CONSTRAINT PERFORMANCE — HOW DANIELS PLAYS UNDER PRESSURE ===")
    _sep()
    print("  Constraint defined via: score differential, time remaining, down & distance.")
    print()

    pass_plays = pbp[pbp['passer_player_name'] == QB].copy()
    rush_plays = pbp[pbp['rusher_player_name'] == QB].copy()
    all_plays  = pd.concat([pass_plays, rush_plays]).drop_duplicates('order_sequence')

    def _bucket(row) -> str:
        t  = _sf(row.get('game_seconds_remaining'), 1800)
        sd = _sf(row.get('score_differential'), 0)
        dn = row.get('down')
        yl = _sf(row.get('yardline_100'), 50)
        if abs(sd) > 24: return 'garbage_time'
        if t <= 120:     return 'two_minute_drill'
        if t <= 480 and abs(sd) <= 8: return 'late_and_close'
        if dn == 4:      return 'fourth_down'
        if dn == 3 and _sf(row.get('ydstogo'), 10) >= 7: return '3rd_and_long'
        if yl <= 5:      return 'goal_line'
        if yl <= 20:     return 'red_zone'
        return 'normal'

    bucket_order = [
        'two_minute_drill', 'late_and_close', 'fourth_down',
        '3rd_and_long', 'goal_line', 'red_zone', 'normal', 'garbage_time'
    ]
    bucket_label = {
        'two_minute_drill': 'Two-minute drill  (<=2min)',
        'late_and_close':   'Late & close      (<=8min, <=8)',
        'fourth_down':      'Fourth down',
        '3rd_and_long':     '3rd & 7+',
        'goal_line':        'Goal line         (<=5yd)',
        'red_zone':         'Red zone          (<=20yd)',
        'normal':           'Normal',
        'garbage_time':     'Garbage time      (>24pt)',
    }

    print(f"  {'Situation':<28} {'Plays':>6} {'meanEPA':>8} {'CPOE':>7} {'TDs':>4} {'INTs':>4} {'Scrm':>5}")
    print(f"  {'-'*28} {'-'*6} {'-'*8} {'-'*7} {'-'*4} {'-'*4} {'-'*5}")

    for bk in bucket_order:
        sub_all  = all_plays[all_plays.apply(_bucket, axis=1) == bk]
        sub_pass = pass_plays[pass_plays.apply(_bucket, axis=1) == bk]
        sub_rush = rush_plays[rush_plays.apply(_bucket, axis=1) == bk]
        if len(sub_all) == 0:
            continue
        epa_v = [_sf(v) for v in sub_all['epa'].dropna()]
        cpoe_v = [_sf(v) for v in sub_pass['cpoe'].dropna()]
        tds   = int(sub_all.get('pass_touchdown', pd.Series(dtype=float)).sum()
                    if 'pass_touchdown' in sub_all else 0) + \
                int(sub_all.get('rush_touchdown', pd.Series(dtype=float)).sum()
                    if 'rush_touchdown' in sub_all else 0)
        ints  = int(sub_pass['interception'].sum()) if len(sub_pass) else 0
        scrm  = int(sub_rush['qb_scramble'].sum()) if len(sub_rush) else 0
        cpoe_mean = _mean(cpoe_v)
        print(
            f"  {bucket_label[bk]:<28} {len(sub_all):>6} {_mean(epa_v):>+8.3f} "
            f"{cpoe_mean:>+7.2f} {tds:>4} {ints:>4} {scrm:>5}"
        )

    hit_plays = pass_plays[pass_plays['qb_hit'] == 1]
    clean_plays = pass_plays[(pass_plays['qb_hit'] != 1) & (pass_plays['sack'] != 1)]
    print()
    print("  Pocket pressure (qb_hit):")
    h_epa = [_sf(v) for v in hit_plays['epa'].dropna()]
    c_epa = [_sf(v) for v in clean_plays['epa'].dropna()]
    h_cpoe = [_sf(v) for v in hit_plays['cpoe'].dropna()]
    c_cpoe = [_sf(v) for v in clean_plays['cpoe'].dropna()]
    print(f"    Under pressure  n={len(hit_plays):>4}  mean_EPA={_mean(h_epa):>+.3f}  CPOE={_mean(h_cpoe):>+.2f}")
    print(f"    Clean pocket    n={len(clean_plays):>4}  mean_EPA={_mean(c_epa):>+.3f}  CPOE={_mean(c_cpoe):>+.2f}")
    print(f"    Pressure delta: EPA {_mean(h_epa)-_mean(c_epa):>+.3f}  CPOE {_mean(h_cpoe)-_mean(c_cpoe):>+.2f}")


def print_ngs_arc(ngs: pd.DataFrame) -> None:
    _sep()
    print("=== NGS PASSING ARC — DANIELS WEEKLY PROGRESSION ===")
    _sep()
    print("  Reading the season as a learning/compression trajectory.")
    print("  avg_air_yds = ambition of the throw | aggressiveness = tightness of window")
    print("  CPAE = completion above expectation | TTT = time in pocket before release")
    print()
    print(f"  {'Wk':>3} {'TTT':>6} {'AirYds':>7} {'Aggr':>6} {'CPAE':>7}  Structural note")
    print(f"  {'-'*3} {'-'*6} {'-'*7} {'-'*6} {'-'*7}  {'-'*35}")

    for _, r in ngs.iterrows():
        wk   = int(r['week'])
        if wk in _MARIOTA_WEEKS:
            continue
        ttt  = _sf(r['avg_time_to_throw'])
        ayd  = _sf(r['avg_intended_air_yards'])
        aggr = _sf(r['aggressiveness'])
        cpae = _sf(r['completion_percentage_above_expectation'])

        notes = []
        if wk == 8:  notes.append("HAIL MARYLAND — long hold, deep shot")
        if ttt < 2.4: notes.append("quick release (pressure response)")
        if ttt > 3.2: notes.append("extended pocket (time to look deep)")
        if aggr > 22: notes.append("tight-window throws")
        if cpae > 12: notes.append("well above expected completion")
        if cpae < -10: notes.append("below expected completion")
        if ayd > 11:  notes.append("attacking downfield")

        post = '*' if wk >= 19 else ' '
        print(f"  {post}{wk:>2} {ttt:>6.2f} {ayd:>7.2f} {aggr:>6.1f} {cpae:>+7.2f}  {' | '.join(notes)}")

    # Season trajectory: early vs. late regular season
    reg = ngs[~ngs['week'].isin(_MARIOTA_WEEKS) & (ngs['week'] < 19)]
    early = reg[reg['week'] <= 9]
    late  = reg[reg['week'] > 9]
    print()
    print("  Early season (wks 1-9) vs. late season (wks 10-18):")
    for label, subset in [("Early", early), ("Late", late)]:
        if len(subset) == 0:
            continue
        print(
            f"    {label}: TTT={_mean([_sf(v) for v in subset['avg_time_to_throw']]):.2f}s  "
            f"AirYds={_mean([_sf(v) for v in subset['avg_intended_air_yards']]):.2f}  "
            f"Aggr={_mean([_sf(v) for v in subset['aggressiveness']]):.1f}  "
            f"CPAE={_mean([_sf(v) for v in subset['completion_percentage_above_expectation']]):>+.2f}"
        )


def print_ceiling_and_floor(pbp: pd.DataFrame) -> None:
    _sep()
    print("=== PLAY CEILING & FLOOR — BEST AND WORST SINGLE PLAYS ===")
    _sep()

    pass_plays = pbp[pbp['passer_player_name'] == QB].copy()
    rush_plays = pbp[pbp['rusher_player_name'] == QB].copy()
    all_plays  = pd.concat([pass_plays, rush_plays]).drop_duplicates('order_sequence')
    all_plays_clean = all_plays.dropna(subset=['epa'])

    def _fmt(r) -> str:
        wk = int(_sf(r['week']))
        t  = int(_sf(r['game_seconds_remaining']))
        sd = _sf(r['score_differential'])
        ep = _sf(r['epa'])
        return (f"    wk{wk:>2} t={t:>4}s diff={sd:>+.0f}  epa={ep:>+.3f}  "
                f"{str(r['desc'])[:72]}")

    print("  Top 8 plays by EPA (the ceiling):")
    for _, r in all_plays_clean.nlargest(8, 'epa').iterrows():
        print(_fmt(r))

    print()
    print("  Bottom 8 plays by EPA (the floor):")
    for _, r in all_plays_clean.nsmallest(8, 'epa').iterrows():
        print(_fmt(r))


def print_comeback_drives(pbp: pd.DataFrame) -> None:
    _sep()
    print("=== COMEBACK / GAME-WINNING DRIVES ===")
    _sep()
    print("  Drives where WAS was trailing in 4th quarter and either scored")
    print("  or set up the winning score. Daniels as structural agent under")
    print("  maximum constraint (low breadth, high time pressure).")
    print()

    q4 = pbp[
        (pbp['passer_player_name'] == QB) &
        (pbp['game_seconds_remaining'] <= 900) &
        (pbp['score_differential'] < 0) &
        (pbp['posteam'] == TEAM)
    ].copy()

    if len(q4) == 0:
        print("  No qualifying comeback plays found.")
        return

    for gid in sorted(q4['game_id'].unique()):
        game_plays = q4[q4['game_id'] == gid].sort_values('game_seconds_remaining', ascending=False)
        epa_v = [_sf(v) for v in game_plays['epa'].dropna()]
        tds   = int(game_plays['pass_touchdown'].sum())
        wk    = int(game_plays['week'].iloc[0])
        opp   = str(game_plays['defteam'].iloc[0])

        game_row = pbp[pbp['game_id'] == gid].iloc[0]
        home  = str(game_row['home_team']) == TEAM
        sf    = int(_sf(game_row['home_score'] if home else game_row['away_score']))
        so    = int(_sf(game_row['away_score'] if home else game_row['home_score']))
        won   = sf > so

        hail  = '<- HAIL MARYLAND' if gid == '2024_08_CHI_WAS' else ''
        print(
            f"  wk{wk:>2} vs {opp}  {'W' if won else 'L'} {sf}-{so}  "
            f"trailing plays={len(game_plays)}  TDs={tds}  "
            f"mean_EPA={_mean(epa_v):>+.3f}  total_EPA={sum(epa_v):>+.1f}  {hail}"
        )
        if gid == '2024_08_CHI_WAS':
            final = game_plays[game_plays['game_seconds_remaining'] <= 25]
            for _, r in final.sort_values('game_seconds_remaining', ascending=False).iterrows():
                print(f"      t={int(_sf(r['game_seconds_remaining']))}s  {str(r['desc'])[:72]}")


def print_season_compression(pbp: pd.DataFrame) -> None:
    _sep()
    print("=== SEASON COMPRESSION ARC — DANIELS EPA TRAJECTORY ===")
    _sep()
    print("  Weekly EPA as a proxy for how well Daniels was converting")
    print("  possibility into outcome. Trending up = compression improving.")
    print()

    pass_plays = pbp[pbp['passer_player_name'] == QB].copy()
    rush_plays = pbp[pbp['rusher_player_name'] == QB].copy()

    weeks_data: dict[int, dict] = {}
    for wk in sorted(pass_plays['week'].unique()):
        if int(wk) in _MARIOTA_WEEKS:
            continue
        wp = pass_plays[pass_plays['week'] == wk]
        wr = rush_plays[rush_plays['week'] == wk]
        stype = str(wp['season_type'].iloc[0]) if len(wp) else 'REG'
        opp   = str(wp['defteam'].iloc[0])     if len(wp) else '?'

        epa_pass  = [_sf(v) for v in wp['epa'].dropna()]
        epa_rush  = [_sf(v) for v in wr['epa'].dropna()]
        epa_all   = epa_pass + epa_rush

        cpoe_v    = [_sf(v) for v in wp['cpoe'].dropna()]
        att       = int(wp['pass_attempt'].sum())
        comp      = int(wp['complete_pass'].sum())
        scrm      = int(wr['qb_scramble'].sum())

        weeks_data[int(wk)] = {
            'stype': stype, 'opp': opp,
            'epa_total': sum(epa_all), 'epa_per_db': _mean(epa_all),
            'cpoe': _mean(cpoe_v),
            'comp_pct': comp / att if att else 0,
            'scrm': scrm,
        }

    print(f"  {'Wk':>3} {'Type':>4} {'Opp':>5} {'EPA_tot':>8} {'EPA/db':>7} {'CPOE':>7} {'Comp%':>6} {'Scrm':>5}  Bar")
    print(f"  {'-'*3} {'-'*4} {'-'*5} {'-'*8} {'-'*7} {'-'*7} {'-'*6} {'-'*5}  {'-'*20}")

    for wk, d in weeks_data.items():
        bar_val = d['epa_total']
        bar_len = max(0, min(20, int(bar_val * 2 + 10)))
        bar     = '█' * bar_len
        post    = '*' if d['stype'] == 'POST' else ' '
        print(
            f"  {post}{wk:>2} {d['stype']:>4} {d['opp']:>5} "
            f"{d['epa_total']:>+8.1f} {d['epa_per_db']:>+7.3f} "
            f"{d['cpoe']:>+7.2f} {d['comp_pct']:>6.1%} {d['scrm']:>5}  {bar}"
        )

    all_epa = [d['epa_total'] for d in weeks_data.values() if d['stype'] == 'REG']
    all_cpoe = [d['cpoe'] for d in weeks_data.values() if d['stype'] == 'REG']
    print()
    print(f"  Regular season: total EPA {sum(all_epa):>+.1f}  mean CPOE {_mean(all_cpoe):>+.2f}")


def print_season_dcp_arc(pbp: pd.DataFrame) -> None:
    """
    Treat the entire 2024 season as a single DCP macro-trajectory.

    Each game = one TrajectoryEvent.
    possibility_breadth = WAS pre-game win probability (first WAS offensive play wp)
    constraint_proxy    = season fraction (week / 22.0 — time pressure accumulating)
    collapse_step       = wk21 NFC Championship vs PHI (last game played)
    final_morphology    = DISSOLUTIVE (season ended without Super Bowl)
    """
    from domains.self.analysis.probes import (
        estimate_tension,
        estimate_post_collapse_narrowing,
        compute_qualification_status,
    )
    from domains.self.analysis.trajectory import (
        TrajectoryEvent, TrajectoryLog,
        EVENT_SCHEMA_VERSION, LOG_SCHEMA_VERSION,
    )

    _sep()
    print("=== SEASON AS DCP MACRO-TRAJECTORY — 2024 WAS ARC ===")
    _sep()
    print("  Each game = one step. Entire season = one TrajectoryLog.")
    print("  possibility_breadth = WAS pre-game win probability (opening wp)")
    print("  constraint_proxy    = season fraction (week / 22 total possible)")
    print("  collapse_step       = wk21 NFC Championship (PHI) — season-ending")
    print("  final_morphology    = DISSOLUTIVE (eliminated 1 game from Super Bowl)")
    print()

    was_plays = pbp[pbp['posteam'] == TEAM].sort_values('order_sequence').copy()

    game_steps: list[dict] = []
    for gid in sorted(was_plays['game_id'].unique()):
        game_plays = was_plays[was_plays['game_id'] == gid].sort_values('order_sequence')
        wk = int(game_plays['week'].iloc[0])
        if wk in _MARIOTA_WEEKS:
            continue

        stype = str(game_plays['season_type'].iloc[0])
        opp   = str(game_plays['defteam'].iloc[0])

        wp_open = _sf(game_plays['wp'].iloc[0], default=0.5)

        gr   = pbp[pbp['game_id'] == gid].iloc[0]
        home = str(gr['home_team']) == TEAM
        sf   = int(_sf(gr['home_score'] if home else gr['away_score']))
        so   = int(_sf(gr['away_score'] if home else gr['home_score']))
        won  = sf > so

        wp_final = _sf(game_plays['wp'].iloc[-1], default=(1.0 if won else 0.0))
        epa_vals = [_sf(v) for v in game_plays['epa'].dropna()]

        game_steps.append({
            'game_id': gid, 'week': wk, 'stype': stype, 'opp': opp,
            'wp_open': wp_open, 'wp_final': wp_final,
            'won': won, 'score_for': sf, 'score_opp': so,
            'epa_total': sum(epa_vals),
            'season_fraction': wk / 22.0,
        })

    game_steps.sort(key=lambda x: x['week'])

    breadth_series: list[float] = [g['wp_open'] for g in game_steps]
    events = []

    print(f"  {'Wk':>3} {'Type':>4} {'Opp':>5} {'Result':>7}  "
          f"{'WP_open':>7} {'Constr':>7} {'Tension':>7}  Arc")
    print(f"  {'-'*3} {'-'*4} {'-'*5} {'-'*7}  "
          f"{'-'*7} {'-'*7} {'-'*7}  {'-'*22}")

    collapse_idx: int = len(game_steps) - 1

    for i, g in enumerate(game_steps):
        breadth   = g['wp_open']
        constraint = g['season_fraction']
        tension    = estimate_tension(breadth_series[:i + 1])

        bar_len = max(0, min(20, int(breadth * 20)))
        bar     = '█' * bar_len + '░' * (20 - bar_len)

        is_collapse = (i == collapse_idx)
        post_flag   = ' <- COLLAPSE' if is_collapse else ''
        hail_flag   = ' <- HAIL MARYLAND' if g['game_id'] == '2024_08_CHI_WAS' else ''
        post_marker = '*' if g['stype'] == 'POST' else ' '
        res_str     = f"{'W' if g['won'] else 'L'} {g['score_for']}-{g['score_opp']}"

        print(
            f"  {post_marker}{g['week']:>2} {g['stype']:>4} {g['opp']:>5} {res_str:>7}  "
            f"{breadth:>7.3f} {constraint:>7.3f} {tension:>7.4f}  {bar}{post_flag}{hail_flag}"
        )

        state = {
            'game_id':        g['game_id'],
            'week':           g['week'],
            'season_type':    g['stype'],
            'opponent':       g['opp'],
            'won':            g['won'],
            'score':          f"{g['score_for']}-{g['score_opp']}",
            'wp_open':        round(breadth, 4),
            'wp_final':       round(g['wp_final'], 4),
            'epa_total':      round(g['epa_total'], 3),
            'season_fraction': round(constraint, 4),
            'fixture':        'was_2024_season',
        }
        ev = TrajectoryEvent(
            step                = i,
            possibility_breadth = round(breadth, 4),
            constraint_proxy    = round(constraint, 4),
            tension_proxy       = round(tension, 4),
            state_summary       = state,
            schema_version      = EVENT_SCHEMA_VERSION,
        )
        if is_collapse:
            ev.collapse_flag       = True
            ev.collapse_morphology = 'DISSOLUTIVE'
        events.append(ev)

    post_narrowing = estimate_post_collapse_narrowing(breadth_series, collapse_idx)
    qual = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = True,
        has_tension_proxy     = any(estimate_tension(breadth_series[:i + 1]) > 0
                                    for i in range(1, len(breadth_series))),
        has_collapse_proxy    = True,
        has_post_collapse     = (post_narrowing is not None),
    )

    reg_games = [g for g in game_steps if g['stype'] == 'REG']
    post_games = [g for g in game_steps if g['stype'] == 'POST']
    reg_wins   = sum(1 for g in reg_games if g['won'])
    post_wins  = sum(1 for g in post_games if g['won'])
    mean_wp    = _mean([g['wp_open'] for g in game_steps])
    max_wp_g   = max(game_steps, key=lambda g: g['wp_open'])
    min_wp_g   = min(game_steps, key=lambda g: g['wp_open'])
    peak_epa_g = max(game_steps, key=lambda g: g['epa_total'])

    print()
    print(f"  -- Macro trajectory summary --")
    print(f"  Games modeled:       {len(game_steps)} ({len(reg_games)} REG + {len(post_games)} POST)")
    print(f"  Record:              {reg_wins}-{len(reg_games)-reg_wins} REG | {post_wins}-{len(post_games)-post_wins} POST")
    print(f"  Mean opening WP:     {mean_wp:.3f}")
    print(f"  Highest-confidence:  wk{max_wp_g['week']} vs {max_wp_g['opp']}  wp={max_wp_g['wp_open']:.3f}")
    print(f"  Lowest-confidence:   wk{min_wp_g['week']} vs {min_wp_g['opp']}  wp={min_wp_g['wp_open']:.3f}")
    print(f"  Peak EPA game:       wk{peak_epa_g['week']} vs {peak_epa_g['opp']}  EPA={peak_epa_g['epa_total']:+.1f}")
    print(f"  Collapse step:       {collapse_idx} (wk21 NFC Championship vs PHI)")
    print(f"  Post-collapse narr:  {post_narrowing}")
    print(f"  Qualification:       {qual}")
    print(f"  Final morphology:    DISSOLUTIVE")

    events[collapse_idx].post_collapse_narrowing = post_narrowing

    log = TrajectoryLog(
        fixture_id           = 'was_2024_season',
        fixture_type         = 'NFL Season Arc (nfl_data_py)',
        run_id               = 'was_season_2024_macro',
        seed                 = hash('was_season_2024_macro') % (2**31),
        config               = {
            'team':            TEAM,
            'season':          SEASON,
            'n_games':         len(game_steps),
            'record_reg':      f"{reg_wins}-{len(reg_games)-reg_wins}",
            'record_post':     f"{post_wins}-{len(post_games)-post_wins}",
            'mean_opening_wp': round(mean_wp, 4),
        },
        events               = events,
        collapse_step        = collapse_idx,
        final_morphology     = 'DISSOLUTIVE',
        qualification_status = qual,
        schema_version       = LOG_SCHEMA_VERSION,
    )

    print()
    print(f"  TrajectoryLog built: run_id={log.run_id}  steps={len(log.events)}")
    print(f"  Schema: {log.schema_version}")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="2024 Washington Commanders DCP Analysis")
    parser.add_argument(
        "--section", choices=["team", "daniels", "all"], default="all",
        help="Which section to run (default: all)"
    )
    args = parser.parse_args()

    # Single data load shared between both sections
    pbp = load_pbp()

    # Filter to WAS plays only for speed
    was_pbp = pbp[(pbp["posteam"] == TEAM) | (pbp["defteam"] == TEAM)].copy()

    section = args.section

    # ── Part 1: Team-level drive analysis ────────────────────────────────────
    if section in ("team", "all"):
        print(f"\n{'='*80}")
        print("PART 1: TEAM-LEVEL DRIVE ANALYSIS")
        print(f"{'='*80}")

        pairs = build_was_drives(was_pbp)

        print_season_stats(pairs)
        print_top_drives(pairs, n=10)
        annotate_hail_maryland(pairs, was_pbp)
        print_playoff_arc(pairs, was_pbp)
        print_season_arc(pairs, was_pbp)
        print_ngs_daniels(was_pbp, pairs)
        print_situational_analysis(was_pbp)
        print_third_down_analysis(pairs, was_pbp)
        print_dcp_vs_epa_divergence(pairs)

        print(f"\nPart 1 complete. {len(pairs)} WAS offensive drives analyzed.")

    # ── Part 2: Jayden Daniels deep dive ─────────────────────────────────────
    if section in ("daniels", "all"):
        print(f"\n{'='*80}")
        print("PART 2: JAYDEN DANIELS DEEP DIVE")
        print(f"{'='*80}")

        ngs = load_ngs()

        print_game_log(was_pbp)
        print_scramble_signature(was_pbp)
        print_constraint_performance(was_pbp)
        print_ngs_arc(ngs)
        print_ceiling_and_floor(was_pbp)
        print_comeback_drives(was_pbp)
        print_season_compression(was_pbp)
        print_season_dcp_arc(was_pbp)

        print(f"\n{'='*80}")
        print("Part 2 complete.")

    print("\nDone.")


if __name__ == "__main__":
    main()
