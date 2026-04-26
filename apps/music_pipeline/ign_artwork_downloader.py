import json
import re
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
IGN_GAMES_BASE = "https://www.ign.com/games/"

# MD5 hashes of known IGN placeholder images (no real art available).
# Add new ones here when discovered.
KNOWN_IGN_PLACEHOLDER_HASHES = {
    "856faeec5bfabac93bf8657a98e6db5c",  # Generic IGN placeholder (Assault City)
    "10ae74119286b34978e3f02307610217",  # Large IGN placeholder ~28MB (ABC Monday Night Football, 688 Attack Sub, etc.)
}

# Hard-coded IGN image URLs for major series where slug resolution is fragile.
# Used by batch_repair_ff.py
FF_SERIES_IMAGE_MAP = {
    "final_fantasy_i":    "https://assets1.ignimgs.com/2022/06/23/final-fantasy-i-1655991600626.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_ii":   "https://assets1.ignimgs.com/2022/06/23/final-fantasy-ii-1655991600626.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_iii":  "https://assets1.ignimgs.com/2022/06/23/final-fantasy-iii-1655991600626.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_iv":   "https://assets1.ignimgs.com/2022/06/23/final-fantasy-iv-1655991600626.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_v":    "https://assets1.ignimgs.com/2022/06/23/final-fantasy-v-1655991600626.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_vi":   "https://assets1.ignimgs.com/2022/06/23/final-fantasy-vi-1655991600626.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_vii":  "https://assets1.ignimgs.com/2018/09/30/final-fantasy-vii-buttonfinf-1538333812218.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_viii": "https://assets1.ignimgs.com/2019/08/27/final-fantasy-viii-button-1566933795735.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_ix":   "https://assets1.ignimgs.com/2019/01/18/final-fantasy-ix-button-1547849052665.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_x":    "https://assets1.ignimgs.com/2019/05/12/final-fantasy-x-button-1557703012665.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_xi":   "https://assets1.ignimgs.com/2021/03/02/final-fantasy-xi-button-1614721802012.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_xii":  "https://assets1.ignimgs.com/2018/09/21/final-fantasy-xii-button-1537568402012.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_xiii": "https://assets1.ignimgs.com/2019/03/22/final-fantasy-xiii-button-1553277602012.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_xiv":  "https://assets1.ignimgs.com/2019/07/01/final-fantasy-xiv-button-1561990402012.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_xv":   "https://assets1.ignimgs.com/2018/06/13/final-fantasy-xv-button-1528905602012.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
    "final_fantasy_xvi":  "https://assets1.ignimgs.com/2022/09/16/final-fantasy-xvi-button-1663362402012.jpg?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000",
}

# Japanese title → IGN slug remappings.
# Policy: use English/American name unless the English release name was poor
# or the title was Japan-only with no official English equivalent.
VGM_ALIAS_MAP = {
    # Castlevania — use English names for internationally released titles
    "akumajo-dracula":                   "castlevania",
    "akumajo-dracula-x68000":            "akumajo-dracula",       # X68000 — Japan-only
    "akumajo-dracula-x-chi-no-rondo":    "castlevania-rondo-of-blood",
    "akumajo-dracula-xx":                "castlevania-dracula-x",
    "akumajo-dracula-x":                 "akumajo-dracula-x",     # PC Engine — keep JP slug

    # Pokémon — combined folder names → first listed IGN version page
    "pokemon-firered-and-leafgreen":     "pokemon-firered-version",
    "pokemon-gold-and-silver":           "pokemon-gold-version",
    "pokemon-ruby-and-sapphire":         "pokemon-ruby-version",
    "pokemon-diamond-and-pearl":         "pokemon-diamond-version",
    "pokemon-black-and-white":           "pokemon-black-version",
    "pokemon-black-2-and-white-2":       "pokemon-black-version-ii",
    "pokemon-x-and-y":                   "pokemon-x",
    "pokemon-x-y":                       "pokemon-x",
    "pokemon-sun-and-moon":              "pokemon-sun",
    "pokemon-sword-and-shield":          "pokemon-sword",
    "pokemon-scarlet-and-violet":        "pokemon-scarlet",

    # JP → EN title remappings
    "famicom-tantei-club":               "famicom-detective-club",
    "pocket-monsters":                   "pokemon",
    "ryu-ga-gotoku":                     "yakuza",
    "biohazard":                         "resident-evil",
    "rockman":                           "mega-man",
    "hokuto-no-ken":                     "fist-of-the-north-star",
    "hoshi-no-kirby":                    "kirby",
    "mother":                            "earthbound",
    "earthbound-beginnings":             "earthbound-beginnings",
    "densetsu-no-stafy":                 "the-legendary-starfy",
    "bare-knuckle":                      "streets-of-rage",

    # Subtitle/spelling corrections
    "the-witcher-iii-wild-hunt":         "the-witcher-3-wild-hunt",
    "the-witcher-ii-assassins-of-kings": "the-witcher-2-assassins-of-kings",
    "xenoblade-ii-torna":                "xenoblade-2-torna-the-golden-country",
    "klonoa-ii":                         "klonoa-2-lunateas-veil",
    "ys-i-and-ii-chronicles":            "ys-i-ii-chronicles",

    # Ace Combat — IGN uses subtitle in slug
    "ace-combat-2":     "ace-combat-2",
    "ace-combat-ii":    "ace-combat-2",
    "ace-combat-3":     "ace-combat-3-electrosphere",
    "ace-combat-iii":   "ace-combat-3-electrosphere",
    "ace-combat-4":     "ace-combat-4-shattered-skies",
    "ace-combat-iv":    "ace-combat-4-shattered-skies",
    "ace-combat-5":     "ace-combat-5-the-unsung-war",
    "ace-combat-v":     "ace-combat-5-the-unsung-war",
    "ace-combat-zero":  "ace-combat-zero-the-belkan-war",
    "ace-combat-6":     "ace-combat-6-fires-of-liberation",
    "ace-combat-vi":    "ace-combat-6-fires-of-liberation",
    "ace-combat-7":     "ace-combat-7-skies-unknown",
    "ace-combat-vii":   "ace-combat-7-skies-unknown",
}

