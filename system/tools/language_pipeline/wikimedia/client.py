"""
MediaWiki API client for Language Phase 1 ingestion.
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.parse
from typing import Generator

# Helix custom User-Agent to comply with Wikimedia API guidelines
_USER_AGENT = "HelixLanguageIngester/1.0 (Research Domain; User:Dissident93)"


class WikimediaClient:
    """Client for fetching user contributions from MediaWiki APIs."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.headers = {"User-Agent": _USER_AGENT}

    def get_user_contributions(
        self, username: str, limit_per_page: int = 500
    ) -> Generator[list[dict], None, None]:
        """
        Yields pages of user contributions (up to `limit_per_page` items each).
        Handles `uccontinue` pagination automatically.
        """
        base_params = {
            "action": "query",
            "list": "usercontribs",
            "ucuser": username,
            "uclimit": str(limit_per_page),
            "ucprop": "ids|title|timestamp|comment|size|sizediff|flags|tags",
            "format": "json"
        }
        
        continue_params = {}

        while True:
            params = {**base_params, **continue_params}
            url = f"{self.endpoint}?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode("utf-8"))
            except Exception as e:
                print(f"[wikimedia_client] API Error for {self.endpoint}: {e}")
                break

            if "query" in data and "usercontribs" in data["query"]:
                yield data["query"]["usercontribs"]

            if "continue" in data and "uccontinue" in data["continue"]:
                continue_params = {"uccontinue": data["continue"]["uccontinue"]}
                # Sleep briefly to respect API etiquette
                time.sleep(0.5)
            else:
                break
