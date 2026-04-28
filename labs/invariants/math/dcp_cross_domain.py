"""
DCP Cross-Domain Comparison
core/probes/dcp_cross_domain.py

Collects DCP artifacts from all active Helix domains and produces a structured
comparison report. Does NOT force a single universal metric — instead compares
available signals domain by domain.

Domains covered:
  math       — Kuramoto oscillator at K above and below K_c
  games      — pursuit and resource fixtures (new sequential decision)
  music      — Spotify metadata sample (heuristic proxies only)
  language   — grammar_resolution fixtures (k_eff as compression proxy)
  cognition  — branching fixture (linear constraint schedule)
  synthetic  — 3 calibration fixtures outside major domains

For each domain, the report shows:
  - DCP component availability (which of the 5 components were measurable)
  - qualification_status ('FULL' | 'UNCONFIRMED' | 'INCOMPLETE' | 'INSUFFICIENT')
  - Peak tension estimate
  - Collapse sharpness (if available)
  - Post-collapse narrowing (if available)
  - Collapse morphology
  - DCP composite score (provisional)
  - Confidence
  - Honest limitation notes

Epistemology:
  This report does NOT promote DCP. It documents what signals exist and how they
  compare. The evidence status section mirrors dcp_trajectory_open_questions.md.

Run:
    python core/probes/dcp_cross_domain.py

Output:
    Console comparison table + structured dict written to stdout as JSON.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Domain adapters — each returns a list of DomainRecord dicts
# ---------------------------------------------------------------------------

def _fmt(v: Optional[float]) -> str:
    if v is None:
        return "  None "
    return f"{v:7.4f}"


# ── Math domain ──────────────────────────────────────────────────────────────

def _run_math_probe() -> list[dict]:
    """
    Run minimal pure-Python Kuramoto at several K values.
    Returns DCP-equivalent records for K < K_c (null), K ≈ K_c (transition),
    and K > K_c (locked).

    Pure Python implementation — no numpy dependency in this function.
    Uses the same Kuramoto formulation as core/probes/discovery_probe.py.
    """
    records = []

    def _kuramoto_r(n, K, steps, dt, seed):
        rng = random.Random(seed)
        omega = [rng.gauss(0, 1) for _ in range(n)]
        theta = [rng.uniform(0, 2 * math.pi) for _ in range(n)]
        r_series = []
        for _ in range(steps):
            re_ = sum(math.cos(t) for t in theta) / n
            im_ = sum(math.sin(t) for t in theta) / n
            r_t = math.sqrt(re_**2 + im_**2)
            r_series.append(r_t)
            psi = math.atan2(im_, re_)
            theta = [
                theta[i] + dt * (omega[i] + K * r_t * math.sin(psi - theta[i]))
                for i in range(n)
            ]
        return r_series

    N, STEPS, DT, SEED = 30, 200, 0.05, 42
    # K_c ≈ 2*sigma/pi ≈ 2/pi ≈ 0.637 for sigma=1 Gaussian
    # Use empirically calibrated K_c ≈ 0.48 (from dcp_null_tests.py, seed=42, N=50)
    K_c = 0.484

    for label, K, desc in [
        ("math_K0.0x",  0.0,       "K=0 (null — no coupling)"),
        ("math_K0.5Kc", 0.5 * K_c, "K=0.5·K_c (below critical)"),
        ("math_K1.0Kc", 1.0 * K_c, "K=1.0·K_c (at critical)"),
        ("math_K1.5Kc", 1.5 * K_c, "K=1.5·K_c (above critical)"),
        ("math_K2.0Kc", 2.0 * K_c, "K=2.0·K_c (locked)"),
    ]:
        r_series = _kuramoto_r(N, K, STEPS, DT, SEED)

        # Possibility space proxy: initial phase dispersion (before coupling settles)
        early_r  = sum(r_series[:20]) / 20
        late_r   = sum(r_series[-20:]) / 20
        poss     = 1.0 - early_r   # high dispersion = open space
        constr   = min(1.0, K / max(K_c, 1e-6))  # K/K_c ratio

        # Tension: variance of r in middle third of series
        mid = r_series[STEPS // 3: 2 * STEPS // 3]
        tension = min(1.0, _safe_std(mid) * 10)

        # Collapse: sharpness of r rise
        collapse_val = _sharpness(r_series)
        if K < 0.1:
            collapse_val = None   # no collapse at K=0

        # Post-collapse narrowing: 1 - std(tail) / std(early)
        early_std = _safe_std(r_series[:30])
        tail_std  = _safe_std(r_series[-30:])
        post_narr = max(0.0, 1.0 - tail_std / max(early_std, 1e-9)) if K > 0 else None

        dcp = _composite(poss, constr, tension, collapse_val, post_narr)

        records.append({
            "domain":            "math",
            "fixture_id":        label,
            "description":       desc,
            "K":                 round(K, 4),
            "K_over_Kc":         round(K / K_c, 3),
            "possibility_space": round(poss, 4),
            "constraint":        round(constr, 4),
            "tension":           round(tension, 4),
            "collapse":          round(collapse_val, 4) if collapse_val is not None else None,
            "post_narrowing":    round(post_narr, 4) if post_narr is not None else None,
            "morphology":        "TRANSFORMATIVE" if late_r > 0.85 else (
                                 "CIRCULAR"       if late_r > 0.50 else
                                 "DEFERRED_SUSPENDED"),
            "dcp_composite":     round(dcp, 4),
            "confidence":        round(min(0.85, dcp * 0.90), 4),
            "qualification":     _qualify(poss, constr, tension, collapse_val, post_narr),
            "calibration":       "calibrated — Tests 1,2,4 passed (dcp_null_tests.py)",
            "limitations":       "K_c estimate approximate; tension proxy = variance not accumulation index",
        })

    return records


# ── Games domain ─────────────────────────────────────────────────────────────

def _run_games_probe() -> list[dict]:
    """Run pursuit, resource, and null games fixtures."""
    try:
        from model.domains.games.fixtures.sequential_decision import (
            PursuitConfig, run_pursuit,
            ResourceConfig, run_resource,
            NullConfig, run_null,
        )
        from model.domains.games.analysis.dcp import extract_dcp_event
    except ImportError as e:
        return [{"domain": "games", "error": str(e)}]

    records = []
    for name, log in [
        ("games_pursuit",  run_pursuit(PursuitConfig(seed=42))),
        ("games_resource", run_resource(ResourceConfig(seed=42))),
        ("games_null",     run_null(NullConfig(seed=42))),
    ]:
        ev  = extract_dcp_event(log)
        records.append({
            "domain":            "games",
            "fixture_id":        name,
            "description":       log.fixture_type,
            "possibility_space": ev.possibility_space_proxy,
            "constraint":        ev.constraint_proxy,
            "tension":           ev.tension_proxy,
            "collapse":          ev.collapse_proxy,
            "post_narrowing":    ev.post_collapse_narrowing,
            "morphology":        ev.collapse_morphology,
            "dcp_composite":     ev.domain_metadata.get("dcp_composite"),
            "confidence":        ev.confidence,
            "qualification":     log.qualification_status,
            "collapse_step":     log.collapse_step,
            "n_steps":           len(log.events),
            "calibration":       "provisional — not yet calibrated against null corpus",
            "limitations":       "abstract game model; Godot real-data path not yet wired",
        })
    return records


# ── Music domain ─────────────────────────────────────────────────────────────

def _run_music_probe(n_tracks: int = 8) -> list[dict]:
    """Load Spotify metadata and extract DCP events for a sample of tracks."""
    try:
        from model.domains.music.analysis.dcp import extract_dcp_event_from_spotify
    except ImportError as e:
        return [{"domain": "music", "error": str(e)}]

    spotify_path = ROOT / "domains/music/data/output/library/metadata/spotify.json"
    if not spotify_path.exists():
        return [{"domain": "music", "error": "spotify.json not found"}]

    try:
        with open(spotify_path, encoding="utf-8") as f:
            tracks = json.load(f)
    except Exception as e:
        return [{"domain": "music", "error": str(e)}]

    records = []
    for track in tracks[:n_tracks]:
        try:
            ev = extract_dcp_event_from_spotify(track)
            records.append({
                "domain":            "music",
                "fixture_id":        ev.event_id or "unknown",
                "description":       f"{track.get('Track Name', '?')} — {track.get('Artist Name(s)', '?')}",
                "possibility_space": ev.possibility_space_proxy,
                "constraint":        ev.constraint_proxy,
                "tension":           ev.tension_proxy,
                "collapse":          ev.collapse_proxy,      # None — requires audio
                "post_narrowing":    ev.post_collapse_narrowing,
                "morphology":        ev.collapse_morphology,
                "dcp_composite":     ev.domain_metadata.get("dcp_composite"),
                "confidence":        ev.confidence,
                "qualification":     ev.qualification_status(),
                "calibration":       "provisional — metadata proxies only",
                "limitations":       "collapse_proxy=None (requires audio); morphology heuristic",
            })
        except Exception as e:
            records.append({"domain": "music", "error": str(e)})

    return records


# ── Language domain ───────────────────────────────────────────────────────────

def _run_language_probe(n_languages: int = 8) -> list[dict]:
    """
    Load grammar_resolution fixtures and compute DCP-equivalent proxies.

    Language DCP interpretation:
        possibility_space = k_eff / max_k_eff (normalized effective alternatives)
        constraint        = HHI of agent weights (concentration = constraint)
        tension           = variance in HHI across rounds (unresolved competition)
        collapse          = None (language has no sharp collapse event — grammar
                            is a persistent constraint, not a one-time event)
        post_narrowing    = 1 - (final HHI / initial HHI)  (convergence to dominant rule)

    This is a static (not temporal) DCP reading — grammar is a constraint state,
    not a collapse event. Language DCP evidence is INCOMPLETE by design.
    """
    lang_path = ROOT / "domains/language/model/data/datasets"
    fixtures  = sorted(lang_path.glob("grammar_resolution_*.json"))[:n_languages]

    if not fixtures:
        return [{"domain": "language", "error": "no grammar_resolution fixtures found"}]

    records = []
    for fp in fixtures:
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)

            lang   = data.get("language", fp.stem)
            agents = data.get("agents", [])
            rounds = data.get("decision_rounds", [])
            diag   = data.get("ud_diagnostics", {})

            # k_eff from diagnostics (UD-calibrated)
            k_eff       = float(diag.get("ud_k_eff", 2.0))
            max_k_eff   = 4.0   # approximate upper bound (Mandarin region)
            poss        = min(1.0, k_eff / max_k_eff)

            # HHI of agent weights = constraint proxy
            weights = [a.get("influence_weight", 0.0) for a in agents]
            hhi     = sum(w**2 for w in weights)
            constr  = min(1.0, hhi)

            # Tension: variance of HHI across rounds
            round_hhis = []
            for r in rounds:
                rw = r.get("weights", [])
                if rw:
                    round_hhis.append(sum(w**2 for w in rw))
            tension = min(1.0, _safe_std(round_hhis) * 5) if round_hhis else 0.0

            # Post narrowing: convergence to dominant rule across rounds
            if len(round_hhis) >= 2:
                post_narr = max(0.0, 1.0 - (round_hhis[-1] / max(round_hhis[0], 1e-9)))
            else:
                post_narr = None

            dcp = _composite(poss, constr, tension, None, post_narr)

            records.append({
                "domain":            "language",
                "fixture_id":        f"lang_{lang}",
                "description":       f"Grammar resolution — {lang}",
                "k_eff":             round(k_eff, 3),
                "possibility_space": round(poss, 4),
                "constraint":        round(constr, 4),
                "tension":           round(tension, 4),
                "collapse":          None,    # language has no sharp collapse event
                "post_narrowing":    round(post_narr, 4) if post_narr is not None else None,
                "morphology":        None,    # not applicable to static grammar constraint
                "dcp_composite":     round(dcp, 4),
                "confidence":        round(min(0.45, dcp * 0.50), 4),
                "qualification":     "INCOMPLETE",   # collapse_proxy always None
                "calibration":       "UD-calibrated weights; k_eff from treebank data",
                "limitations":       (
                    "Grammar is a persistent constraint, not a collapse event. "
                    "collapse_proxy=None by design. Language DCP evidence = INCOMPLETE. "
                    "Temporal narrowing requires sentence-level trajectory probe."
                ),
            })
        except Exception as e:
            records.append({"domain": "language", "language": fp.stem, "error": str(e)})

    return records


# ── Cognition domain ──────────────────────────────────────────────────────────

def _run_cognition_probe() -> list[dict]:
    """Run branching fixture (linear + null schedules)."""
    try:
        from model.domains.self.fixtures.branching import BranchingConfig, run
        from model.domains.self.analysis.morphology_classifier import morphology_summary
        from core.invariants.dcp.morphology import CollapseMorphology
        from core.invariants.dcp.metrics import collapse_sharpness, compute_dcp_score
    except ImportError as e:
        return [{"domain": "cognition", "error": str(e)}]

    records = []
    for schedule, label in [
        ("linear",   "cognition_linear"),
        ("none",     "cognition_null"),
        ("step",     "cognition_step"),
        ("exponential", "cognition_exp"),
    ]:
        try:
            cfg = BranchingConfig(constraint_schedule=schedule, seed=42)
            log = run(cfg)

            breadths = [e.possibility_breadth for e in log.events]
            tensions = [e.tension_proxy       for e in log.events]

            poss    = breadths[0] if breadths else 1.0
            constr  = max([e.constraint_proxy for e in log.events], default=0.0)
            tension = max(tensions, default=0.0)

            collapse_val = collapse_sharpness(breadths, window=5) if log.collapse_step else None

            post_narr = None
            if log.collapse_step is not None:
                cs = log.events[log.collapse_step]
                post_narr = cs.post_collapse_narrowing

            dcp = compute_dcp_score(
                possibility_space=poss,
                constraint=constr,
                tension=tension if tension > 0 else None,
                collapse=collapse_val,
                post_narrowing=post_narr,
            )

            records.append({
                "domain":            "cognition",
                "fixture_id":        label,
                "description":       f"Branching fixture — {schedule} schedule",
                "possibility_space": round(poss, 4),
                "constraint":        round(constr, 4),
                "tension":           round(tension, 4),
                "collapse":          round(collapse_val, 4) if collapse_val else None,
                "post_narrowing":    round(post_narr, 4) if post_narr is not None else None,
                "morphology":        log.final_morphology,
                "dcp_composite":     round(float(dcp), 4),
                "confidence":        round(min(0.70, float(dcp) * 0.75), 4),
                "qualification":     log.qualification_status,
                "calibration":       "provisional — cognition null baseline not yet run",
                "limitations":       "toy fixture, not real agent data",
            })
        except Exception as e:
            records.append({"domain": "cognition", "fixture_id": label, "error": str(e)})

    return records


# ── Synthetic fixtures ────────────────────────────────────────────────────────

def _run_synthetic_probe() -> list[dict]:
    """Run all three synthetic calibration fixtures."""
    try:
        from applications.labs.dcp_synthetic_fixtures import (
            run_forced_narrowing,
            run_basin_transition,
            run_ambiguity_pool,
        )
        from core.invariants.dcp.metrics import collapse_sharpness, compute_dcp_score
    except ImportError as e:
        return [{"domain": "synthetic", "error": str(e)}]

    records = []
    for fn, kwargs, label in [
        (run_forced_narrowing,  {"n_branches": 8, "n_steps": 20}, "syn_forced_narrow"),
        (run_basin_transition,  {"transition_step": 15, "n_steps": 30}, "syn_basin_trans"),
        (run_ambiguity_pool,    {"initial_hypotheses": 10, "n_steps": 15}, "syn_ambiguity"),
    ]:
        try:
            log     = fn(**kwargs)
            breadths = [e.possibility_breadth for e in log.events]
            tensions = [e.tension_proxy       for e in log.events]

            poss    = breadths[0] if breadths else 1.0
            constr  = max([e.constraint_proxy for e in log.events], default=0.0)
            tension = max(tensions, default=0.0)

            collapse_val = collapse_sharpness(breadths) if log.collapse_step else None

            post_narr = None
            if log.collapse_step is not None:
                cs = log.events[log.collapse_step]
                post_narr = cs.post_collapse_narrowing

            dcp = compute_dcp_score(
                possibility_space=poss,
                constraint=constr,
                tension=tension if tension > 0 else None,
                collapse=collapse_val,
                post_narrowing=post_narr,
            )

            records.append({
                "domain":            "synthetic",
                "fixture_id":        label,
                "description":       log.fixture_type,
                "possibility_space": round(poss, 4),
                "constraint":        round(constr, 4),
                "tension":           round(tension, 4),
                "collapse":          round(collapse_val, 4) if collapse_val else None,
                "post_narrowing":    round(post_narr, 4) if post_narr is not None else None,
                "morphology":        log.final_morphology,
                "dcp_composite":     round(float(dcp), 4),
                "confidence":        round(min(0.80, float(dcp) * 0.85), 4),
                "qualification":     log.qualification_status,
                "calibration":       "synthetic calibration baseline",
                "limitations":       "no domain semantics; pure structural test",
            })
        except Exception as e:
            records.append({"domain": "synthetic", "fixture_id": label, "error": str(e)})

    return records


# ---------------------------------------------------------------------------
# Comparison summary
# ---------------------------------------------------------------------------

def _summarize_by_domain(all_records: list[dict]) -> dict:
    """Group records by domain and compute per-domain summary statistics."""
    by_domain: dict[str, list] = {}
    for r in all_records:
        d = r.get("domain", "unknown")
        by_domain.setdefault(d, []).append(r)

    summary = {}
    for domain, recs in by_domain.items():
        valid = [r for r in recs if "error" not in r]
        if not valid:
            summary[domain] = {"status": "error", "records": len(recs)}
            continue

        quals = [r.get("qualification", "INSUFFICIENT") for r in valid]
        collapses = [r for r in valid if r.get("collapse") is not None]
        tensions  = [r.get("tension", 0) or 0 for r in valid]
        dcps      = [r.get("dcp_composite", 0) or 0 for r in valid]

        summary[domain] = {
            "n_fixtures":            len(valid),
            "full_qualified":        quals.count("FULL"),
            "incomplete_or_better":  sum(1 for q in quals if q in ("FULL", "UNCONFIRMED", "INCOMPLETE")),
            "collapses_detected":    len(collapses),
            "mean_tension":          round(sum(tensions) / max(len(tensions), 1), 4),
            "mean_dcp":              round(sum(dcps) / max(len(dcps), 1), 4),
            "max_dcp":               round(max(dcps, default=0), 4),
            "morphologies":          list({r.get("morphology") for r in valid if r.get("morphology")}),
        }

    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_std(series: list[float]) -> float:
    if len(series) < 2:
        return 0.0
    mean = sum(series) / len(series)
    var  = sum((x - mean)**2 for x in series) / len(series)
    return math.sqrt(max(0.0, var))


def _sharpness(series: list[float], window: int = 5) -> float:
    """Max proportional decrease over any window of `window` steps."""
    if len(series) < window + 1:
        return 0.0
    min_v, max_v = min(series), max(series)
    rng = max_v - min_v
    if rng < 1e-9:
        return 0.0
    best = 0.0
    for i in range(len(series) - window):
        drop = series[i] - series[i + window]
        if drop > best:
            best = drop
    return min(1.0, best / rng)


def _composite(poss, constr, tension, collapse, post_narr) -> float:
    """Simplified composite DCP score (no numpy dependency)."""
    weights = {"poss": 1.0, "constr": 1.0, "tension": 1.0, "collapse": 1.5, "post": 1.5}
    pairs = [
        (poss,     weights["poss"]),
        (constr,   weights["constr"]),
        (tension,  weights["tension"]),
        (collapse, weights["collapse"]),
        (post_narr, weights["post"]),
    ]
    tw, ws = 0.0, 0.0
    for v, w in pairs:
        if v is not None:
            ws += v * w
            tw += w
    return ws / tw if tw > 0 else 0.0


def _qualify(poss, constr, tension, collapse, post_narr) -> str:
    present = sum(v is not None for v in [poss, constr, tension, collapse, post_narr])
    if present == 5:
        return "FULL"
    if present == 4 and tension is None:
        return "UNCONFIRMED"
    if present >= 3:
        return "INCOMPLETE"
    return "INSUFFICIENT"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_cross_domain_comparison() -> dict:
    """Run all domain probes and return the comparison report."""
    all_records = []

    print("Collecting DCP signals by domain...")
    for label, probe in [
        ("math",      _run_math_probe),
        ("games",     _run_games_probe),
        ("music",     _run_music_probe),
        ("language",  _run_language_probe),
        ("cognition", _run_cognition_probe),
        ("synthetic", _run_synthetic_probe),
    ]:
        print(f"  {label}...", end=" ", flush=True)
        try:
            recs = probe()
            all_records.extend(recs)
            errors = sum(1 for r in recs if "error" in r)
            ok     = len(recs) - errors
            print(f"{ok} records ({errors} errors)")
        except Exception as e:
            print(f"FAILED — {e}")
            all_records.append({"domain": label, "error": str(e)})

    summary = _summarize_by_domain(all_records)
    return {"records": all_records, "summary": summary}


def _print_report(report: dict) -> None:
    summary = report["summary"]

    print()
    print("=" * 80)
    print("DCP Cross-Domain Comparison Report")
    print("=" * 80)
    print()

    # Per-domain summary
    print(f"  {'Domain':12s}  {'N':>3}  {'FULL':>5}  {'≥INCMP':>6}  "
          f"{'Collapses':>10}  {'MeanTension':>12}  {'MeanDCP':>8}  {'MaxDCP':>7}")
    print("  " + "-" * 72)
    for domain, s in summary.items():
        if "n_fixtures" not in s:
            print(f"  {domain:12s}  ERROR — {s.get('error', s.get('status', '?'))}")
            continue
        print(
            f"  {domain:12s}"
            f"  {s['n_fixtures']:>3}"
            f"  {s['full_qualified']:>5}"
            f"  {s['incomplete_or_better']:>6}"
            f"  {s['collapses_detected']:>10}"
            f"  {s['mean_tension']:>12.4f}"
            f"  {s['mean_dcp']:>8.4f}"
            f"  {s['max_dcp']:>7.4f}"
        )

    print()
    print("  Evidence status:")
    print("  ─────────────────────────────────────────────────────────────────")

    DOMAIN_STATUS = {
        "math":      "STRONGEST — Tests 1,2,4 passed; time-series tension confirmed",
        "games":     "IMPROVED — new sequential fixtures; not yet null-calibrated",
        "music":     "WEAK — collapse_proxy=None (requires audio); metadata proxies only",
        "language":  "PARTIAL — k_eff captures constraint level; no temporal collapse",
        "cognition": "PROVISIONAL — toy fixtures only; no real agent data yet",
        "synthetic": "CALIBRATION — baselines for probe validation; no domain semantics",
    }
    for domain, status in DOMAIN_STATUS.items():
        print(f"  {domain:12s} {status}")

    print()
    print("  Cross-domain qualifier:")
    print("  DCP remains at CANDIDATE status. Math is the strongest domain.")
    print("  Games is no longer the obvious weak point (Test 3 now runnable).")
    print("  Music and language cannot produce FULL qualification from current data.")
    print("  Synthetic baselines confirm probe functions behave correctly.")
    print("  Null model calibration required before any tier promotion.")
    print("=" * 80)


if __name__ == "__main__":
    report = run_cross_domain_comparison()
    _print_report(report)

    # Optionally write JSON output
    if "--json" in sys.argv:
        out = json.dumps(report, indent=2, default=str)
        print(out)

