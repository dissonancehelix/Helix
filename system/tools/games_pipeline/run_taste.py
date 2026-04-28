"""
Games taste model runner.

Usage:
    python -m system.tools.games_pipeline.run_taste

Stages:
  1. Load raw Steam library
  2. Enrich with SteamSpy tags (cached after first run)
  3. Build taste profile
  4. Fetch candidate games from SteamSpy
  5. Score and print recommendations
"""
import argparse
import json
from pathlib import Path

from system.tools.games_pipeline.steamspy_client import enrich_library, get_all_games, get_app_details

from labs.research.games.taste_model import (
    build_taste_profile, recommend, save_profile,
    top_profile_tags
)

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "derived" / "games_pipeline"
RAW_LIBRARY = ROOT / "data" / "raw" / "games" / "data_steam_raw.json"
ENRICHED_PATH = DATA_DIR / "steam_enriched.json"
PROFILE_PATH  = DATA_DIR / "taste_profile.json"
OVERRIDES_PATH = DATA_DIR / "taste_overrides.json"


def load_raw_library() -> list[dict]:
    with open(RAW_LIBRARY, encoding="utf-8") as f:
        return json.load(f)


def load_overrides() -> dict:
    if OVERRIDES_PATH.exists():
        with open(OVERRIDES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def stage_enrich(library: list[dict], overrides: dict) -> list[dict]:
    if ENRICHED_PATH.exists():
        print(f"[enrich] Loading cached enriched library from {ENRICHED_PATH}")
        with open(ENRICHED_PATH, encoding="utf-8") as f:
            return json.load(f)

    n_played = sum(1 for g in library if g.get("playtime_forever_min", 0) > 0)
    print(f"[enrich] Fetching SteamSpy tags for {n_played} played games...")
    print("  (This takes ~6 minutes on first run — cached after that)")
    subs = overrides.get("substitute", {})
    if subs:
        print(f"  Substitutions: {len(subs)}")
        for src, dst in subs.items():
            print(f"    appid {src} → tags from appid {dst}")
    enriched = enrich_library(library, overrides=overrides)

    # inject manual anchor games
    manual = overrides.get("manual_games", [])
    if manual:
        print(f"\n[enrich] Injecting {len(manual)} manual taste anchors...")
        owned_appids = {str(g["appid"]) for g in library}
        for entry in manual:
            appid = str(entry["appid"])
            hours = entry.get("playtime_hours_equivalent", 100)
            print(f"  {entry['name']} ({hours}h equivalent)")
            details = get_app_details(appid)
            enriched.append({
                "appid": appid,
                "name": entry["name"],
                "playtime_forever_min": int(hours * 60),
                "playtime_2weeks_min": 0,
                "last_played": None,
                "tags": details.get("tags", {}),
                "tags_source_appid": appid,
                "review_ratio": None,
                "total_reviews": 0,
                "genre": details.get("genre", ""),
                "developer": details.get("developer", ""),
                "publisher": details.get("publisher", ""),
                "manual_anchor": True,
            })

    with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)
    print(f"[enrich] Saved → {ENRICHED_PATH}")
    return enriched


def stage_profile(enriched: list[dict]) -> dict:
    print("[profile] Building taste profile...")
    profile = build_taste_profile(enriched)
    save_profile(profile, PROFILE_PATH)

    print("\n── Top 20 taste tags ──────────────────────")
    for tag, weight in top_profile_tags(profile, 20):
        bar = "█" * int(weight * 500)
        print(f"  {tag:<35} {weight:.4f}  {bar}")
    return profile


def stage_candidates(owned_appids: set) -> list[dict]:
    print("\n[candidates] Fetching SteamSpy game catalog (pages 0-4)...")
    candidates = []
    seen = set()
    for page in range(5):
        page_data = get_all_games(page)
        for appid, game in page_data.items():
            if appid not in seen and appid not in owned_appids:
                seen.add(appid)
                # get_all_games returns minimal data — fetch full tags for scoring
                # We do this lazily: only for games that pass the basic review filter
                positive = game.get("positive", 0)
                negative = game.get("negative", 0)
                total = positive + negative
                if total >= 500 and (positive / total) >= 0.70:
                    details = get_app_details(appid)
                    candidates.append({**game, **details, "appid": appid})
        print(f"  Page {page}: {len(page_data)} games, {len(candidates)} candidates so far")
    return candidates


def stage_recommend(profile: dict, candidates: list[dict], owned_appids: set) -> None:
    print(f"\n[recommend] Scoring {len(candidates)} candidates...")
    recs = recommend(profile, candidates, owned_appids, top_n=30)

    print(f"\n{'═'*70}")
    print(f"  TOP GAME RECOMMENDATIONS FOR dissident93")
    print(f"{'═'*70}")
    for i, r in enumerate(recs, 1):
        price = f"${int(r['price'])//100:.0f}" if str(r.get('price','')).isdigit() else "?"
        ratio_pct = f"{r['review_ratio']*100:.0f}%"
        print(f"\n  {i:>2}. {r['name']}")
        print(f"      Score: {r['score']:.5f}  |  Reviews: {ratio_pct} pos ({r['total_reviews']:,})  |  Price: {price}")
        print(f"      Tags:  {', '.join(r['matching_tags'])}")
        print(f"      Genre: {r['genre']}  |  Dev: {r['developer']}")

    # save results
    out_path = DATA_DIR / "recommendations.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(recs, f, indent=2)
    print(f"\n[done] Full results → {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and score the games taste model.")
    parser.add_argument("--skip-candidates", action="store_true", help="Build/enrich the taste profile without fetching candidate games.")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    library   = load_raw_library()
    overrides = load_overrides()
    owned_appids = {str(g["appid"]) for g in library}

    enriched   = stage_enrich(library, overrides)
    profile    = stage_profile(enriched)
    if args.skip_candidates:
        return 0
    candidates = stage_candidates(owned_appids)
    stage_recommend(profile, candidates, owned_appids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

