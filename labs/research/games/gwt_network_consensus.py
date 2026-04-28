"""
model/domains/games/probes/gwt_network_consensus.py

Helix — Network Density → Consensus Speed (Wikipedia Talk Pages)

Tests the topology floor prediction in a real deliberation corpus:
  consensus speed (steps to converge) correlates with participant network
  density more than with individual "learning rate" (edit frequency).

Data source: Wikipedia Talk pages via the MediaWiki API (no auth required).
Focus: WT:NFL — active, long-running, high-participant threads with clear
consensus outcomes (article name changes, notability decisions, etc.)

Measures per thread:
  N         — number of unique participants
  edges     — reply pairs (i replied to j at least once) → network density
  density   — edges / (N*(N-1)/2)
  turns     — total number of posts (proxy for "steps to consensus")
  resolved  — bool: did the thread reach a stated outcome?

Prediction: turns_to_consensus ~ f(path_length) not f(edit_rate_per_user)
  i.e. dense networks converge faster per participant than sparse ones

Cross-reference: user Dissident93 included if present — real participation data.
"""

from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "Helix-Research/1.0 (cognition probe; academic use)"}

FOCUS_USER = "Dissident93"

# Talk pages to sample — WT:NFL archive index + a few specific high-activity pages
TALK_PAGES = [
    "Wikipedia talk:WikiProject National Football League",
    "Wikipedia talk:WikiProject National Football League/Archive 1",
    "Wikipedia talk:WikiProject National Football League/Archive 2",
    "Wikipedia talk:WikiProject National Football League/Archive 3",
    "Wikipedia talk:WikiProject National Football League/Archive 4",
    "Wikipedia talk:WikiProject National Football League/Archive 5",
    "Talk:Washington Commanders/Archive 1",
    "Talk:Washington Commanders/Archive 2",
    "Talk:National Football League/Archive 1",
    "Talk:National Football League/Archive 2",
    "Talk:Dallas Cowboys/Archive 1",
    "Talk:Kansas City Chiefs/Archive 1",
    "Talk:Super Bowl LVIII",
]


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _api_get(params: dict) -> dict:
    params["format"] = "json"
    url = API + "?" + urlencode(params)
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        return {"error": str(e)}


def _get_page_revisions(title: str, limit: int = 50) -> list[dict]:
    """Fetch recent revisions with user and timestamp."""
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "user|timestamp|comment|size",
        "rvlimit": limit,
    }
    data = _api_get(params)
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        return page.get("revisions", [])
    return []


def _get_page_content(title: str) -> str:
    """Fetch raw wikitext of a talk page."""
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvslots": "main",
        "rvlimit": 1,
    }
    data = _api_get(params)
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        revs = page.get("revisions", [])
        if revs:
            slots = revs[0].get("slots", {})
            return slots.get("main", {}).get("*", "")
    return ""


def _get_user_contributions(username: str, titles: list[str], limit: int = 100) -> list[dict]:
    """Get contributions by a specific user to specific pages."""
    params = {
        "action": "query",
        "list": "usercontribs",
        "ucuser": username,
        "uclimit": limit,
        "ucprop": "title|timestamp|comment|size",
        "ucnamespace": "1",     # Talk namespace only (4 = Wikipedia talk, needs separate call)
    }
    data = _api_get(params)
    contribs = data.get("query", {}).get("usercontribs", [])
    title_set = {t.lower() for t in titles}
    return [c for c in contribs if c.get("title", "").lower() in title_set]


# ---------------------------------------------------------------------------
# Thread parsing
# ---------------------------------------------------------------------------

_SIG_RE = re.compile(r"\[\[User(?:_talk)?:([^\]|]+)", re.IGNORECASE)
_SECTION_RE = re.compile(r"^==+\s*(.+?)\s*==+\s*$", re.MULTILINE)
_INDENT_RE = re.compile(r"^(:+)", re.MULTILINE)