# Folder names that should never be sent to IGN (BIOS dumps, system software, etc.)
# These have no IGN page and the DDG fallback returns false positives.
# Keep patterns specific — avoid catching legitimate game titles.
IGN_SKIP_PATTERNS = re.compile(
    r'\b(bios|firmware|sdk|devkit'
    r'|test\s*cart|burn.in\s*test'
    r'|proto(?:type)?|unreleased)\b'
    r'|^sega\s+channel$'          # exact: "Sega Channel" but not "Space Channel 5"
    r'|disk\s+system\s+bios',
    re.IGNORECASE
)


RE_IGN_PRIMARY_ART = re.compile(
    r'https://(?:assets[^\s"]+ignimgs\.com|media\.gamestats\.com)/[^\s"]+\.(?:jpg|png|webp|jpeg)(?:\?crop=1%3A1%2Csmart)?'
)


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# IGN spells out leading numbers in game slugs.
_LEADING_NUM_TO_WORD = {
    "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
    "11": "eleven", "12": "twelve", "13": "thirteen", "14": "fourteen",
    "15": "fifteen", "16": "sixteen", "17": "seventeen", "18": "eighteen",
    "19": "nineteen", "20": "twenty",
}

# IGN uses Roman numerals for trailing sequel numbers (baldurs-gate-iii, not baldurs-gate-3).
_TRAILING_NUM_TO_ROMAN = {
    "2": "ii", "3": "iii", "4": "iv", "5": "v",
    "6": "vi", "7": "vii", "8": "viii", "9": "ix", "10": "x",
    "11": "xi", "12": "xii", "13": "xiii", "14": "xiv", "15": "xv",
    "16": "xvi", "17": "xvii", "18": "xviii", "19": "xix", "20": "xx",
}


def slugify_game_name(name: str) -> str:
    import unicodedata
    # Normalize diacritics: é→e, ü→u, ñ→n, etc.
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    clean = re.sub(r'\(.*?\)', '', name).strip()
    clean = clean.replace("'", "")
    # Convert leading number to word (e.g. "9 Years" → "nine Years")
    m = re.match(r'^(\d+)\b', clean)
    if m:
        num = m.group(1)
        if num in _LEADING_NUM_TO_WORD:
            clean = _LEADING_NUM_TO_WORD[num] + clean[len(num):]
    # Convert trailing sequel number to Roman numeral (e.g. "Gate 3" → "Gate iii")
    # Skip if the name already ends with a Roman numeral (e.g. "Hades II" → stay as "hades-ii")
    already_roman = bool(re.search(r'\b(II|III|IV|VI|VII|VIII|IX|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)\s*$', clean, re.I))
    if not already_roman:
        m2 = re.search(r'\b(\d+)$', clean.strip())
        if m2:
            num = m2.group(1)
            if num in _TRAILING_NUM_TO_ROMAN:
                clean = clean[:m2.start()] + _TRAILING_NUM_TO_ROMAN[num]
    return re.sub(r'[^a-z0-9]+', '-', clean.lower()).strip('-')



