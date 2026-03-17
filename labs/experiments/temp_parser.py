import os
import json
import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup

TEMP_DIR = Path(r"C:\Users\dissonance\Desktop\temp")

def parse_temp_dir():
    results = {
        "external_links": [],
        "scanned_entities": [],
        "signals": []
    }
    
    # 1. Parse SMPS / Sega Retro HTML for driver mappings
    smps_path = TEMP_DIR / "SMPS - Sega Retro.htm"
    if smps_path.exists():
        with open(smps_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            # Extract tables involving games and drivers
            for row in soup.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    game = cols[0].get_text(strip=True)
                    driver = cols[1].get_text(strip=True)
                    if "SMPS" in driver:
                        results["signals"].append({
                            "type": "DRIVER_MAPPING",
                            "game": game,
                            "driver": driver,
                            "source": "Sega Retro (SMPS)"
                        })

    # 2. Parse lastfmstats for user listening patterns (Seed for Taste Model)
    lastfm_path = TEMP_DIR / "lastfmstats-dissident93.csv"
    if lastfm_path.exists():
        with open(lastfm_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Sample artists for taste seeding
            artists = {}
            for row in reader:
                artist = row.get("artist")
                if artist:
                    artists[artist] = artists.get(artist, 0) + 1
            
            top_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)[:50]
            for artist, count in top_artists:
                results["scanned_entities"].append({
                    "id": f"music.composer:{artist.lower().replace(' ', '_')}",
                    "name": artist,
                    "type": "Composer",
                    "metadata": {"scrobbles": count, "source": "lastfmstats"}
                })

    # 3. Hidden Palace / Sega Japan Sound Docs
    hp_path = TEMP_DIR / "News_Sega of Japan Sound Documents and Source Code - Hidden Palace.htm"
    if hp_path.exists():
        results["external_links"].append({
            "title": "Sega of Japan Sound Documents and Source Code",
            "source": "Hidden Palace",
            "relevance": "Direct source code for drivers/instruments"
        })

    # 4. Sonic Retro S3K Dev Music
    s3k_dev_path = TEMP_DIR / "Sonic the Hedgehog 3_Development_Music - Sonic Retro.htm"
    if s3k_dev_path.exists():
        results["signals"].append({
            "type": "DEV_HISTORY",
            "subject": "Sonic 3 & Knuckles",
            "topic": "Michael Jackson / SST attribution gap",
            "source": "Sonic Retro"
        })

    return results

if __name__ == "__main__":
    report = parse_temp_dir()
    output_path = Path(r"C:\Users\dissonance\Desktop\Helix\artifacts\temp_parse_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {output_path}")
