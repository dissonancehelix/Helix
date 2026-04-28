"""
Normalized data models for Games Domain platform traces.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class PlatformSource:
    platform: str  # steam, psn, etc.
    account_id: str
    auth_status: str  # authenticated, public_only, missing_credentials, privacy_blocked
    pull_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PlatformAccount:
    source: PlatformSource
    persona_name: str
    profile_url: str
    visibility_state: str  # public, private, friends_only
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class GameTitleEntity:
    title_id: str  # AppID or NPWRID
    name: str
    platform: str
    has_achievements: bool = False
    icon_url: Optional[str] = None


@dataclass
class EngagementRecord:
    playtime_forever_minutes: int
    playtime_2weeks_minutes: int = 0
    last_played_timestamp: Optional[int] = None
    completion_percentage: float = 0.0


@dataclass
class AchievementRecord:
    achievement_id: str
    name: str
    unlocked: bool
    unlock_timestamp: Optional[int] = None
    rarity: Optional[float] = None
    hidden: bool = False


@dataclass
class TrophyRecord:
    trophy_id: int
    name: str
    grade: str  # bronze, silver, gold, platinum
    earned: bool
    earned_timestamp: Optional[str] = None
    rarity_percent: Optional[float] = None
    hidden: bool = False


@dataclass
class OwnershipRecord:
    """A single normalized trace of a game owned/played by the operator."""
    account: PlatformSource
    game: GameTitleEntity
    engagement: EngagementRecord
    achievements_earned: int = 0
    achievements_possible: int = 0
    trophies: list[TrophyRecord] = field(default_factory=list)
    raw_source_data: dict[str, Any] = field(default_factory=dict)

    @property
    def total_playtime_hours(self) -> float:
        return self.engagement.playtime_forever_minutes / 60.0

    def to_dict(self) -> dict:
        return {
            "platform": self.account.platform,
            "title_id": self.game.title_id,
            "name": self.game.name,
            "playtime_hours": round(self.total_playtime_hours, 2),
            "playtime_2weeks_hours": round(self.engagement.playtime_2weeks_minutes / 60.0, 2),
            "last_played": self.engagement.last_played_timestamp,
            "achievements_earned": self.achievements_earned,
            "achievements_possible": self.achievements_possible,
        }


@dataclass
class ReconciliationStatus:
    status: str
    matched_title_id: Optional[str] = None
    confidence: float = 0.0