def _extract_threads(wikitext: str) -> list[dict]:
    """
    Split wikitext into discussion threads by == section ==.
    For each thread extract:
      - participants (from [[User: signatures)
      - reply indentation levels (proxy for reply-to structure)
      - total posts
    """
    sections = _SECTION_RE.split(wikitext)
    threads = []

    # sections alternates: [preamble, title, body, title, body, ...]
    i = 1
    while i < len(sections) - 1:
        title = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""
        i += 2

        users = list(dict.fromkeys(  # preserve order, deduplicate
            m.group(1).strip().replace("_", " ")
            for m in _SIG_RE.finditer(body)
        ))

        # Build reply graph from indentation transitions
        lines = body.split("\n")
        prev_user = None
        prev_indent = 0
        edges: set[tuple[str, str]] = set()
        current_user = None

        for line in lines:
            indent_m = _INDENT_RE.match(line)
            indent = len(indent_m.group(1)) if indent_m else 0
            sig_m = _SIG_RE.search(line)
            if sig_m:
                current_user = sig_m.group(1).strip().replace("_", " ")
                if indent > prev_indent and prev_user and current_user != prev_user:
                    edges.add((current_user, prev_user))
                prev_user = current_user
                prev_indent = indent

        n_participants = len(users)
        n_edges = len(edges)
        max_edges = n_participants * (n_participants - 1) / 2 if n_participants > 1 else 1
        density = n_edges / max_edges if max_edges > 0 else 0.0

        # Approximate path length from density (Erdos-Renyi approximation)
        if density > 0 and n_participants > 2:
            mean_degree = density * (n_participants - 1)
            if mean_degree > 1:
                path_length = math.log(n_participants) / math.log(mean_degree)
            else:
                path_length = n_participants  # near-disconnected
        else:
            path_length = None

        total_posts = sum(1 for line in lines if _SIG_RE.search(line))

        # Resolved heuristic: look for "Result:", "Closed:", "Consensus:" keywords
        resolved = bool(re.search(
            r"(result|closed|consensus|archiv|resolved|done)\s*[:\|]",
            body, re.IGNORECASE
        ))

        if n_participants >= 3 and total_posts >= 5:
            threads.append({
                "title":         title[:80],
                "n_participants": n_participants,
                "n_edges":        n_edges,
                "density":        round(density, 4),
                "path_length":    round(path_length, 3) if path_length else None,
                "total_posts":    total_posts,
                "resolved":       resolved,
                "participants":   users[:20],   # cap for JSON size
            })

    return threads


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def _linreg(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    if n < 3:
        return {"slope": None, "intercept": None, "r2": None}
    mx, my = sum(xs)/n, sum(ys)/n
    ss_xy = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    ss_xx = sum((x-mx)**2 for x in xs)
    ss_yy = sum((y-my)**2 for y in ys)
    if ss_xx < 1e-12 or ss_yy < 1e-12:
        return {"slope": None, "intercept": None, "r2": None}
    slope = ss_xy/ss_xx
    r2 = (ss_xy**2)/(ss_xx*ss_yy)
    return {"slope": round(slope,4), "intercept": round(my-slope*mx,4), "r2": round(r2,4)}


def analyze_threads(all_threads: list[dict]) -> dict:
    valid = [t for t in all_threads if t["path_length"] is not None and t["total_posts"] > 0]

    # Prediction: posts_per_participant (convergence cost) ~ path_length
    xs_L    = [t["path_length"]  for t in valid]
    xs_dens = [t["density"]      for t in valid]
    ys_ppp  = [t["total_posts"] / max(t["n_participants"], 1) for t in valid]

    fit_L    = _linreg(xs_L,    ys_ppp)
    fit_dens = _linreg(xs_dens, ys_ppp)

    # Density should have inverse relationship (higher density → lower cost)
    # So we expect fit_dens.slope < 0

    verdict = "insufficient data"
    if fit_L["r2"] is not None and fit_dens["r2"] is not None:
        topology_drives = fit_L["r2"] > 0.3
        density_inverse = (fit_dens["slope"] or 0) < 0
        if topology_drives and density_inverse:
            verdict = "supported — path length predicts convergence cost, density inversely related"
        elif topology_drives:
            verdict = "partial — path length correlates but density direction unexpected"
        else:
            verdict = "not supported — topology does not predict convergence cost in this corpus"

    return {
        "fit_posts_per_participant_vs_path_length": fit_L,
        "fit_posts_per_participant_vs_density":     fit_dens,
        "n_threads": len(valid),
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== Network Density → Consensus Speed (Wikipedia WT:NFL) ===\n")

    all_threads: list[dict] = []

    for page_title in TALK_PAGES:
        print(f"  Fetching: {page_title} ... ", end="", flush=True)
        content = _get_page_content(page_title)
        if not content:
            print("no content")
            continue

        threads = _extract_threads(content)
        print(f"{len(threads)} threads parsed")

        for t in threads:
            t["source_page"] = page_title
        all_threads.extend(threads)
        time.sleep(0.5)

    print(f"\n  Total threads: {len(all_threads)}")

    # Check for FOCUS_USER presence
    user_threads = [
        t for t in all_threads
        if FOCUS_USER.lower() in [p.lower() for p in t.get("participants", [])]
    ]
    print(f"  Threads with {FOCUS_USER}: {len(user_threads)}")

    # Also fetch user contributions directly
    print(f"\n  Fetching contributions for {FOCUS_USER} ...", end="", flush=True)
    contribs = _get_user_contributions(FOCUS_USER, TALK_PAGES)
    print(f" {len(contribs)} contributions found")

    user_profile = None
    if contribs:
        # Measure edit rate (posts per page) as proxy for individual "learning rate"
        from collections import Counter
        pages_edited = Counter(c["title"] for c in contribs)
        user_profile = {
            "username": FOCUS_USER,
            "total_contributions": len(contribs),
            "pages_edited": dict(pages_edited),
            "mean_posts_per_page": round(len(contribs) / max(len(pages_edited), 1), 2),
        }
        print(f"  {FOCUS_USER}: {len(contribs)} edits across {len(pages_edited)} pages")

    # Analysis
    result = analyze_threads(all_threads)
    print(f"\n--- Topology → consensus fit ---")
    f_L = result["fit_posts_per_participant_vs_path_length"]
    f_d = result["fit_posts_per_participant_vs_density"]
    print(f"  posts/participant vs path_length: slope={f_L['slope']}  R²={f_L['r2']}")
    print(f"  posts/participant vs density:     slope={f_d['slope']}  R²={f_d['r2']}")
    print(f"  Verdict: {result['verdict']}")

    # Top threads by participant count
    top = sorted(all_threads, key=lambda t: t["n_participants"], reverse=True)[:10]
    print(f"\n  Top threads by participant count:")
    for t in top:
        print(f"    [{t['n_participants']} users, {t['total_posts']} posts, density={t['density']:.3f}] {t['title']}")

    out = {
        "threads": all_threads,
        "analysis": result,
        "focus_user": user_profile,
        "top_threads": top,
    }
    dest = ARTIFACTS / "gwt_network_consensus.json"
    with open(dest, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()

