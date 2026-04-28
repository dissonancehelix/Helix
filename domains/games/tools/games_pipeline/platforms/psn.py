"""
PSN ingestion module.
Uses the community `psnawp_api` library for live traversal, and provides
a fallback offline mechanism for Sony Data Access exports.
"""
import os
import json
from pathlib import Path
from typing import Optional

from .models import PlatformSource, PlatformAccount, GameTitleEntity, EngagementRecord, OwnershipRecord, TrophyRecord


class PSNClient:
    def __init__(self, npsso: Optional[str] = None):
        self.npsso = npsso or os.environ.get("PSN_NPSSO")
        self.api = None
        self.fallback_file = None
        
        if self.npsso:
            try:
                from psnawp_api import PSNAWP
                self.api = PSNAWP(self.npsso)
                print("[psn] Successfully authenticated with PSNAWP using NPSSO.")
            except ImportError:
                print("[psn] `psnawp_api` not installed. Live PSN fetching disabled.")
            except Exception as e:
                print(f"[psn] Failed to authenticate: {e}")
        else:
            print("[psn] NPSSO not provided. Live PSN fetching disabled.")

    def set_fallback(self, json_path: Path):
        """Sets an offline track source (Sony Data Access export) if auth fails."""
        if json_path.exists():
            print(f"[psn] Using fallback export: {json_path}")
            self.fallback_file = json_path
        else:
            print(f"[psn] Fallback export not found: {json_path}")
            
    def is_authenticated(self) -> bool:
        return self.api is not None

    def get_summary(self, online_id: str) -> Optional[PlatformAccount]:
        """Fetch profile and privacy defaults from PSN."""
        if not self.is_authenticated():
            return None
            
        try:
            user = self.api.user(online_id=online_id)
            profile = user.profile()
            
            return PlatformAccount(
                source=PlatformSource("psn", user.account_id, auth_status="authenticated"),
                persona_name=profile.get("onlineId", online_id),
                profile_url=profile.get("avatarUrls", [{}])[0].get("avatarUrl", ""),
                visibility_state="public", # PSNAWP hides some if private, assume public if fetched
                raw_data=profile
            )
        except Exception as e:
            print(f"[psn] Profile fetch failed for {online_id}: {e}")
            return None

    def get_owned_games(self, online_id: str) -> list[OwnershipRecord]:
        """Pulls the entire trace list of played PSN games + trophies."""
        records = []
        
        if self.is_authenticated():
            try:
                user = self.api.user(online_id=online_id)
                # Fetches title history
                titles = user.title_stats()
                source = PlatformSource("psn", user.account_id, auth_status="authenticated")
                
                for title in titles:
                    game = GameTitleEntity(
                        title_id=title.title_id,
                        name=title.name,
                        platform=f"psn_{title.category}", 
                        has_achievements=True,
                        icon_url=title.image_url
                    )
                    
                    # Convert timedelta returned by psnawp to minutes
                    total_playtime_minutes = int(title.play_duration.total_seconds() / 60) if title.play_duration else 0
                    
                    engagement = EngagementRecord(
                        playtime_forever_minutes=total_playtime_minutes,
                        last_played_timestamp=int(title.last_played_date_time.timestamp()) if title.last_played_date_time else None
                    )
                    
                    records.append(OwnershipRecord(
                        account=source,
                        game=game,
                        engagement=engagement,
                        raw_source_data={"category": title.category, "first_played": str(title.first_played_date_time)}
                    ))
            except Exception as e:
                print(f"[psn] Failed to fetch live games: {e}")
                
        elif self.fallback_file:
            print("[psn] Using dummy/offline fallback ingestion logic...")
            # If the user provides a Sony Data request zip/json, parse it here
            try:
                with open(self.fallback_file, "r") as f:
                    data = json.load(f)
                    source = PlatformSource("psn", "OFFLINE_EXPORT", auth_status="offline_fallback")
                    # Scaffolding assuming structural layout
                    for item in data.get("games", []):
                        records.append(OwnershipRecord(
                            account=source,
                            game=GameTitleEntity(title_id=item.get("titleId", ""), name=item.get("name", "Unknown PSN Game"), platform="psn"),
                            engagement=EngagementRecord(playtime_forever_minutes=item.get("playTimeInMinutes", 0))
                        ))
            except Exception as e:
                 print(f"[psn] Failed parsing fallback: {e}")
                 
        return records
