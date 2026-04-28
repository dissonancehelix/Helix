"""
Operator taste model for games domain.

Builds a weighted tag profile from play history and scores candidate
games against it. Uses log(hours+1) weighting so outlier playtime
(e.g. Garry's Mod 3000h) doesn't completely erase the signal from
the 100-400h "completed engagement" tier.

Taste profile: dict of tag -> normalized weight
Score: dot product of candidate tag presence with taste profile,
       normalized by candidate tag count.
"""
import math
import json
from pathlib import Path
from typing import Optional

# Tags that are metadata noise, not taste signal
NOISE_TAGS = {
    "Singleplayer", "Multiplayer", "Steam Achievements", "Steam Cloud",
    "Steam Trading Cards", "Full controller support", "Partial Controller Support",
    "Co-op", "Online Co-Op", "Local Co-Op", "Local Multiplayer",
    "Cross-Platform Multiplayer", "Captions available", "Commentary available",
    "Steam Workshop", "Includes level editor", "Stats", "Leaderboards",
    "Remote Play on TV", "Remote Play on Phone", "Remote Play on Tablet",
    "Family Sharing", "Early Access",
}

# Minimum hours to treat a game as a taste signal
MIN_HOURS = 2.0


def build_taste_profile(enriched_library: list[dict]) -> dict[str, float]:
    """
    Build a weighted tag profile from the enriched library.
    Returns: {tag: normalized_weight}
    """
    tag_scores: dict[str, float] = {}

    for game in enriched_library:
        hours = game.get("playtime_forever_min", 0) / 60.0
        if hours < MIN_HOURS:
            continue

        tags: dict = game.get("tags", {})
        if not tags:
            continue

        # log weighting — compresses extreme outliers
        weight = math.log(hours + 1)

        # normalize tag weights within this game (SteamSpy gives raw vote counts)
        tag_total = sum(tags.values()) or 1
        for tag, count in tags.items():
            if tag in NOISE_TAGS:
                continue
            normalized = count / tag_total
            tag_scores[tag] = tag_scores.get(tag, 0.0) + weight * normalized

    # normalize the full profile to sum to 1
    total = sum(tag_scores.values()) or 1.0
    return {tag: score / total for tag, score in sorted(
        tag_scores.items(), key=lambda x: -x[1]
    )}


def score_candidate(candidate_tags: dict, taste_profile: dict[str, float]) -> float:
    """
    Score a candidate game against the taste profile.
    candidate_tags: {tag: vote_count} from SteamSpy
    Returns float in [0, 1].
    """
    if not candidate_tags:
        return 0.0

    tag_total = sum(candidate_tags.values()) or 1
    score = 0.0
    for tag, count in candidate_tags.items():
        if tag in NOISE_TAGS:
            continue
        normalized = count / tag_total
        score += normalized * taste_profile.get(tag, 0.0)

    return score


def top_profile_tags(taste_profile: dict[str, float], n: int = 30) -> list[tuple[str, float]]:
    """Return the top n tags from the taste profile."""
    return list(taste_profile.items())[:n]


def recommend(
    taste_profile: dict[str, float],
    candidates: list[dict],
    owned_appids: set,
    min_reviews: int = 500,
    min_review_ratio: float = 0.70,
    top_n: int = 30,
) -> list[dict]:
    """
    Score candidate games and return top_n recommendations.
    Filters out owned games, low-review games, and poor-rated games.
    """
    results = []

    for game in candidates:
        appid = str(game.get("appid", ""))
        if appid in owned_appids:
            continue

        positive = game.get("positive", 0)
        negative = game.get("negative", 0)
        total_reviews = positive + negative
        if total_reviews < min_reviews:
            continue
        review_ratio = positive / total_reviews
        if review_ratio < min_review_ratio:
            continue

        tags = game.get("tags", {})
        score = score_candidate(tags, taste_profile)
        if score <= 0:
            continue

        # top matching tags for explanation
        matching = sorted(
            [(t, taste_profile[t]) for t in tags if t in taste_profile and t not in NOISE_TAGS],
            key=lambda x: -x[1]
        )[:5]

        results.append({
            "appid": appid,
            "name": game.get("name", "Unknown"),
            "score": round(score, 6),
            "review_ratio": round(review_ratio, 3),
            "total_reviews": total_reviews,
            "genre": game.get("genre", ""),
            "developer": game.get("developer", ""),
            "price": game.get("price", ""),
            "matching_tags": [t for t, _ in matching],
        })

    results.sort(key=lambda x: -x["score"])
    return results[:top_n]


def save_profile(profile: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    print(f"Saved taste profile → {path}")


def load_profile(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
