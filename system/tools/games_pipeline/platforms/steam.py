"""
Steam official Web API client.
Extracts operator play traces from Steam profiles.
"""
import os
import urllib.request
import urllib.parse
import json
from typing import Optional

from .models import PlatformSource, PlatformAccount, GameTitleEntity, EngagementRecord, OwnershipRecord


class SteamClient:
    """Client for pulling traces via Steam Web API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("STEAM_API_KEY")
        self.base_url = "http://api.steampowered.com"
        
    def is_authenticated(self) -> bool:
        return bool(self.api_key)

    def _get(self, interface: str, method: str, version: str, **params) -> dict:
        if not self.api_key:
            raise ValueError("STEAM_API_KEY is missing. Cannot fetch Steam traces.")
            
        params["key"] = self.api_key
        params["format"] = "json"
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}/{interface}/{method}/{version}/?{query}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HelixGamesIngest/1.0"})
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"[steam] 403 Forbidden on {method} (Privacy/Visibility block)")
                return {}
            elif e.code == 401:
                print("[steam] 401 Unauthorized. Invalid API Key.")
                return {}
            raise e
        except Exception as e:
            print(f"[steam] API Request Failed: {e}")
            return {}

    def resolve_vanity(self, vanit_url: str) -> Optional[str]:
        """Resolves a vanity profile URL into a SteamID64."""
        resp = self._get("ISteamUser", "ResolveVanityURL", "v0001", vanityurl=vanit_url)
        if "response" in resp and resp["response"].get("success") == 1:
            return resp["response"]["steamid"]
        return None

    def get_summary(self, steam_id: str) -> Optional[PlatformAccount]:
        """Fetch player summary and privacy defaults."""
        resp = self._get("ISteamUser", "GetPlayerSummaries", "v0002", steamids=steam_id)
        if "response" in resp and resp["response"].get("players"):
            p = resp["response"]["players"][0]
            
            # CommunityVisibilityState: 1 = private, 3 = public
            vis = "public" if p.get("communityvisibilitystate") == 3 else "private"
            
            return PlatformAccount(
                source=PlatformSource("steam", steam_id, auth_status="authenticated" if self.api_key else "missing_credentials"),
                persona_name=p.get("personaname", "Unknown User"),
                profile_url=p.get("profileurl", ""),
                visibility_state=vis,
                raw_data=p
            )
        return None

    def get_owned_games(self, steam_id: str) -> list[OwnershipRecord]:
        """Pulls the entire trace list of owned and played Free-to-Play games."""
        resp = self._get(
            "IPlayerService", "GetOwnedGames", "v0001", 
            steamid=steam_id, 
            include_appinfo=1, 
            include_played_free_games=1
        )
        
        owned = []
        source = PlatformSource("steam", steam_id, auth_status="authenticated")
        
        if "response" in resp and "games" in resp["response"]:
            for game in resp["response"]["games"]:
                entity = GameTitleEntity(
                    title_id=str(game["appid"]),
                    name=game.get("name", f"App {game['appid']}"),
                    platform="steam",
                    icon_url=game.get("img_icon_url")
                )
                
                engagement = EngagementRecord(
                    playtime_forever_minutes=game.get("playtime_forever", 0),
                    playtime_2weeks_minutes=game.get("playtime_2weeks", 0),
                    last_played_timestamp=game.get("rtime_last_played")
                )
                
                owned.append(OwnershipRecord(
                    account=source,
                    game=entity,
                    engagement=engagement,
                    raw_source_data=game
                ))
        return owned
    
    def get_achievements(self, steam_id: str, appid: str) -> dict:
        """Pulls game-level achievements and unlock timestamps."""
        resp = self._get(
            "ISteamUserStats", "GetPlayerAchievements", "v0001",
            steamid=steam_id,
            appid=appid
        )
        stats = {"achievements_earned": 0, "achievements_possible": 0, "success": False}
        
        if "playerstats" in resp and resp["playerstats"].get("success"):
            stats["success"] = True
            achievements = resp["playerstats"].get("achievements", [])
            stats["achievements_possible"] = len(achievements)
            stats["achievements_earned"] = sum(1 for a in achievements if a.get("achieved", 0) == 1)
            
        return stats
