"""
Platforms ingestion pipeline for the Games Domain.
"""
from .models import (
    PlatformSource, PlatformAccount, GameTitleEntity, 
    EngagementRecord, OwnershipRecord, TrophyRecord, AchievementRecord
)
from .steam import SteamClient
from .psn import PSNClient
from .classifier import classify_record
from .corpus import build_games_corpus

__all__ = [
    "PlatformSource", "PlatformAccount", "GameTitleEntity",
    "EngagementRecord", "OwnershipRecord", "TrophyRecord", "AchievementRecord",
    "SteamClient", "PSNClient", "classify_record", "build_games_corpus"
]
