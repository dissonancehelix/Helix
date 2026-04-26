"""
Corpus generation for Games Domain traces.
Produces metadata aggregations from raw OwnershipRecords.
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from .models import OwnershipRecord
from .classifier import classify_record

def build_games_corpus(records: list[OwnershipRecord]) -> dict[str, Any]:
    artifacts = {}
    
    # 1. Platform Summary
    platforms = Counter(r.account.platform for r in records)
    artifacts["games_platform_summary"] = {
        "total_records": len(records),
        "by_platform": dict(platforms),
    }
    
    # 2. Engagement Summary
    total_hours = sum(r.total_playtime_hours for r in records)
    total_2weeks = sum(r.engagement.playtime_2weeks_minutes / 60.0 for r in records)
    
    top_played = sorted(records, key=lambda x: x.total_playtime_hours, reverse=True)[:50]
    
    artifacts["games_engagement_summary"] = {
        "total_playtime_hours_tracked": round(total_hours, 2),
        "recent_playtime_hours_tracked": round(total_2weeks, 2),
        "most_played_titles": [
            {
                "title": t.game.name, 
                "hours": round(t.total_playtime_hours, 2),
                "platform": t.account.platform
            } for t in top_played
        ]
    }
    
    # 3. Classifications (First Pass)
    class_dist = Counter()
    classified_records = []
    
    for r in records:
        labels = classify_record(r)
        for label in labels:
            class_dist[label] += 1
            
        rec_dict = r.to_dict()
        rec_dict["classifications"] = labels
        classified_records.append(rec_dict)

    artifacts["games_classifications"] = {"distribution": dict(class_dist)}
    artifacts["games_normalized_entities"] = classified_records
    
    return artifacts
