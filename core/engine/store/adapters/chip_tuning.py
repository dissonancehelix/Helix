"""
chip_tuning.py — R2: Pitch Discretization Error Tables
=======================================================
Computes the cents deviation from 12-TET for every MIDI note (0–127) on each
PSG-family chip. The result is a per-chip intonation fingerprint: a 128-element
vector of signed cent errors showing how far the closest achievable period lands
from true equal temperament.

This is a Diophantine approximation problem: given a target frequency
f_target = 440 * 2^((n-69)/12), find the integer period p minimising
|f(p) - f_target|, then compute cents_error = 1200 * log2(f(p) / f_target).

Run directly to produce JSON artifact and console summary:
    python core/adapters/chip_tuning.py [--out <path>]

Output JSON schema:
    {
        "chips": {
            "<chip_id>": {
                "description": str,
                "clock_hz": int,
                "period_bits": int,
                "period_min": int,
                "period_max": int,
                "freq_formula": str,
                "tuning_errors_cents": [float * 128],  # MIDI notes 0-127
                "mean_abs_error_cents": float,
                "max_abs_error_cents": float,
                "notes_within_5_cents": int,   # out of 128
                "notes_within_10_cents": int,
                "dead_notes": int,             # MIDI notes with no reachable period
            }
        },
        "comparison": {
            "<chip_a>_vs_<chip_b>": {
                "rms_diff_cents": float,       # RMS of (error_a - error_b)
            }
        }
    }
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Chip definitions
# ---------------------------------------------------------------------------
# Each entry: (description, clock_hz, period_bits, period_min, f_of_period)
# f_of_period: callable(period: int) -> float Hz

_INF = float("inf")


def _nes_pulse_f(period: int) -> float:
    return 1_789_773 / (16 * (period + 1))


def _nes_triangle_f(period: int) -> float:
    return 1_789_773 / (32 * (period + 1))


def _sn76489_f(period: int) -> float:
    if period == 0:
        return _INF
    return 3_579_545 / (32 * period)


def _ay_f(clock: int) -> Callable[[int], float]:
    def _f(period: int) -> float:
        if period == 0:
            return _INF
        return clock / (16 * period)
    return _f


def _gb_f(period: int) -> float:
    denom = 2048 - period
    if denom <= 0:
        return _INF
    return 131_072 / denom


CHIPS: dict[str, dict] = {
    "nes_pulse": {
        "description": "NES APU Pulse (2A03 NTSC)",
        "clock_hz":    1_789_773,
        "period_bits": 11,
        "period_min":  0,
        "period_max":  2047,
        "freq_formula": "1789773 / (16 * (period + 1))",
        "f": _nes_pulse_f,
    },
    "nes_triangle": {
        "description": "NES APU Triangle (2A03 NTSC)",
        "clock_hz":    1_789_773,
        "period_bits": 11,
        "period_min":  0,
        "period_max":  2047,
        "freq_formula": "1789773 / (32 * (period + 1))",
        "f": _nes_triangle_f,
    },
    "sn76489_genesis": {
        "description": "SN76489 / Sega Genesis (3.579 MHz)",
        "clock_hz":    3_579_545,
        "period_bits": 10,
        "period_min":  1,
        "period_max":  1023,
        "freq_formula": "3579545 / (32 * period)",
        "f": _sn76489_f,
    },
    "ay_zx_spectrum": {
        "description": "AY-3-8910 / ZX Spectrum (1.7734 MHz)",
        "clock_hz":    1_773_400,
        "period_bits": 12,
        "period_min":  1,
        "period_max":  4095,
        "freq_formula": "1773400 / (16 * period)",
        "f": _ay_f(1_773_400),
    },
    "ay_atari_st": {
        "description": "YM2149 / Atari ST (2.0 MHz)",
        "clock_hz":    2_000_000,
        "period_bits": 12,
        "period_min":  1,
        "period_max":  4095,
        "freq_formula": "2000000 / (16 * period)",
        "f": _ay_f(2_000_000),
    },
    "ay_msx": {
        "description": "AY-3-8910 / MSX (1.7897 MHz — CPU/2)",
        "clock_hz":    1_789_773,
        "period_bits": 12,
        "period_min":  1,
        "period_max":  4095,
        "freq_formula": "1789773 / (16 * period)",
        "f": _ay_f(1_789_773),
    },
    "gb_dmg": {
        "description": "Game Boy DMG APU Pulse/Wave (4.194 MHz master)",
        "clock_hz":    4_194_304,
        "period_bits": 11,
        "period_min":  0,
        "period_max":  2047,
        "freq_formula": "131072 / (2048 - period)",
        "f": _gb_f,
    },
}

# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

_A4_HZ = 440.0


def midi_to_hz(note: int) -> float:
    return _A4_HZ * (2 ** ((note - 69) / 12))


def hz_to_cents_error(achieved: float, target: float) -> float | None:
    """Cents deviation of achieved from target. None if achieved is inf/0."""
    if achieved <= 0 or achieved == _INF or target <= 0:
        return None
    return 1200.0 * math.log2(achieved / target)


def best_period(target_hz: float, p_min: int, p_max: int,
                f: Callable[[int], float]) -> tuple[int, float]:
    """
    Find the integer period in [p_min, p_max] whose frequency is closest
    to target_hz. Returns (period, achieved_hz).

    Works for both monotone-decreasing (PSG: larger period → lower freq) and
    monotone-increasing (Game Boy: larger period → higher freq) functions.
    Detects direction from f(p_min) vs f(p_max) and adjusts binary search.
    """
    if p_min > p_max:
        return p_min, f(p_min)

    f_lo = f(p_min)
    f_hi = f(p_max)
    increasing = (f_hi > f_lo)   # GB is increasing; PSG/NES are decreasing

    lo, hi = p_min, p_max
    while lo < hi:
        mid = (lo + hi) // 2
        f_mid = f(mid)
        if increasing:
            # find smallest p where f(p) >= target
            if f_mid < target_hz:
                lo = mid + 1
            else:
                hi = mid
        else:
            # find smallest p where f(p) <= target (decreasing)
            if f_mid > target_hz:
                lo = mid + 1
            else:
                hi = mid

    candidates = []
    for p in (max(p_min, lo - 1), lo, min(p_max, lo + 1)):
        freq = f(p)
        if 0 < freq < _INF:
            candidates.append((p, freq))

    if not candidates:
        return lo, _INF

    return min(candidates, key=lambda x: abs(x[1] - target_hz))


def compute_chip_tuning(chip_id: str) -> dict:
    chip = CHIPS[chip_id]
    f        = chip["f"]
    p_min    = chip["period_min"]
    p_max    = chip["period_max"]

    errors: list[float | None] = []
    for note in range(128):
        target  = midi_to_hz(note)
        _, achieved = best_period(target, p_min, p_max, f)
        errors.append(hz_to_cents_error(achieved, target))

    valid_errors = [e for e in errors if e is not None]
    abs_errors   = [abs(e) for e in valid_errors]
    dead_notes   = errors.count(None)

    return {
        "description":        chip["description"],
        "clock_hz":           chip["clock_hz"],
        "period_bits":        chip["period_bits"],
        "period_min":         p_min,
        "period_max":         p_max,
        "freq_formula":       chip["freq_formula"],
        "tuning_errors_cents": [round(e, 4) if e is not None else None
                                for e in errors],
        "mean_abs_error_cents": round(sum(abs_errors) / len(abs_errors), 4)
                                if abs_errors else None,
        "max_abs_error_cents":  round(max(abs_errors), 4) if abs_errors else None,
        "notes_within_5_cents":  sum(1 for e in abs_errors if e <= 5.0),
        "notes_within_10_cents": sum(1 for e in abs_errors if e <= 10.0),
        "dead_notes":            dead_notes,
    }


def compute_all() -> dict:
    chips_out: dict[str, dict] = {}
    for chip_id in CHIPS:
        chips_out[chip_id] = compute_chip_tuning(chip_id)

    # Pairwise RMS difference between tuning error vectors
    ids = list(CHIPS.keys())
    comparison: dict[str, dict] = {}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            errs_a = chips_out[a]["tuning_errors_cents"]
            errs_b = chips_out[b]["tuning_errors_cents"]
            diffs = [
                (ea - eb) ** 2
                for ea, eb in zip(errs_a, errs_b)
                if ea is not None and eb is not None
            ]
            rms = math.sqrt(sum(diffs) / len(diffs)) if diffs else None
            comparison[f"{a}_vs_{b}"] = {
                "rms_diff_cents": round(rms, 4) if rms is not None else None
            }

    return {"chips": chips_out, "comparison": comparison}


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def print_summary(result: dict) -> None:
    chips = result["chips"]
    print("\n=== Chip Pitch Discretization Error (R2) ===\n")
    print(f"{'Chip':<22} {'Mean |err|':>10} {'Max |err|':>10} "
          f"{'≤5¢':>5} {'≤10¢':>6} {'Dead':>5}")
    print("-" * 64)
    for chip_id, d in chips.items():
        print(f"{chip_id:<22} "
              f"{d['mean_abs_error_cents']:>10.2f} "
              f"{d['max_abs_error_cents']:>10.2f} "
              f"{d['notes_within_5_cents']:>5} "
              f"{d['notes_within_10_cents']:>6} "
              f"{d['dead_notes']:>5}")

    print("\n=== Pairwise RMS Difference (cents) — most similar pairs ===\n")
    pairs = sorted(
        result["comparison"].items(),
        key=lambda x: x[1]["rms_diff_cents"] or 999
    )
    for key, val in pairs[:6]:
        a, _, b = key.partition("_vs_")
        print(f"  {a:<22} vs {b:<22}  {val['rms_diff_cents']:>7.3f} ¢ RMS")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute chip tuning error tables (R2)")
    parser.add_argument("--out", default=None,
                        help="JSON output path (default: core/adapters/chip_tuning_tables.json)")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else Path(__file__).parents[1] / "library" / "reference" / "audio" / "chip_tuning_tables.json"

    result = compute_all()
    print_summary(result)

    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nArtifact written: {out_path}")