# URL fragments that indicate IGN is serving a generic placeholder image
# rather than real game art.
_IGN_PLACEHOLDER_URL_PATTERNS = re.compile(
    r'red-dpad|ign-default|no-image|placeholder|missing|default[-_]cover'
    r'|/registration/|GameBacklog|backlog[-_]?light',
    re.IGNORECASE
)


def needs_repair(folder: Path) -> bool:
    """
    Returns True only if the cover genuinely needs replacing:
    - missing
    - too small (< 50 KB)
    - known IGN placeholder hash
    - corrupted / unreadable by PIL
    Folders with .cover_locked are always skipped (manually curated).
    """
    if (folder / ".cover_locked").exists():
        return False
    cover = folder / "cover.jpg"
    if not cover.exists():
        return True
    if cover.stat().st_size < 50000:
        return True
    return is_ign_placeholder(cover)


def is_ign_placeholder(file_path: Path) -> bool:
    """Returns True if the file matches a known IGN placeholder hash."""
    try:
        with open(file_path, 'rb') as f:
            h = hashlib.md5(f.read()).hexdigest()
        return h in KNOWN_IGN_PLACEHOLDER_HASHES
    except Exception:
        return False


def download_artwork(url: str, dest_path: Path) -> bool:
    """
    Downloads any image URL and saves it as a proper JPEG at dest_path.
    Re-encodes via Pillow to guarantee JPEG bytes regardless of source format
    (IGN sometimes serves WebP despite ?format=jpg in the URL).
    """
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
        if len(data) < 5000:
            return False

        # Re-encode as JPEG via Pillow to handle WebP/PNG/etc. from source
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(data))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=95, optimize=True)
            dest_path.write_bytes(out.getvalue())
        except Exception:
            # Pillow unavailable or unrecognised format — fall back to raw write
            dest_path.write_bytes(data)

        return True
    except Exception:
        return False



# Keep old name as alias for backward compat with batch_repair_ff.py
download_ign_artwork = download_artwork


# ---------------------------------------------------------------------------
# Source 1: IGN (clean digital key visuals, no console branding)
# ---------------------------------------------------------------------------

