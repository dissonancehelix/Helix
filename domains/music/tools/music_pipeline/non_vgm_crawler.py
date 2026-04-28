"""
non_vgm_crawler.py
Crawls Anime, Film, and Others library folders and downloads cover art.

Source priority:
  - MusicBrainz Cover Art Archive (CAA)  — primary for all non-VGM
  - Last.fm album art                     — fallback
"""
import sys, re, time, json, urllib.request, urllib.parse, hashlib
from pathlib import Path

HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
sys.path.insert(0, str(HELIX_ROOT / "domains/music/model/ingestion"))

from ign_artwork_downloader import download_artwork, is_ign_placeholder

LIBRARY_ROOT = Path("C:/Users/dissonance/Music")
NON_VGM_ROOTS = ["Anime", "Film", "Others"]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
MIN_COVER_SIZE = 50_000  # 50KB

HEADERS = {
    "User-Agent": "HelixMusicIndex/1.0 (helix@local)",
    "Accept": "application/json",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def needs_cover(folder: Path) -> bool:
    # cover.webp = user-verified — skip entirely
    if (folder / "cover.webp").exists():
        return False
    cover = folder / "cover.jpg"
    if not cover.exists():
        return True
    if cover.stat().st_size < MIN_COVER_SIZE:
        return True
    if is_ign_placeholder(cover):
        return True
    try:
        from PIL import Image
        with Image.open(cover) as img:
            img.verify()
    except Exception:
        return True
    return False


def purge_non_canonical(folder: Path):
    for f in folder.iterdir():
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
            if f.name not in ("cover.jpg", "cover.webp"):
                try:
                    f.unlink()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Source 1: MusicBrainz CAA
# ---------------------------------------------------------------------------

def resolve_musicbrainz(query: str) -> str | None:
    """Search MusicBrainz for a release matching query, return CAA front art URL."""
    try:
        search_url = (
            "https://musicbrainz.org/ws/2/release/"
            f"?query={urllib.parse.quote_plus(query)}&fmt=json&limit=3"
        )
        req = urllib.request.Request(search_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        releases = data.get("releases", [])
        if not releases:
            return None
        # Prefer releases that have cover art
        for rel in releases:
            mbid = rel.get("id")
            if not mbid:
                continue
            caa_url = f"https://coverartarchive.org/release/{mbid}/front-500"
            # HEAD check to see if art exists
            try:
                req2 = urllib.request.Request(caa_url, method="HEAD", headers={
                    "User-Agent": "HelixMusicIndex/1.0"
                })
                with urllib.request.urlopen(req2, timeout=8) as r2:
                    if r2.status == 200:
                        return caa_url
            except Exception:
                continue
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Source 2: Last.fm album art
# ---------------------------------------------------------------------------

def resolve_lastfm(artist: str, album: str) -> str | None:
    """Fetch album art from Last.fm (no API key for image URLs)."""
    try:
        query = urllib.parse.quote_plus(f"{artist} {album}")
        # Last.fm search page — scrape og:image
        url = f"https://www.last.fm/music/{urllib.parse.quote_plus(artist)}/{urllib.parse.quote_plus(album)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Extract og:image
        m = re.search(r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if not m:
            m = re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
        if m:
            img_url = m.group(1)
            # Filter out Last.fm placeholder
            if "noimage" not in img_url and "default_avatar" not in img_url:
                # Upgrade to larger size
                img_url = re.sub(r'/\d+s/', '/500s/', img_url)
                return img_url
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Folder name helpers
# ---------------------------------------------------------------------------

def parse_folder_name(folder_name: str) -> tuple[str, str]:
    """
    Try to extract (artist, album) from a folder name.
    Handles patterns like:
      - "Artist - Album"
      - "Artist - Album (Year)"
      - "Album" (flat, no artist)
    """
    # "Artist - Album" pattern
    m = re.match(r'^(.+?)\s+-\s+(.+)$', folder_name)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", folder_name.strip()


# ---------------------------------------------------------------------------
# Main crawler
# ---------------------------------------------------------------------------

def process_folder(folder: Path, parent_artist: str = "", source_class: str = "non_vgm") -> bool:
    """Process a single album folder. source_class: 'anime' | 'non_vgm'"""
    if not needs_cover(folder):
        return False

    folder_name = folder.name
    artist, album = parse_folder_name(folder_name)
    if not artist and parent_artist:
        artist = parent_artist

    cover_path = folder / "cover.jpg"

    # Anime: VGMdb ONLY — MusicBrainz returns wrong results for anime OSTs
    if source_class == "anime":
        ost_query = f"{album} original soundtrack" if album else folder_name
        if artist:
            ost_query = f"{artist} {ost_query}"
        print(f"  [{folder_name}] -> VGMdb: '{ost_query}'")
        from ign_artwork_downloader import resolve_vgmdb_artwork
        try:
            url = resolve_vgmdb_artwork(ost_query)
            if not url:
                # Retry bare name without "original soundtrack"
                url = resolve_vgmdb_artwork(album or folder_name)
            if url and download_artwork(url, cover_path):
                print(f"    [OK] VGMdb")
                purge_non_canonical(folder)
                time.sleep(0.5)
                return True
            print(f"    [FAIL] VGMdb — no result")
        except RuntimeError as e:
            print(f"    [SKIP] {e} — VGMdb unavailable, will retry later")
        return False  # Never fall to MusicBrainz for anime

    # Default: MusicBrainz
    query = f"{artist} {album}".strip() if artist else album or folder_name
    print(f"  [{folder_name}] -> MusicBrainz: '{query}'")
    url = resolve_musicbrainz(query)
    if url and download_artwork(url, cover_path):
        print(f"    [OK] MusicBrainz")
        purge_non_canonical(folder)
        time.sleep(0.5)
        return True

    # Last.fm fallback
    if artist:
        url = resolve_lastfm(artist, album or folder_name)
        if url and download_artwork(url, cover_path):
            print(f"    [OK] Last.fm")
            purge_non_canonical(folder)
            time.sleep(0.5)
            return True

    print(f"    [FAIL]")
    return False


DISC_FOLDER_RE = re.compile(
    r'^(disc|disk|cd|side|part|vol\.?)\s*\d+$', re.IGNORECASE
)


def crawl_root(root: Path, source_class: str = "non_vgm"):
    print(f"\n=== {root.name} ({len([f for f in root.iterdir() if f.is_dir()])}) ===")
    fixed = 0
    for top in sorted(root.iterdir()):
        if not top.is_dir():
            continue

        sub_dirs = [s for s in top.iterdir() if s.is_dir()
                    and s.name not in ("Artwork", "Scans", "Bonus", "Extras")]
        disc_subs = [s for s in sub_dirs if DISC_FOLDER_RE.match(s.name)]
        real_subs = [s for s in sub_dirs if not DISC_FOLDER_RE.match(s.name)]

        if disc_subs and not real_subs:
            if process_folder(top, source_class=source_class):
                fixed += 1
        elif real_subs:
            print(f"\n{top.name}/")
            for album_folder in sorted(real_subs):
                if process_folder(album_folder, parent_artist=top.name, source_class=source_class):
                    fixed += 1
        else:
            if process_folder(top, source_class=source_class):
                fixed += 1
    print(f"\n{root.name} done. Fixed: {fixed}")


if __name__ == "__main__":
    import sys
    targets = sys.argv[1:] if len(sys.argv) > 1 else NON_VGM_ROOTS

    # Wipe stale Anime covers before re-crawling
    if "Anime" in targets:
        anime_root = LIBRARY_ROOT / "Anime"
        wiped = 0
        for f in anime_root.rglob("cover.jpg"):
            if not (f.parent / "cover.webp").exists():
                f.unlink()
                wiped += 1
        print(f"[ANIME] Wiped {wiped} stale covers")

    for root_name in targets:
        root = LIBRARY_ROOT / root_name
        sc = "anime" if root_name == "Anime" else "non_vgm"
        if root.exists():
            crawl_root(root, source_class=sc)
        else:
            print(f"SKIP: {root} not found")

