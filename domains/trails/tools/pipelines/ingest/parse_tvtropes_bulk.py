import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
MIRROR_DIR = ROOT / 'corpus' / 'tvtropes'
MIRROR_PATH = MIRROR_DIR / 'en_tvtropes_mirror.json'

# Ensure directory exists
MIRROR_DIR.mkdir(parents=True, exist_ok=True)

# ── Configuration ─────────────────────────────────────────────────────────────
# TV Tropes blocks direct requests via Cloudflare. We use Google Cache as a workaround for live data.
CACHE_PREFIX = "http://webcache.googleusercontent.com/search?q=cache:"
BASE_TVTROPES = "https://tvtropes.org/pmwiki/pmwiki.php/"

TARGET_URLS = [
    "VideoGame/TrailsSeries",
    "Characters/TrailsSeries",
    "VideoGame/TheLegendOfHeroesTrailsInTheSky",
    "VideoGame/TheLegendOfHeroesTrailsInTheSkySC",
    "VideoGame/TheLegendOfHeroesTrailsInTheSkyThe3rd",
    "VideoGame/TheLegendOfHeroesTrailsFromZero",
    "VideoGame/TheLegendOfHeroesTrailsToAzure",
    "VideoGame/TheLegendOfHeroesTrailsOfColdSteel",
    "VideoGame/TheLegendOfHeroesTrailsOfColdSteelII",
    "VideoGame/TheLegendOfHeroesTrailsOfColdSteelIII",
    "VideoGame/TheLegendOfHeroesTrailsOfColdSteelIV",
    "VideoGame/TheLegendOfHeroesTrailsIntoReverie",
    "VideoGame/TheLegendOfHeroesTrailsThroughDaybreak",
    "VideoGame/TheLegendOfHeroesTrailsThroughDaybreakII",
    "VideoGame/TheLegendOfHeroesTrailsBeyondTheHorizon",
    "VideoGame/TheLegendOfNayutaBoundlessTrails",
    "VideoGame/AkatsukiNoKiseki",
    "Anime/TheLegendOfHeroesTrailsOfColdSteelNorthernWar",
    "Characters/TrailsSeriesLiberlEstellesParty",
    "Characters/TrailsSeriesLiberlRoyaltyAndMilitary",
    "Characters/TrailsSeriesLiberlCivilians",
    "Characters/TrailsSeriesCrossbellSpecialSupportSection",
    "Characters/TrailsSeriesCrossbellPoliceAndMilitary",
    "Characters/TrailsSeriesCrossbellGovernmentAndInfluentialGroups",
    "Characters/TrailsSeriesCrossbellCivilians",
    "Characters/TrailsSeriesEreboniaThorsClassVIIOriginalMale",
    "Characters/TrailsSeriesEreboniaThorsClassVIIOriginalFemale",
    "Characters/TrailsSeriesEreboniaThorsClassVIINewClassVII",
    "Characters/TrailsSeriesEreboniaMilitaryAndGovernment",
    "Characters/TrailsSeriesEreboniaCivilians",
    "Characters/TrailsSeriesEreboniaOthers",
    "Characters/TrailsSeriesCalvardArkrideSolutionsOffice",
    "Characters/TrailsSeriesCalvardCIDAndMilitary",
    "Characters/TrailsSeriesCalvardGovernmentAndCivilians",
    "Characters/TrailsSeriesTheBracerGuild",
    "Characters/TrailsSeriesOuroboros",
    "Characters/TrailsSeriesSeptianChurch",
    "Characters/TrailsSeriesAntagonists",
    "Characters/TrailsSeriesImperialLiberationFront",
    "Characters/TrailsSeriesPosthumousCharacters",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}

def fetch_page(path):
    url = f"{CACHE_PREFIX}{BASE_TVTROPES}{path}"
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 404:
            print(f"  [ERROR] 404 Not Found on {path} (Not in Google Cache).")
            return None
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {path}: {e}")
        return None

def extract_article_body(html):
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    
    # Strip Google Cache header if present
    cache_header = soup.find(id='google-cache-hdr')
    if cache_header:
        cache_header.decompose()

    # TV Tropes article body is usually inside #main-article
    article = soup.find(id='main-article')
    if not article:
        # Fallback for structured pages
        article = soup.find(class_='article-content')
    
    if article:
        # Remove navigation, ads, etc.
        for trash in article.find_all(['script', 'style', 'ins', 'iframe', 'nav']):
            trash.decompose()
        return str(article)
    return html

def run_scraper():
    mirror = {}
    if MIRROR_PATH.exists():
        with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
            mirror = json.load(f)
        print(f"Loaded {len(mirror)} existing pages from mirror.")

    newly_fetched = 0
    for path in TARGET_URLS:
        if path in mirror:
            continue
        
        content = fetch_page(path)
        if content:
            # We save the cleaned HTML to reduce size while keeping structure (for tropes parsing)
            cleaned_content = extract_article_body(content)
            mirror[path] = cleaned_content
            newly_fetched += 1
            print(f"  [SUCCESS] {path} cloned.")
        
        # Polite delay to avoid stressing the archive
        time.sleep(2)
        
        # Save progress every 5 pages
        if newly_fetched % 5 == 0 and newly_fetched > 0:
            with open(MIRROR_PATH, 'w', encoding='utf-8') as f:
                json.dump(mirror, f, ensure_ascii=False, indent=2)
            print(f"--- Saved progress: {len(mirror)} total pages ---")

    # Final save
    with open(MIRROR_PATH, 'w', encoding='utf-8') as f:
        json.dump(mirror, f, ensure_ascii=False, indent=2)
    
    print(f"\n[DONE] Ingested {newly_fetched} NEW pages. Total in mirror: {len(mirror)}")

if __name__ == '__main__':
    run_scraper()