def _resolve_ign_search(game_name: str) -> str | None:
    """
    Fallback for JS-gated IGN pages: search DuckDuckGo for site:ign.com/<slug>
    to find the canonical slug, then fetch the IGN game page for the image.
    """
    query = urllib.parse.quote_plus(f"site:ign.com/games {game_name}")
    ddg_url = f"https://html.duckduckgo.com/html/?q={query}"
    try:
        req = urllib.request.Request(ddg_url, headers={
            **_HEADERS,
            "Accept": "text/html",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Extract ign.com/games/<slug> links from DDG results
        slugs = re.findall(r'ign\.com/games/([\w\-]+)', html)
        if not slugs:
            return None

        # Try each slug — but validate it actually matches the game name.
        # Stops DDG returning e.g. dragon-quest for 'Seed of Dragon'.
        _STOPWORDS = {'the', 'a', 'an', 'of', 'in', 'to', 'and', 'or', 'for',
                      'de', 'no', 'ga', 'wo', 'ni', 'part', 'version', 'vol'}

        def _slug_matches_game(slug: str, game: str) -> bool:
            """True if slug shares ≥1 significant word with the game name."""
            game_words = {w for w in re.split(r'\W+', game.lower()) if len(w) > 2 and w not in _STOPWORDS}
            slug_words = set(slug.replace('-', ' ').split())
            return bool(game_words & slug_words)

        exact_slug = slugify_game_name(game_name)
        ordered = []
        for s in slugs:
            if s == exact_slug:
                ordered.insert(0, s)
            elif _slug_matches_game(s, game_name):
                ordered.append(s)
        # If nothing matched, bail — don't guess
        if not ordered:
            return None

        for slug in ordered[:3]:
            page_url = f"{IGN_GAMES_BASE}{slug}"
            try:
                req2 = urllib.request.Request(page_url, headers=_HEADERS)
                with urllib.request.urlopen(req2, timeout=10) as r2:
                    page_html = r2.read().decode("utf-8", errors="ignore")
                candidates = RE_IGN_PRIMARY_ART.findall(page_html)
                best = None
                for c in candidates:
                    if 'crop=1%3A1' in c:
                        best = c
                        break
                    if 'button' in c.lower() or 'boxart' in c.lower():
                        best = c
                if not best and candidates:
                    best = candidates[0]
                if best:
                    base = best.split("?")[0] if "?" in best else best
                    if not _IGN_PLACEHOLDER_URL_PATTERNS.search(base):
                        return f"{base}?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000"
            except Exception:
                continue

    except Exception:
        pass
    return None


_ROMAN_TO_NUM = {"ii":"2","iii":"3","iv":"4","v":"5","vi":"6","vii":"7","viii":"8","ix":"9","x":"10","xi":"11","xii":"12","xiii":"13","xiv":"14","xv":"15","xvi":"16"}
_NUM_TO_ROMAN = {v: k for k, v in _ROMAN_TO_NUM.items()}


def _both_number_variants(slug: str) -> list[str]:
    """
    Given a slug, return both the Roman-numeral and numeric trailing variants.
    e.g. 'ace-combat-vi'  -> ['ace-combat-vi', 'ace-combat-6']
         'yakuza-3'       -> ['yakuza-3', 'yakuza-iii']
    Returns empty list if no trailing numeral found.
    """
    # Trailing Roman numeral → also emit numeric
    m = re.search(r'-(' + '|'.join(_ROMAN_TO_NUM) + r')$', slug, re.IGNORECASE)
    if m:
        num = _ROMAN_TO_NUM[m.group(1).lower()]
        numeric = slug[:m.start()] + '-' + num
        return [slug, numeric]
    # Trailing digit → also emit Roman
    m = re.search(r'-(\d+)$', slug)
    if m and m.group(1) in _NUM_TO_ROMAN:
        roman = slug[:m.start()] + '-' + _NUM_TO_ROMAN[m.group(1)]
        return [slug, roman]
    return []


_PLATFORM_NORMALISE = {
    "nes": "nes", "famicom": "nes",
    "snes": "snes", "super nintendo": "snes", "super-nintendo": "snes",
    "gen": "genesis", "md": "genesis", "mega drive": "genesis", "genesis": "genesis",
    "gb": "game-boy", "gbc": "game-boy-color", "gba": "game-boy-advance",
    "gc": "gamecube", "gamecube": "gamecube",
    "n64": "nintendo-64", "nintendo 64": "nintendo-64",
    "ds": "nintendo-ds", "3ds": "nintendo-3ds",
    "ps1": "playstation", "psx": "playstation", "ps": "playstation",
    "ps2": "playstation-2", "ps3": "playstation-3", "ps4": "playstation-4", "ps5": "playstation-5",
    "psp": "psp", "vita": "playstation-vita",
    "sat": "saturn", "saturn": "saturn",
    "scd": "sega-cd", "sega cd": "sega-cd",
    "gg": "game-gear", "sms": "master-system",
    "pc": "pc", "win": "pc", "dos": "pc",
    "x68": "x68000", "x68000": "x68000",
    "tg16": "turbografx-16", "pce": "pc-engine",
    "ngp": "neo-geo-pocket", "ng": "neo-geo",
    "xbox": "xbox", "x360": "xbox-360", "xone": "xbox-one",
    "wii": "wii", "wiiu": "wii-u", "switch": "switch",
}


def _slug_candidates(game_name: str) -> list[str]:
    """
    Generate slug variants to try when the primary slug fails.
    - Both Roman numeral and numeric trailing forms
    - Subtitle stripping
    - Platform-qualified slugs before bare name
    - Parenthetical tag stripping
    """
    slug = slugify_game_name(game_name)
    candidates = [slug]
    candidates.extend(_both_number_variants(slug))

    # Platform tag in parens: "Aladdin (SNES)" → try "aladdin-snes" before "aladdin"
    paren_match = re.search(r'\(([^)]+)\)', game_name)
    if paren_match:
        tag = paren_match.group(1).strip().lower()
        platform = _PLATFORM_NORMALISE.get(tag)
        no_paren = re.sub(r'\s*\([^)]+\)', '', game_name).strip()
        bare_slug = slugify_game_name(no_paren)
        if platform:
            candidates.append(f"{bare_slug}-{platform}")
        candidates.append(bare_slug)
        candidates.extend(_both_number_variants(bare_slug))
    elif '(' in game_name:
        no_paren = re.sub(r'\s*\([^)]+\)', '', game_name).strip()
        bare_slug = slugify_game_name(no_paren)
        candidates.append(bare_slug)
        candidates.extend(_both_number_variants(bare_slug))

    # Subtitle stripping: "Game - Subtitle" → try "game" and "subtitle"
    for sep in [" - ", ": ", " ~ "]:
        if sep in game_name:
            main = game_name.split(sep)[0].strip()
            sub  = game_name.split(sep, 1)[1].strip()
            main_slug = slugify_game_name(main)
            candidates.append(main_slug)
            candidates.extend(_both_number_variants(main_slug))
            candidates.append(slugify_game_name(sub))
            candidates.append(slugify_game_name(main + " " + sub))
            break

    seen: set = set()
    out = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out




def _try_ign_slug(slug: str) -> str | None:
    """Fetch an IGN game page by slug and extract the best art URL."""
    url = f"{IGN_GAMES_BASE}{slug}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
        candidates = RE_IGN_PRIMARY_ART.findall(html)
        best = None
        for c in candidates:
            if 'crop=1%3A1' in c:
                best = c
                break
            if 'button' in c.lower() or 'boxart' in c.lower() or 'key-visual' in c.lower():
                best = c
        if not best and candidates:
            best = candidates[0]
        if best:
            base = best.split('?')[0] if '?' in best else best
            if _IGN_PLACEHOLDER_URL_PATTERNS.search(base):
                return None
            return f"{base}?crop=1%3A1%2Csmart&format=jpg&quality=100&width=1000"
    except Exception:
        pass
    return None


def _resolve_ign(game_name: str) -> str | None:
    # Skip BIOS dumps, system software, demos etc. — no IGN page, DDG returns garbage
    if IGN_SKIP_PATTERNS.search(game_name):
        return None

    # Check hard-coded overrides first (FF series etc.)
    clean_key = re.sub(r'[^a-z0-9_]', '_', game_name.lower().strip())
    if clean_key in FF_SERIES_IMAGE_MAP:
        return FF_SERIES_IMAGE_MAP[clean_key]

    for slug in _slug_candidates(game_name):
        # Apply alias map
        resolved = VGM_ALIAS_MAP.get(slug, slug)
        result = _try_ign_slug(resolved)
        if result:
            return result

    # All slug variants failed — try DuckDuckGo search fallback
    return _resolve_ign_search(game_name)


# ---------------------------------------------------------------------------
# Source 2: VGMdb (OST covers via vgmdb.info JSON mirror)
# ---------------------------------------------------------------------------

_SEARCH_STOPWORDS = {'the','a','an','of','in','to','and','or','for','original',
                     'soundtrack','ost','music','collection','complete','best',
                     'de','no','wa','ga','wo','ni','to','vol','part','ep'}

def _title_matches_query(album_titles: dict, query: str, threshold: int = 1) -> bool:
    """
    Check if any of the album's titles share >= threshold significant words with the query.
    Also enforces sequel number matching: 'Ace Combat 6' will not match 'Ace Combat 7'.
    """
    query_words = {w for w in re.split(r'\W+', query.lower())
                   if len(w) > 2 and w not in _SEARCH_STOPWORDS}
    if not query_words:
        return True  # can't validate, accept

    # Extract trailing sequel number from query (digit or Roman numeral)
    query_num = None
    m = re.search(r'\b(\d+)$', query.strip())
    if m:
        query_num = m.group(1)
    else:
        m = re.search(r'\b(' + '|'.join(_ROMAN_TO_NUM) + r')$', query.strip(), re.IGNORECASE)
        if m:
            query_num = _ROMAN_TO_NUM[m.group(1).lower()]  # normalize to digit string

    for title in album_titles.values():
        title_words = {w for w in re.split(r'\W+', title.lower())
                       if len(w) > 2 and w not in _SEARCH_STOPWORDS}
        if len(query_words & title_words) < threshold:
            continue

        # If query has a sequel number, ensure title has the SAME number
        if query_num is not None:
            # Find any number in the title (digit or Roman)
            title_nums = set()
            for n in re.findall(r'\b(\d+)\b', title):
                title_nums.add(n)
            for rn in re.findall(r'\b(' + '|'.join(_ROMAN_TO_NUM) + r')\b', title, re.IGNORECASE):
                title_nums.add(_ROMAN_TO_NUM[rn.lower()])
            # If title has numbers but none match → reject; if title has NO numbers → also reject (wrong sequel)
            if not title_nums or query_num not in title_nums:
                continue

        return True
    return False


def resolve_vgmdb_artwork(game_name: str) -> str | None:
    """
    Searches vgmdb.info (JSON API mirror) for the soundtrack cover.
    Raises RuntimeError on 503/429 so callers can back off.
    Validates result title to avoid false positives.
    """
    query = urllib.parse.quote_plus(game_name)
    search_url = f"https://vgmdb.info/search/albums/{query}?format=json"
    try:
        req = urllib.request.Request(search_url, headers={**_HEADERS, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (429, 503, 502):
            raise RuntimeError(f"VGMdb rate-limited ({e.code})") from e
        return None
    except Exception:
        return None

    try:
        results = data.get("results", {}).get("albums", [])
        if not results:
            return None

        for result in results[:3]:
            album_link = result.get("link")
            if not album_link:
                continue
            album_titles = result.get("titles", {})
            if album_titles and not _title_matches_query(album_titles, game_name):
                continue

            time.sleep(0.5)  # be polite to the API
            album_url = f"https://vgmdb.info/{album_link}?format=json"
            req2 = urllib.request.Request(album_url, headers={**_HEADERS, "Accept": "application/json"})
            with urllib.request.urlopen(req2, timeout=12) as resp2:
                album_data = json.loads(resp2.read().decode("utf-8"))

            if not album_titles:
                full_titles = album_data.get("names", {})
                if full_titles and not _title_matches_query(full_titles, game_name):
                    continue

            cover = album_data.get("picture_full") or album_data.get("picture_small")
            if cover:
                return cover

        return None
    except Exception:
        return None




# ---------------------------------------------------------------------------
# Source 3: TheAudioDB (game/anime OST covers, free API)
# ---------------------------------------------------------------------------

def resolve_theaudiodb_artwork(game_name: str) -> str | None:
    """
    Searches TheAudioDB for the game's OST album art.
    Uses the free API (key=2). Validates title match before accepting.
    """
    query = urllib.parse.quote_plus(game_name)
    # TheAudioDB general album search
    url = f"https://www.theaudiodb.com/api/v1/json/2/searchalbum.php?s={query}&a={query}"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        albums = data.get("album") or []
        for album in albums[:3]:
            title = album.get("strAlbum", "")
            artist = album.get("strArtist", "")
            if not _title_matches_query({"title": title, "artist": artist}, game_name):
                continue
            thumb = album.get("strAlbumThumb")
            if thumb:
                return thumb
    except Exception:
        pass
    return None



# ---------------------------------------------------------------------------
# Source 4: iTunes Search API (OST releases on Apple Music)
# ---------------------------------------------------------------------------

def resolve_itunes_artwork(game_name: str) -> str | None:
    """
    Searches iTunes for the OST album. Returns 1000px artwork URL.
    Validates album name matches query before accepting.
    """
    # Append "original soundtrack" to bias toward OST results
    query = urllib.parse.quote_plus(f"{game_name} original soundtrack")
    url = f"https://itunes.apple.com/search?term={query}&entity=album&limit=5&media=music"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results = data.get("results", [])
        for r in results:
            collection = r.get("collectionName", "")
            artist = r.get("artistName", "")
            if not _title_matches_query({"collection": collection, "artist": artist}, game_name):
                continue
            art = r.get("artworkUrl100", "")
            if art:
                # Upgrade to 1000px
                return art.replace("100x100bb", "1000x1000bb")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Source 5: MusicBrainz CAA (physical OST releases)
# ---------------------------------------------------------------------------

def resolve_musicbrainz_caa(game_name: str) -> str | None:
    """
    Searches MusicBrainz for an OST release and returns front cover from CAA.
    Validates release title before fetching cover.
    """
    query = urllib.parse.quote_plus(f"{game_name} original soundtrack")
    search_url = f"https://musicbrainz.org/ws/2/release/?query={query}&fmt=json&limit=5"
    try:
        req = urllib.request.Request(search_url, headers={
            **_HEADERS, "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        releases = data.get("releases", [])
        for rel in releases[:5]:
            title = rel.get("title", "")
            if not _title_matches_query({"title": title}, game_name):
                continue
            mbid = rel.get("id")
            if not mbid:
                continue
            caa_url = f"https://coverartarchive.org/release/{mbid}/front-500"
            try:
                req2 = urllib.request.Request(caa_url, method="HEAD", headers={
                    "User-Agent": _HEADERS["User-Agent"]
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
# Source 6: SNESmusic.org (title screens for SNES games)
# ---------------------------------------------------------------------------


def _snesmusic_find_game(game_name: str) -> str | None:
    """
    Searches all pages of the snesmusic.org listing for game_name.
    Returns the profile URL or None.
    """
    clean = re.sub(r'^(?:the|a|an)\s+', '', game_name.strip(), flags=re.IGNORECASE)
    first_char = clean[0].upper() if clean else game_name[0].upper()
    if not first_char.isalpha():
        first_char = 'n1-9'

    name_lower = game_name.lower()
    base = f"https://www.snesmusic.org/v2/select.php?view=sets&char={first_char}&limit="

    for page in range(20):  # up to 600 entries per letter
        offset = page * 30
        try:
            req = urllib.request.Request(f"{base}{offset}", headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')

            entries = re.findall(
                r"href='(profile\.php\?profile=set&amp;selected=\d+)'>([^<]+)</a>",
                html
            )
            if not entries:
                break  # no more results

            for href, title in entries:
                if title.lower() == name_lower:
                    return f"https://www.snesmusic.org/v2/{href.replace('&amp;', '&')}"

            # Fuzzy pass: require significant word overlap, not just substring
            for href, title in entries:
                if _title_matches_query({"title": title}, game_name):
                    return f"https://www.snesmusic.org/v2/{href.replace('&amp;', '&')}"

            if len(entries) < 30:
                break  # last page
        except Exception:
            break

    return None


def resolve_snesmusic_artwork(game_name: str) -> str | None:
    """
    Fetches the title screen screenshot from snesmusic.org.
    Only meaningful for SNES games — returns the in-game title screen image.
    """
    profile_url = _snesmusic_find_game(game_name)
    if not profile_url:
        return None
    try:
        req = urllib.request.Request(profile_url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            profile_html = resp.read().decode('utf-8', errors='ignore')
        screen = re.search(r"src='(images/screenshots/[^\s'\"<>]+)'", profile_html)
        if screen:
            return f"https://www.snesmusic.org/v2/{screen.group(1)}"
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Source 4: VGMrips (title screens for NES, MD, GB, and other retro platforms)
# ---------------------------------------------------------------------------

def resolve_vgmrips_artwork(game_name: str) -> str | None:
    """
    Searches VGMrips for the game and returns the pack's cover image.
    Covers NES, Mega Drive, Game Boy, Neo Geo, arcade, and other retro platforms.
    Handles direct pack pages, search result lists, and disambiguation pages.
    Tries multiple query forms if the full name returns no results.
    """
    # Build query candidates: full name, subtitle, simplified name
    queries = [game_name]
    for sep in [" - ", ": ", " ~ "]:
        if sep in game_name:
            parts = game_name.split(sep, 1)
            queries.append(parts[1].strip())  # subtitle only
            queries.append(parts[0].strip())  # main title only
            break

    def _extract_image(page_html: str) -> str | None:
        large = re.search(
            r'(https://vgmrips\.net/packs/images/large/[^\s"\'<>]+\.png)', page_html
        )
        if large:
            return large.group(1)
        small = re.search(
            r'(https://vgmrips\.net/packs/images/small/[^\s"\'<>]+\.png)', page_html
        )
        if small:
            return small.group(1).replace('/small/', '/large/')
        return None

    def _try_search(query: str) -> str | None:
        q = urllib.parse.quote_plus(query)
        try:
            req = urllib.request.Request(
                f"https://vgmrips.net/packs/search/?q={q}", headers=_HEADERS
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')

            if 'No results' in html and 'no results' in html.lower():
                return None

            # Case 1: direct pack page — has large/small image + <title>
            img = _extract_image(html)
            if img:
                title_tag = re.search(r'<title>([^<]+)</title>', html)
                if title_tag and not _title_matches_query(
                    {"title": title_tag.group(1)}, game_name
                ):
                    return None
                return img

            # Case 2: disambiguation/list page — follow /packs/pack/ links
            pack_links = re.findall(r'href="(/packs/pack/[^"]+)"', html)
            seen: set = set()
            for link in pack_links:
                if link in seen:
                    continue
                seen.add(link)
                slug_name = link.split('/packs/pack/')[-1].replace('-', ' ')
                if not _title_matches_query({"slug": slug_name}, game_name):
                    continue
                try:
                    req2 = urllib.request.Request(
                        f"https://vgmrips.net{link}", headers=_HEADERS
                    )
                    with urllib.request.urlopen(req2, timeout=10) as resp2:
                        pack_html = resp2.read().decode('utf-8', errors='ignore')
                    img = _extract_image(pack_html)
                    if img:
                        return img
                except Exception:
                    continue
        except Exception:
            pass
        return None

    try:
        for query in queries:
            result = _try_search(query)
            if result:
                return result
    except Exception:
        pass
    return None



# ---------------------------------------------------------------------------
# Source 5: MobyGames (box art scans for all retro platforms)
# ---------------------------------------------------------------------------

def resolve_mobygames_artwork(game_name: str) -> str | None:
    """
    Fetches front box art from MobyGames.
    Covers virtually all platforms — SMS, NES, SNES, Genesis, PS1, etc.
    Prefers front cover scans over title screens.
    """
    query = urllib.parse.quote_plus(game_name)
    search_url = f"https://www.mobygames.com/search/?q={query}&type=game"
    try:
        req = urllib.request.Request(search_url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # Extract first game ID: /game/{id}/{slug}/
        game_match = re.search(
            r'href=["\']https://www\.mobygames\.com/game/(\d+)/([^\s"\'<>]+/)["\']',
            html
        )
        if not game_match:
            return None

        game_id, game_slug = game_match.group(1), game_match.group(2)
        covers_url = f"https://www.mobygames.com/game/{game_id}/{game_slug}covers/"
        req2 = urllib.request.Request(covers_url, headers=_HEADERS)
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            covers_html = resp2.read().decode('utf-8', errors='ignore')

        # Prefer front cover
        front = re.search(
            r'(https://cdn\.mobygames\.com/covers/[^\s"\'<>]*front[^\s"\'<>]*\.(?:jpg|png))',
            covers_html, re.IGNORECASE
        )
        if front:
            return front.group(1)

        # Any cover
        any_cover = re.search(
            r'(https://cdn\.mobygames\.com/covers/[^\s"\'<>]+\.(?:jpg|png))',
            covers_html
        )
        if any_cover:
            return any_cover.group(1)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Source 6: Sega Retro (box art for Sega platform games — bot-gated, best-effort)
# ---------------------------------------------------------------------------

def resolve_sega_retro_artwork(game_name: str) -> str | None:
    """
    Fetches box front art from Sega Retro wiki (segaretro.org).
    Note: Site uses Anubis JS challenge — this only works when the challenge is
    not active (some IPs/times pass through). Best-effort last resort.
    """
    wiki_title = re.sub(r'\s+', '_', game_name.strip())
    page_url = f"https://segaretro.org/{urllib.parse.quote(wiki_title)}"
    try:
        req = urllib.request.Request(page_url, headers={
            **_HEADERS,
            "Referer": "https://segaretro.org/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        box_match = re.search(
            r'(https://segaretro\.org/images/(?:thumb/)?[a-f0-9/]+/[^\s"\']*?'
            r'(?:box|cover|front)[^\s"\']*?\.(?:jpg|png))'
            r'(?:/\d+px-[^\s"\']*)?',
            html, re.IGNORECASE
        )
        if box_match:
            return re.sub(r'/thumb/', '/', box_match.group(1))

        img_match = re.search(
            r'https://segaretro\.org/images/[a-f0-9/]+/[^\s"\']+\.(?:jpg|png)',
            html
        )
        if img_match:
            return img_match.group(0)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Source 6: MusicBrainz Cover Art Archive (non-VGM: bands, artists)
# ---------------------------------------------------------------------------

def resolve_musicbrainz_artwork(query: str) -> str | None:
    """
    Fetches cover art from MusicBrainz Cover Art Archive.
    Best for non-VGM content (MGMT, Tool, etc.). No API key required.
    query: "Artist Album" e.g. "MGMT Oracular Spectacular"
    """
    try:
        search_url = (
            "https://musicbrainz.org/ws/2/release/"
            f"?query={urllib.parse.quote_plus(query)}&fmt=json&limit=1"
        )
        req = urllib.request.Request(search_url, headers={
            **_HEADERS,
            "User-Agent": "HelixMusicIndex/1.0 (helix@local)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        releases = data.get("releases", [])
        if not releases:
            return None
        mbid = releases[0]["id"]
        # CAA front-500 redirects to the actual image
        return f"https://coverartarchive.org/release/{mbid}/front-500"
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Main resolver — full source chain
# ---------------------------------------------------------------------------

def resolve_artwork(game_name: str, source_class: str = "vgm_original") -> tuple[str | None, str]:
    """
    Resolves the best available artwork URL for game_name.

    source_class:
      "vgm_original" — VGM game folder
                        Chain: IGN → VGMdb → SNESmusic → VGMrips
      "non_vgm"      — Commercial music (bands, anime, film soundtracks)
                        Chain: MusicBrainz Cover Art Archive

    Returns: (url, source_name) or (None, "none")
    """
    if source_class == "non_vgm":
        url = resolve_musicbrainz_artwork(game_name)
        return (url, "musicbrainz_caa") if url else (None, "none")

    # --- VGM chain ---
    # 1. IGN — clean digital key art, always preferred
    url = _resolve_ign(game_name)
    if url:
        return url, "ign"

    # 2. VGMdb — official OST cover art
    url = resolve_vgmdb_artwork(game_name)
    if url:
        return url, "vgmdb"

    # 3. SNESmusic — title screens (SNES)
    url = resolve_snesmusic_artwork(game_name)
    if url:
        return url, "snesmusic"

    # 4. VGMrips — title screens (NES, Genesis, Game Boy, arcade, etc.)
    url = resolve_vgmrips_artwork(game_name)
    if url:
        return url, "vgmrips"

    return None, "none"


def autonomously_resolve_art(game_name: str) -> str | None:
    """
    Backward-compatible wrapper. Returns URL only (no source).
    Callers that need the source should use resolve_artwork() directly.
    """
    url, _ = resolve_artwork(game_name, source_class="vgm_original")
    return url
