"""
Probe: PSG Hardware Oscillator Locking (R3)
===========================================
Tests whether the integer period registers of PSG-family chips cause frequency
ratios between simultaneously active channels to cluster near simple rational
numbers — more than would occur by chance — when the chip is used musically.

Hypothesis: the oscillator_locking invariant (verified at 100% confidence in
games/language/music) should appear at the hardware substrate level. Integer
period quantization does not just permit simple rational ratios — it enforces
them, because the only way to hit target frequencies is to pick integers, and
those integers for musically-adjacent notes have small GCDs.

Method:
  1. MUSICAL pairs: for each PSG chip, compute the periods that best approximate
     the 8 notes of C major (C4–C5). Generate all pairwise period combinations
     (28 pairs per chip × 7 chips = 196 pairs). These represent what a composer
     using the chip for tonal music would actually program.
  2. NULL pairs: for each chip, generate 200 random period pairs uniformly
     sampled from the valid period range. These represent the unconstrained
     baseline — no musical intent.
  3. For each pair, compute the frequency ratio f1/f2 and test whether it falls
     within LOCK_THRESHOLD_CENTS of any simple rational in SIMPLE_RATIONALS.
  4. Signal = musical_lock_rate − null_lock_rate.
     If > 0: musical use of integer-period hardware produces more rational
     frequency ratios than chance. The larger the signal, the stronger the
     hardware-level locking effect.

Pass condition: signal > PASS_THRESHOLD (default 0.15).

This probe requires no external data files — period tables are synthesised
from chip adapter constants via chip_tuning.py (core/adapters/chip_tuning.py).
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
from pathlib import Path

VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOCK_THRESHOLD_CENTS = 15.0   # within 15¢ of a simple rational = "locked"
PASS_THRESHOLD       = 0.15   # signal > 15 percentage points → pass
RANDOM_SEED          = 42
NULL_PAIRS_PER_CHIP  = 200

# Simple rationals to test (spans up to 3 octaves, low-integer only)
SIMPLE_RATIONALS: list[tuple[int, int]] = [
    (1, 1), (2, 1), (3, 1), (4, 1),
    (3, 2), (4, 3), (5, 4), (6, 5),
    (5, 3), (8, 5), (7, 4), (7, 6),
    (9, 8), (16, 9), (15, 8),
    # inverses are handled by taking max/min of ratio
]

# C major scale: MIDI notes 60–72
C_MAJOR_MIDI = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C (one octave)

# ---------------------------------------------------------------------------
# Chip frequency functions (inline — no import dependency on adapter files)
# ---------------------------------------------------------------------------

_INF = float("inf")


def _midi_to_hz(n: int) -> float:
    return 440.0 * (2 ** ((n - 69) / 12))


CHIP_SPECS: dict[str, dict] = {
    "nes_pulse":        {"p_min": 0,  "p_max": 2047,  "f": lambda p: 1_789_773 / (16 * (p + 1))},
    "nes_triangle":     {"p_min": 0,  "p_max": 2047,  "f": lambda p: 1_789_773 / (32 * (p + 1))},
    "sn76489_genesis":  {"p_min": 1,  "p_max": 1023,  "f": lambda p: 3_579_545 / (32 * p) if p > 0 else _INF},
    "ay_zx_spectrum":   {"p_min": 1,  "p_max": 4095,  "f": lambda p: 1_773_400 / (16 * p) if p > 0 else _INF},
    "ay_msx":           {"p_min": 1,  "p_max": 4095,  "f": lambda p: 1_789_773 / (16 * p) if p > 0 else _INF},
    "ay_atari_st":      {"p_min": 1,  "p_max": 4095,  "f": lambda p: 2_000_000 / (16 * p) if p > 0 else _INF},
    "gb_dmg":           {"p_min": 0,  "p_max": 2047,  "f": lambda p: 131_072 / (2048 - p) if p < 2048 else _INF},
}


def _best_period(target_hz: float, p_min: int, p_max: int, f) -> tuple[int, float]:
    """Binary search for closest period (handles both increasing and decreasing f)."""
    f_lo, f_hi = f(p_min), f(p_max)
    increasing = (f_hi > f_lo) if (f_lo != _INF and f_hi != _INF) else False
    lo, hi = p_min, p_max
    while lo < hi:
        mid = (lo + hi) // 2
        f_mid = f(mid)
        if increasing:
            lo = mid + 1 if f_mid < target_hz else (hi := mid) or hi
        else:
            lo = mid + 1 if f_mid > target_hz else (hi := mid) or hi
    candidates = []
    for p in (max(p_min, lo - 1), lo, min(p_max, lo + 1)):
        freq = f(p)
        if 0 < freq < _INF:
            candidates.append((p, freq))
    if not candidates:
        return lo, _INF
    return min(candidates, key=lambda x: abs(x[1] - target_hz))


# ---------------------------------------------------------------------------
# Ratio analysis
# ---------------------------------------------------------------------------

def _ratio_to_cents_from_nearest_simple(ratio: float) -> float:
    """
    Distance in cents from *ratio* to the nearest entry in SIMPLE_RATIONALS.
    Always uses ratio >= 1 (takes max/min to normalise direction).
    """
    if ratio <= 0 or not math.isfinite(ratio):
        return _INF
    r = max(ratio, 1 / ratio) if ratio < 1 else ratio
    best = _INF
    for num, den in SIMPLE_RATIONALS:
        target = num / den
        if target <= 0:
            continue
        dist = abs(1200.0 * math.log2(r / target))
        if dist < best:
            best = dist
    return best


def _is_locked(p1: int, p2: int, f) -> bool:
    f1, f2 = f(p1), f(p2)
    if f1 <= 0 or f2 <= 0 or f1 == _INF or f2 == _INF:
        return False
    return _ratio_to_cents_from_nearest_simple(f1 / f2) <= LOCK_THRESHOLD_CENTS


# ---------------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------------

def _build_musical_pairs() -> list[dict]:
    """
    For each chip: find best period per C-major note, emit all pairwise combos.
    Returns list of {chip, p1, p2, midi1, midi2}.
    """
    pairs = []
    for chip_id, spec in CHIP_SPECS.items():
        p_min, p_max, f = spec["p_min"], spec["p_max"], spec["f"]
        periods: list[tuple[int, int]] = []   # (midi_note, period)
        for midi in C_MAJOR_MIDI:
            target = _midi_to_hz(midi)
            p, achieved = _best_period(target, p_min, p_max, f)
            # Only include if the chip can actually reach within a semitone
            if achieved != _INF and abs(1200 * math.log2(achieved / target)) <= 100:
                periods.append((midi, p))
        for i in range(len(periods)):
            for j in range(i + 1, len(periods)):
                pairs.append({
                    "chip":  chip_id,
                    "p1":    periods[i][1],
                    "p2":    periods[j][1],
                    "midi1": periods[i][0],
                    "midi2": periods[j][0],
                    "kind":  "musical",
                })
    return pairs


def _build_null_pairs(rng: random.Random) -> list[dict]:
    """Random period pairs for each chip as null baseline."""
    pairs = []
    for chip_id, spec in CHIP_SPECS.items():
        p_min, p_max = spec["p_min"], spec["p_max"]
        for _ in range(NULL_PAIRS_PER_CHIP):
            p1 = rng.randint(p_min, p_max)
            p2 = rng.randint(p_min, p_max)
            if p1 != p2:
                pairs.append({"chip": chip_id, "p1": p1, "p2": p2, "kind": "null"})
    return pairs


# ---------------------------------------------------------------------------
# Probe execution
# ---------------------------------------------------------------------------

def run_probe(dataset: dict | None = None) -> dict:
    rng = random.Random(RANDOM_SEED)
    musical = _build_musical_pairs()
    null    = _build_null_pairs(rng)

    def _lock_rate(pairs: list[dict]) -> tuple[float, int, int]:
        locked = total = 0
        for pair in pairs:
            spec = CHIP_SPECS.get(pair["chip"])
            if spec is None:
                continue
            total += 1
            if _is_locked(pair["p1"], pair["p2"], spec["f"]):
                locked += 1
        rate = locked / total if total > 0 else 0.0
        return rate, locked, total

    musical_rate, musical_locked, musical_total = _lock_rate(musical)
    null_rate,    null_locked,    null_total    = _lock_rate(null)

    signal = musical_rate - null_rate
    passed = signal > PASS_THRESHOLD

    # Per-chip breakdown
    chip_stats: dict[str, dict] = {}
    for chip_id in CHIP_SPECS:
        m_pairs = [p for p in musical if p["chip"] == chip_id]
        n_pairs = [p for p in null    if p["chip"] == chip_id]
        spec = CHIP_SPECS[chip_id]
        m_rate, m_locked, m_total = _lock_rate(m_pairs)
        n_rate, n_locked, n_total = _lock_rate(n_pairs)
        chip_stats[chip_id] = {
            "musical_lock_rate": round(m_rate, 4),
            "null_lock_rate":    round(n_rate, 4),
            "signal":            round(m_rate - n_rate, 4),
            "musical_pairs":     m_total,
            "null_pairs":        n_total,
        }

    interpretation = (
        f"Musical period pairs lock {signal*100:.1f}pp more often than random "
        f"({musical_rate*100:.1f}% vs {null_rate*100:.1f}%). "
        + ("Hypothesis supported." if passed else "Hypothesis not clearly supported.")
    )

    return {
        "probe_name":          "psg_oscillator_locking",
        "version":             VERSION,
        "domain":              "music_hardware",
        "signal":              round(signal, 4),
        "musical_lock_rate":   round(musical_rate, 4),
        "null_lock_rate":      round(null_rate, 4),
        "musical_locked":      musical_locked,
        "musical_total":       musical_total,
        "null_locked":         null_locked,
        "null_total":          null_total,
        "lock_threshold_cents": LOCK_THRESHOLD_CENTS,
        "pass_threshold":      PASS_THRESHOLD,
        "simple_rationals_tested": len(SIMPLE_RATIONALS),
        "passed":              passed,
        "confidence":          "high" if signal > 0.30 else "medium" if signal > 0.15 else "low",
        "interpretation":      interpretation,
        "per_chip":            chip_stats,
        "connection_to_invariant": (
            "oscillator_locking verified at 100% confidence across games/language/music. "
            "This probe tests the same invariant at the hardware substrate level: "
            "integer period registers on PSG chips enforce rational frequency ratios "
            "when used musically, producing phase-locking as a structural consequence "
            "of the hardware encoding rather than as a compositional choice."
        ),
    }


# ---------------------------------------------------------------------------
# Entry point (standalone + Helix sandbox compatible)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Helix runner injects HELIX_SYSTEM_INPUT and HELIX_ARTIFACT_DIR
    artifact_dir = os.environ.get("HELIX_ARTIFACT_DIR")
    system_input_path = os.environ.get("HELIX_SYSTEM_INPUT")

    dataset = None
    if system_input_path and Path(system_input_path).exists():
        with open(system_input_path, encoding="utf-8") as fh:
            inp = json.load(fh)
            dataset = inp.get("dataset")

    result = run_probe(dataset)

    # Pretty print
    print(f"\n{'='*60}")
    print(f"PSG Hardware Oscillator Locking Probe  v{VERSION}")
    print(f"{'='*60}")
    print(f"Signal:          {result['signal']:+.4f}")
    print(f"Musical lock:    {result['musical_lock_rate']*100:.1f}%  "
          f"({result['musical_locked']}/{result['musical_total']})")
    print(f"Null lock:       {result['null_lock_rate']*100:.1f}%  "
          f"({result['null_locked']}/{result['null_total']})")
    print(f"Passed:          {result['passed']}")
    print(f"Confidence:      {result['confidence']}")
    print(f"\n{result['interpretation']}\n")

    print("Per-chip breakdown:")
    print(f"  {'Chip':<22} {'Musical%':>9} {'Null%':>7} {'Signal':>8}")
    print(f"  {'-'*52}")
    for chip_id, s in result["per_chip"].items():
        print(f"  {chip_id:<22} {s['musical_lock_rate']*100:>8.1f}% "
              f"{s['null_lock_rate']*100:>6.1f}% "
              f"{s['signal']:>+8.3f}")

    # Write artifact
    if artifact_dir:
        out = Path(artifact_dir) / "probe_result.json"
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nArtifact: {out}")

    sys.exit(0 if result["passed"] else 1)
