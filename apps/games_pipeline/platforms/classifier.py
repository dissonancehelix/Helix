"""
Classifier for Games Domain engagement traces.
Produces structural categorizations from raw duration and unlock frequencies.
"""
from __future__ import annotations
import time
from .models import OwnershipRecord

# Classifications matching user targets
CLS_OWNED_NOT_PLAYED    = "owned_not_played"
CLS_LIGHTLY_ENGAGED     = "lightly_engaged"
CLS_HEAVILY_ENGAGED     = "heavily_engaged"
CLS_RECENTLY_ACTIVE     = "recently_active"
CLS_LEGACY_LIBRARY      = "legacy_library"
CLS_ACHIEVEMENT_RICH    = "achievement_rich"
CLS_MULTI_PLATFORM      = "multi_platform_candidate"
CLS_VISIBILITY_BLOCKED  = "visibility_blocked"


def classify_record(record: OwnershipRecord) -> list[str]:
    """Applies engagement-based heuristic buckets to an OwnershipRecord."""
    classifications = []
    
    # 1. Ownership vs Execution
    if record.total_playtime_hours < 0.1:
        classifications.append(CLS_OWNED_NOT_PLAYED)
    elif record.total_playtime_hours < 5.0:
        classifications.append(CLS_LIGHTLY_ENGAGED)
    elif record.total_playtime_hours > 50.0:
        classifications.append(CLS_HEAVILY_ENGAGED)
        
    # 2. Recency
    if record.engagement.playtime_2weeks_minutes > 0:
        classifications.append(CLS_RECENTLY_ACTIVE)
        
    if record.engagement.last_played_timestamp:
        # If older than 3 years (approx 3 * 31536000 seconds)
        if (time.time() - record.engagement.last_played_timestamp) > 94608000:
            classifications.append(CLS_LEGACY_LIBRARY)
            
    # 3. Achievement Density
    if record.achievements_possible > 0:
        completion = record.achievements_earned / float(record.achievements_possible)
        if completion > 0.5:
            classifications.append(CLS_ACHIEVEMENT_RICH)
            
    # 4. Privacy failures
    if record.account.auth_status == "privacy_blocked":
        classifications.append(CLS_VISIBILITY_BLOCKED)
        
    return classifications
