"""
domains/games/probes/gwt_llm_agent_profile.py

Helix — LLM Cognitive Profile via Belief Trajectory

Uses the Claude API to run structured Bayesian uncertainty tasks across multiple
turns. At each turn new evidence arrives and the model states its confidence
(0–100). The resulting trajectory is fitted with the logistic collapse model
and classified against the simulation's cognitive profiles.

Non-circular because Claude was not trained on Helix's profiles or thresholds.

Task structure:
  - 6 tasks, each with 8 sequential evidence turns
  - One "clean signal" version (evidence consistently points to truth)
  - One "adversarial" version (3 of 8 turns are false signals)
  - Model asked for confidence as a bare integer at each turn

Profile classification (from simulation):
  CONFORMIST:  k ≈ 200  (collapses immediately on first strong signal)
  SELECTIVE:   k ≈ 17   (slow accumulation, large pre-collapse window)
  PARANOID:    no collapse (refuses to commit even with strong evidence)
  IMPULSIVE:   k ≈ 50–100, high noise (volatile trajectory)

Prediction:
  Clean signal  → LLM should show CONFORMIST/SELECTIVE depending on task ambiguity
  Adversarial   → if LLM shows SELECTIVE profile, it should resist false signals;
                  if CONFORMIST, it should be moved by them
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

TASKS = [
    {
        "id": "urn_draws",
        "setup": (
            "There is an urn containing 100 balls. It is either URN-A (70 red, 30 blue) "
            "or URN-B (30 red, 70 blue). You do not know which. I will draw balls one at "
            "a time with replacement and tell you the colour. After each draw, state your "
            "confidence (0–100) that this is URN-A. Reply with only the integer."
        ),
        "clean":      ["Red", "Red", "Red", "Red", "Red", "Red", "Red", "Red"],
        "adversarial":["Red", "Blue", "Red", "Red", "Blue", "Red", "Red", "Red"],
        "truth": "URN-A",
    },
    {
        "id": "disease_test",
        "setup": (
            "A patient has either Disease X (prevalence 20%) or is healthy. "
            "A diagnostic test has 80% sensitivity and 90% specificity. "
            "I will give you sequential test results. After each, state your confidence "
            "(0–100) that the patient has Disease X. Reply with only the integer."
        ),
        "clean":      ["Positive", "Positive", "Positive", "Positive", "Positive", "Positive", "Positive", "Positive"],
        "adversarial":["Positive", "Negative", "Positive", "Positive", "Negative", "Positive", "Positive", "Positive"],
        "truth": "Disease X",
    },
    {
        "id": "eyewitness",
        "setup": (
            "A crime was committed by either Suspect A or Suspect B — one of them is "
            "certainly guilty. I will present eyewitness statements one at a time. "
            "After each, state your confidence (0–100) that Suspect A is guilty. "
            "Reply with only the integer."
        ),
        "clean": [
            "Witness 1 saw someone matching Suspect A's description near the scene.",
            "Witness 2 confirms the suspect had a distinctive scar — Suspect A has one.",
            "Witness 3 heard the suspect's voice; says it sounded like Suspect A.",
            "A receipt was found placing Suspect A near the scene at the right time.",
            "Suspect A's fingerprints were found on the door handle.",
            "Suspect A's phone pinged a cell tower at the crime location.",
            "A surveillance camera caught someone matching Suspect A's profile.",
            "Suspect A's alibi witness has retracted their statement.",
        ],
        "adversarial": [
            "Witness 1 saw someone matching Suspect A's description near the scene.",
            "Witness 2 says the suspect looked more like Suspect B.",
            "Witness 3 heard the suspect's voice; says it sounded like Suspect A.",
            "A receipt was found placing Suspect A near the scene at the right time.",
            "Suspect B's lawyer has produced a document suggesting Suspect A was framed.",
            "Suspect A's fingerprints were found on the door handle.",
            "Suspect A's phone pinged a cell tower at the crime location.",
            "Suspect A's alibi witness has retracted their statement.",
        ],
        "truth": "Suspect A",
    },
    {
        "id": "market_signal",
        "setup": (
            "A stock will either rise (>+5%) or fall (<-5%) by market close tomorrow. "
            "I will give you analyst signals one at a time. Each signal is from a "
            "different independent analyst. After each, state your confidence (0–100) "
            "that the stock will rise. Reply with only the integer."
        ),
        "clean":      ["BUY", "BUY", "BUY", "BUY", "BUY", "BUY", "BUY", "BUY"],
        "adversarial":["BUY", "BUY", "SELL", "BUY", "BUY", "SELL", "BUY", "BUY"],
        "truth": "RISE",
    },
    {
        "id": "authorship",
        "setup": (
            "An unsigned manuscript was written by either Author A or Author B. "
            "I will share stylometric features one at a time. After each, state your "
            "confidence (0–100) that Author A wrote it. Reply with only the integer."
        ),
        "clean": [
            "Average sentence length is 22 words — matches Author A's style exactly.",
            "The word 'perhaps' appears 3× more than in Author B's corpus.",
            "Em-dash frequency is 0.8 per page — Author A's signature tic.",
            "The manuscript uses Oxford commas consistently — Author A always does.",
            "Passive voice rate is 12% — within Author A's normal range.",
            "The chapter structure (7 parts, no prologue) matches Author A's three previous novels.",
            "Lexical diversity score of 0.71 — typical for Author A, high for Author B.",
            "A distinctive phrase appears that Author A used in a 1998 essay.",
        ],
        "adversarial": [
            "Average sentence length is 22 words — matches Author A's style exactly.",
            "The word 'perhaps' appears 3× more than in Author B's corpus.",
            "However, the comma splice frequency matches Author B more closely.",
            "The manuscript uses Oxford commas consistently — Author A always does.",
            "The opening paragraph structure is unlike anything Author A has published.",
            "Passive voice rate is 12% — within Author A's normal range.",
            "Lexical diversity score of 0.71 — typical for Author A, high for Author B.",
            "A distinctive phrase appears that Author A used in a 1998 essay.",
        ],
        "truth": "Author A",
    },
]


# ---------------------------------------------------------------------------
# Logistic fit
# ---------------------------------------------------------------------------

def _fit_logistic(series: list[float]) -> tuple[float, float, float]:
    """Returns (k, t0, R²)."""
    n = len(series)
    if n < 3:
        return 0.0, 0.5, 0.0
    ts = [i / (n - 1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 2.0:   # less than 2% total movement — no meaningful collapse
        return 0.0, 0.5, 0.0
    norm = [(v - mn) / (mx - mn) for v in series]

    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 75, 100, 150, 200]:
        for t0 in [i / 20 for i in range(21)]:
            ss = sum((y - 1.0 / (1.0 + math.exp(k * (t - t0)))) ** 2
                     for t, y in zip(ts, norm))
            if ss < best_ss:
                best_ss, best_k, best_t0 = ss, k, t0

    mean_y = sum(norm) / n
    ss_tot = sum((y - mean_y) ** 2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss / ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


def _classify_profile(k: float, trajectory: list[float]) -> str:
    """Classify against simulation profiles based on k and trajectory noise."""
    diffs = [abs(trajectory[i+1] - trajectory[i]) for i in range(len(trajectory)-1)]
    noise = sum(diffs) / len(diffs) if diffs else 0.0

    if k >= 100:
        return "CONFORMIST"
    elif k >= 40:
        return "IMPULSIVE" if noise > 8.0 else "DIPLOMAT"
    elif k >= 10:
        return "SELECTIVE"
    else:
        return "PARANOID"


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def _run_task(client, task: dict, condition: str, model: str = "claude-sonnet-4-6") -> dict:
    """
    Run one task (clean or adversarial) and return the confidence trajectory.
    condition: "clean" or "adversarial"
    """
    evidence_list = task[condition]
    messages = []
    trajectory: list[float] = []

    # Initial setup
    messages.append({"role": "user", "content": task["setup"]})
    resp = client.messages.create(
        model=model,
        max_tokens=10,
        messages=messages,
    )
    initial_text = resp.content[0].text.strip()
    messages.append({"role": "assistant", "content": initial_text})

    # Try to extract initial confidence
    try:
        conf = float("".join(c for c in initial_text if c.isdigit() or c == "."))
        if conf > 1.0:
            conf = min(conf, 100.0)
        trajectory.append(conf)
    except Exception:
        trajectory.append(50.0)   # neutral prior if model didn't give a number

    # Sequential evidence turns
    for evidence in evidence_list:
        messages.append({"role": "user", "content": evidence})
        resp = client.messages.create(
            model=model,
            max_tokens=10,
            messages=messages,
        )
        text = resp.content[0].text.strip()
        messages.append({"role": "assistant", "content": text})

        try:
            digits = "".join(c for c in text if c.isdigit() or c == ".")
            conf = float(digits) if digits else trajectory[-1]
            if conf > 100.0:
                conf = 100.0
        except Exception:
            conf = trajectory[-1]

        trajectory.append(conf)
        time.sleep(0.3)   # rate limit buffer

    k, t0, r2 = _fit_logistic(trajectory)
    profile = _classify_profile(k, trajectory)

    return {
        "task_id":    task["id"],
        "condition":  condition,
        "trajectory": [round(v, 1) for v in trajectory],
        "final_confidence": round(trajectory[-1], 1),
        "k":          round(k, 2),
        "t0":         round(t0, 3),
        "fit_r2":     round(r2, 3),
        "profile":    profile,
        "truth":      task["truth"],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        import anthropic
    except ImportError:
        print("anthropic SDK not installed — run: pip install anthropic")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        return

    client = anthropic.Anthropic(api_key=api_key)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    print("=== LLM Cognitive Profile via Belief Trajectory ===\n")
    all_results = []

    for task in TASKS:
        for condition in ["clean", "adversarial"]:
            print(f"  {task['id']} / {condition} ... ", end="", flush=True)
            try:
                r = _run_task(client, task, condition)
                all_results.append(r)
                traj_str = " → ".join(str(int(v)) for v in r["trajectory"])
                print(f"k={r['k']}  profile={r['profile']}  final={r['final_confidence']}%")
                print(f"    trajectory: {traj_str}")
            except Exception as e:
                print(f"ERROR: {e}")
                all_results.append({"task_id": task["id"], "condition": condition, "error": str(e)})

    # Summary
    valid = [r for r in all_results if "k" in r]
    if valid:
        by_cond: dict[str, list] = {"clean": [], "adversarial": []}
        for r in valid:
            by_cond[r["condition"]].append(r)

        print("\n--- Profile summary ---")
        for cond, rows in by_cond.items():
            if not rows:
                continue
            ks = [r["k"] for r in rows]
            profiles = [r["profile"] for r in rows]
            print(f"  {cond}: mean_k={round(sum(ks)/len(ks),1)}  profiles={profiles}")

        # Adversarial resistance: did final confidence stay high despite false signals?
        adv = [r for r in valid if r["condition"] == "adversarial"]
        if adv:
            mean_final = sum(r["final_confidence"] for r in adv) / len(adv)
            resistance = "high" if mean_final > 70 else "low"
            print(f"  Adversarial resistance: mean_final={round(mean_final,1)}%  ({resistance})")

    dest = ARTIFACTS / "gwt_llm_agent_profile.json"
    with open(dest, "w") as f:
        json.dump({"results": all_results}, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()
