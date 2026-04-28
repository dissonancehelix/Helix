"""
library_pipeline.py — Helix Music Library Pipeline
====================================================
Three-stage pipeline for ingesting and analyzing the Helix music library.

Stage 1 — Ingest (from ingest_library.py)
    Scans C:\\Users\\dissonance\\Music and ingests all audio tracks into
    codex/library/music/ following SCHEMA.json v3.0.

    Filename conventions understood:
      Multi-disc:    1.01 - Title.ext   (disc 1, track 01)
      Single-disc:   01 - Title.ext     (track 01)

    Metadata priority order (highest → lowest):
      1. APEv2 .tag sidecar file (authoritative for VGM/SPC — Foobar external tags)
         GD3 and ID666 native tags are intentionally ignored.
      2. Embedded tags via mutagen (MP3, FLAC, Opus, etc.)
      3. Filename parsing (track number, title)
      4. Path inference (album = parent folder)

    Loved status: bootstrapped from m3u8 export on first ingest.
      Stored in library JSONs going forward — m3u8 file not required after initial run.

Stage 2 — Index (from build_field_index.py)
    Scans the library once and produces .field_index.json — a cached
    inverted index for fast field-based queries (artist, format, loved, album).
    Run this after every ingest run.

Stage 3 — Analyze (from analyze_library.py)
    Batch-analyzes all (or a filtered subset of) tracks in the Helix library.
    The pipeline is embarrassingly parallel per track — each file is independent.
    Uses multiprocessing to saturate CPU cores.
    Resume-safe: tracks with analysis already written are skipped unless --force.
    Progress is checkpointed to artifacts/analysis/.library_progress.json.

Usage:
    python domains/music/model/probes/library_pipeline.py                   # all stages
    python domains/music/model/probes/library_pipeline.py --stage ingest    # ingest only
    python domains/music/model/probes/library_pipeline.py --stage index     # index only
    python domains/music/model/probes/library_pipeline.py --stage analyze   # analyze only

    # Ingest flags:
    python domains/music/model/probes/library_pipeline.py --stage ingest --dry-run
    python domains/music/model/probes/library_pipeline.py --stage ingest --limit 500
    python domains/music/model/probes/library_pipeline.py --stage ingest --loved-only

    # Analyze flags:
    python domains/music/model/probes/library_pipeline.py --stage analyze --fmt-cat hardware_log sequence
    python domains/music/model/probes/library_pipeline.py --stage analyze --album sonic_3_knuckles
    python domains/music/model/probes/library_pipeline.py --stage analyze --artist "Jun Senoue"
    python domains/music/model/probes/library_pipeline.py --stage analyze --workers 4

Throughput estimates (analyze stage, rough — depends on format and hardware):
    VGM/VGZ (hardware_log):  ~80-150 tracks/min per worker (parse + symbolic)
    SPC/mini* (sequence):    ~50-100 tracks/min per worker
    MP3/Opus (audio):        ~20-40 tracks/min per worker (render + MIR)

At 4 workers on VGM-only corpus (~40k tracks):  ~60-90 minutes
At 4 workers on full 122k library:              ~4-8 hours
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Optional


def _optimal_workers() -> int:
    """Derive worker count from available RAM and CPU cores.

    Each worker holds madmom neural-net weights (~300 MB) plus audio buffers
    (~200 MB peak), so budget ~500 MB per worker.  Cap at 2× logical CPU count
    to avoid context-switch overhead on CPU-bound inference.
    """
    try:
        import psutil
        available_mb = psutil.virtual_memory().available // (1024 * 1024)
    except ImportError:
        available_mb = 4096  # conservative fallback if psutil missing

    physical_cores = max(1, (os.cpu_count() or 8) // 2)  # physical cores (undo HT)
    ram_limit  = max(1, available_mb // 500)
    core_limit = max(1, physical_cores - 1)  # leave 1 physical core for OS/UI
    return min(ram_limit, core_limit)

# Suppress madmom deprecation warnings (madmom 0.17 method= param, NumPy 2.4 dtype align)
warnings.filterwarnings("ignore", category=UserWarning, module="madmom")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="madmom")
warnings.filterwarnings("ignore", message=".*align.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*histogram_processor.*")

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
sys.path.insert(0, str(ROOT))

# ── Paths ─────────────────────────────────────────────────────────────────────
LIB_ROOT     = ROOT / "codex" / "library" / "music"
MUSIC_ROOT   = Path(r"C:\Users\dissonance\Music")
LOVED_M3U8   = Path(r"C:\Users\dissonance\Desktop\loved m3u8.m3u8")  # bootstrap only — not required after first ingest
LIB_ALBUM    = LIB_ROOT / "album"
ARTIFACTS    = ROOT / "domains" / "language" / "artifacts" / "analysis"
PROGRESS     = ARTIFACTS / ".library_progress.json"
ERROR_LOG    = ARTIFACTS / ".errors.jsonl"
IDX_OUT_PATH = LIB_ROOT / ".field_index.json"

# ── Optional mutagen ───────────────────────────────────────────────────────────
try:
    import mutagen
    from mutagen import File as MutagenFile
    MUTAGEN = True
except ImportError:
    MUTAGEN = False
    print("NOTE: mutagen not installed — using filename/path metadata only.")
    print("      pip install mutagen  for embedded tag support.")

# ── Audio extensions ───────────────────────────────────────────────────────────
AUDIO_EXTS = {
    '.mp3', '.flac', '.opus', '.ogg', '.m4a', '.aac', '.wav', '.wma',
    '.vgm', '.vgz', '.spc', '.nsf', '.nsfe', '.gbs', '.hes',
    '.psf', '.psf2', '.dsf', '.ssf', '.usf', '.gsf', '.ncsf',
    '.mid', '.gym', '.s98', '.ay', '.sid',
    # Mini-sequenced container formats (actual audio tracks, not libraries)
    '.mini2sf',   # Nintendo DS
    '.miniusf',   # Nintendo 64
    '.minincsf',  # Nintendo DS (alternate)
    '.minigsf',   # Game Boy Advance
    '.minipsf',   # PlayStation
}

FORMAT_CATEGORY = {
    'vgm': 'hardware_log', 'vgz': 'hardware_log', 'spc': 'hardware_log',
    'nsf': 'hardware_log', 'nsfe': 'hardware_log', 'gbs': 'hardware_log',
    'hes': 'hardware_log', 'gym': 'hardware_log', 's98': 'hardware_log',
    'psf':  'sequence', 'psf2': 'sequence',  'dsf':  'sequence',
    'ssf':  'sequence', 'usf':  'sequence',  'gsf':  'sequence',
    'ncsf': 'sequence', 'mid':  'sequence',
    # Mini formats — sequenced, emulated
    'mini2sf':  'sequence', 'miniusf':   'sequence',
    'minincsf': 'sequence', 'minigsf':   'sequence',
    'minipsf':  'sequence',
    'mp3': 'audio', 'flac': 'audio', 'opus': 'audio', 'ogg': 'audio',
    'm4a': 'audio', 'aac':  'audio', 'wav':  'audio', 'wma': 'audio',
}


# =============================================================================
# STAGE 1: INGEST
# =============================================================================

def slugify(text: str) -> str:
    if not text:
        return "unknown"
    s = str(text).lower().strip()
    s = re.sub(r"['\u2019\u2018`]", "", s)
    s = re.sub(r"[\s\-\/;,:\.&!?\(\)\[\]\{\}]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_") or "unknown"


def album_id(album_name: str) -> str:
    return f"music.album.{slugify(album_name)}"


def artist_id(artist_name: str) -> str:
    return f"music.artist.{slugify(artist_name)}"


def track_id(album_name: str, track_num: Optional[int], title: str) -> str:
    alb_slug = slugify(album_name)
    t_slug   = slugify(title)
    if track_num is not None:
        return f"music.track.{alb_slug}.{str(track_num).zfill(2)}_{t_slug}"
    return f"music.track.{alb_slug}.{t_slug}"


# Matches: 1.01 - Title  or  01 - Title
_MULTI  = re.compile(r'^(\d+)\.(\d+)\s*[-–]\s*(.+)$')
_SINGLE = re.compile(r'^(\d+)\s*[-–]\s*(.+)$')


def parse_filename(stem: str) -> tuple[Optional[int], Optional[int], str]:
    """Returns (disc_number, track_number, title)."""
    m = _MULTI.match(stem)
    if m:
        return int(m.group(1)), int(m.group(2)), m.group(3).strip()
    m = _SINGLE.match(stem)
    if m:
        return None, int(m.group(1)), m.group(2).strip()
    return None, None, stem


def _tag(tags, *keys: str) -> Optional[str]:
    if not tags:
        return None
    for k in keys:
        v = tags.get(k) or tags.get(k.upper()) or tags.get(k.lower())
        if v:
            if isinstance(v, list):
                v = v[0]
            s = str(v).strip()
            if s:
                return s
    return None

def _tag_multi(tags, *keys: str) -> Optional[str]:
    if not tags:
        return None
    for k in keys:
        v = tags.get(k) or tags.get(k.upper()) or tags.get(k.lower())
        if v:
            if isinstance(v, list):
                return "\x00".join(str(i).strip() for i in v if str(i).strip())
            s = str(v).strip()
            if s:
                return s
    return None




# The FoobarAdapter handles the central external-tags plane.
_foobar_adapter = None
def _get_foobar_meta(path: Path) -> dict:
    global _foobar_adapter
    if _foobar_adapter is None:
        import sqlite3
        from model.domains.music.ingestion.config import FOOBAR_APPDATA
        db_path = Path(r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\external-tags.db")
        if not db_path.exists():
            return {}
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT meta FROM tags WHERE path = ?", (f"file://{path}",))
            row = cur.fetchone()
            conn.close()
            if row:
                from model.domains.music.ingestion.adapters.foobar import decode_fb2k_meta
                return decode_fb2k_meta(row[0])
        except Exception:
            pass
    return {}

def read_tags(path: Path) -> dict:
    """
    Read tags for a file. Priority:
      1. external-tags.db (Foobar external tags — authoritative for all music)
      2. Embedded tags via mutagen (for MP3, FLAC, Opus, etc.)
    """
    # Foobar external-tags.db takes priority
    fb_tags = _get_foobar_meta(path)
    if fb_tags:
        return fb_tags
    
    # Fallback: embedded tags (MP3, FLAC, Opus, etc.)
    if not MUTAGEN:
        return {}
    try:
        f = MutagenFile(path, easy=True)
        if not f:
            return {}
        # Flatten mutagen tag values to strings
        flat = {}
        for k, v in dict(f).items():
            if isinstance(v, list):
                flat[k.lower()] = str(v[0]).strip() if v else ''
            else:
                flat[k.lower()] = str(v).strip()
        return flat
    except Exception:
        return {}


def infer_from_path(file_path: Path) -> dict:
    """
    Infer metadata from directory structure.

    VGM layout:   Music/VGM/<letter>/<Game>/<files>
    Others layout: Music/Others/<genre>/<Artist>/<Album>/<files>
                   Music/Anime/<Title>/<files>
                   Music/Film/<Title>/<files>
    """
    parts = file_path.relative_to(MUSIC_ROOT).parts
    result = {
        "album":        None,
        "artist":       None,
        "album_artist": None,
        "genre":        None,
        "platform":     None,
        "sound_team":   None,
    }

    if not parts:
        return result

    category = parts[0]  # VGM, Others, Anime, Film

    if category == "VGM":
        parent = file_path.parent.name
        if re.match(r'^(disc|cd|disk)\s*\d+$', parent, re.IGNORECASE):
            parent = file_path.parent.parent.name
        result["album"]  = parent
        result["genre"]  = "VGM"
    elif category == "Others":
        parent = file_path.parent.name
        if re.match(r'^(disc|cd|disk)\s*\d+$', parent, re.IGNORECASE):
            parent = file_path.parent.parent.name
        result["album"] = parent
        if len(parts) >= 3:
            result["genre"] = parts[1]
        if len(parts) >= 4:
            result["artist"] = parts[2]
    elif category in ("Anime", "Film"):
        parent = file_path.parent.name
        if re.match(r'^(disc|cd|disk)\s*\d+$', parent, re.IGNORECASE):
            parent = file_path.parent.parent.name
        result["album"] = parent
        result["genre"] = category

    return result


def split_tag_list(value: Optional[str]) -> list:
    """Split a tag value that may contain multiple entries (newline or slash separated)."""
    if not value:
        return []
    parts = re.split(r'[\n/,]+', value)
    return [p.strip() for p in parts if p.strip()]


def load_loved_paths(m3u8_path: Path) -> set[str]:
    """Load file paths from the loved m3u8 into a normalized set."""
    if not m3u8_path.exists():
        print(f"WARNING: Loved m3u8 not found at {m3u8_path}")
        return set()
    loved = set()
    with open(m3u8_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                loved.add(line.replace('\\', '/').lower())
    print(f"Loaded {len(loved)} loved paths from m3u8")
    return loved


def is_loved(file_path: Path, loved_paths: set[str]) -> bool:
    norm = str(file_path).replace('\\', '/').lower()
    return norm in loved_paths


def build_track_record(file_path: Path, loved_paths: set[str]) -> dict:
    """Build a full SCHEMA.json v3.0 track record for a single file."""
    ext = file_path.suffix.lstrip('.').lower()
    stem = file_path.stem

    disc_num, track_num, fname_title = parse_filename(stem)
    tags = read_tags(file_path)
    inferred = infer_from_path(file_path)

    title        = _tag(tags, 'title')        or fname_title
    artist       = _tag_multi(tags, 'artist')       or inferred["artist"] or "Unknown Artist"
    album        = _tag(tags, 'album')        or inferred["album"]  or file_path.parent.name
    album_artist = _tag_multi(tags, 'albumartist', 'album_artist', 'album artist') or artist
    date         = _tag(tags, 'date', 'year') or ""
    genre        = _tag_multi(tags, 'genre')        or inferred["genre"]  or ""
    featuring    = _tag_multi(tags, 'featuring', 'FEATURING', 'featured', 'featured_on') or ""
    sound_team   = _tag_multi(tags, 'sound team', 'soundteam', 'sound_team') or inferred["sound_team"] or ""
    sound_chip   = _tag_multi(tags, 'sound chip', 'soundchip', 'sound_chip') or ""
    chips        = split_tag_list(sound_chip)

    tn_tag = _tag(tags, 'tracknumber', 'track')
    if tn_tag:
        try:
            track_num = int(tn_tag.split('/')[0])
        except (ValueError, AttributeError):
            pass

    dn_tag = _tag(tags, 'discnumber', 'disc')
    if dn_tag:
        try:
            disc_num = int(dn_tag.split('/')[0])
        except (ValueError, AttributeError):
            pass

    total_tracks = _tag(tags, 'totaltracks', 'tracktotal') or ""
    total_discs  = _tag(tags, 'totaldiscs',  'disctotal')  or ""

    loved = is_loved(file_path, loved_paths)
    alb_id = album_id(album)
    art_id = artist_id(artist)
    trk_id = track_id(album, track_num, title)
    fmt_cat = FORMAT_CATEGORY.get(ext, 'audio')

    record = {
        "id":   trk_id,
        "type": "Track",
        "name": title,
        "metadata": {
            "title":        title,
            "album":        album,
            "album_id":     alb_id,
            "game":         None,
            "franchise_id": None,
            "platform":     None,
            "platform_id":  None,
            "year":         date,
            "artist":       artist,
            "artist_ids":   [art_id],
            "featuring":    featuring or None,
            "album_artist": album_artist,
            "sound_team":   sound_team or None,
            "sound_team_ids": [],
            "track_number": track_num,
            "total_tracks": int(total_tracks) if str(total_tracks).isdigit() else None,
            "disc_number":  disc_num,
            "total_discs":  int(total_discs)  if str(total_discs).isdigit()  else None,
            "genre":        genre or None,
            "format":       ext,
            "format_category": fmt_cat,
            "region":       None,
            "arrangement_type": "original",
            "version_type": "final",
            "prototype_status": None,
            "source":       str(file_path),
            "source_artifact_refs": [],
            "tags":         [],
            "library_state": {
                "_note": "DEPRECATED: move to listener overlay.",
                "loved": loved,
            },
            "metadata_sources": {
                "title":  "tag_file" if _tag(tags, 'title') else "filename",
                "artist": "tag_file" if _tag(tags, 'artist') else "path_inference",
                "source": "disk_scan",
                "loved":  "m3u8" if loved else "none",
            },
        },
        "hardware": {
            "_note": "Static playback substrate facts.",
            "chips":        chips,
            "driver":       None,
            "has_loop":     None,
            "loop_start_s": None,
            "loop_end_s":   None,
            "duration_s":   None,
        },
        "substrate": {
            "_chip": None,
            "_confidence": 0.0,
        },
        "causal": {
            "_status": "unavailable" if fmt_cat == "audio" else "pending",
            "_source": None,
            "chip_target": None,
            "channel_layout": {},
            "loop_point_position": None,
            "return_passage_structure": {},
            "causal_trace_ref": None,
        },
        "pitch_harmony": {"_status": "pending"},
        "rhythm_form": {
            "_status": "pending",
            "has_loop":                   None,
            "has_distinct_return_passage": None,
            "loop_behavior_type":         None,
            "loop_continuity_strength":   None,
            "return_passage_prominence":  None,
            "return_passage_type":        None,
            "return_passage_confidence":  None,
            "loop_morphology":            None,
        },
        "orchestration": {"_status": "pending"},
        "style_fingerprint": {"_status": "pending"},
        "dcp": {
            "_status": "pending",
            "_source": None,
            "_confidence": None,
        },
        "attribution": {
            "_status": "pending",
            "composition_credit": {
                "artist_ids": [art_id],
                "label": "unknown",
                "confidence": 0.0,
                "source": "tag_file" if _tag(tags, 'artist') else "path_inference",
            },
        },
        "analysis": {
            "analysis_tier": None,
            "pipeline_version": None,
            "coverage": {
                "perceptual_coverage": None,
                "symbolic_coverage":   None,
                "causal_coverage":     None,
            },
            "causal_complete":      False,
            "symbolic_complete":    False,
            "perceptual_complete":  False,
            "fingerprint_complete": False,
            "dcp_complete":         False,
            "confidence":           0.0,
            "last_analyzed":        None,
        },
        "relationships": [],
    }
    return record


def record_hash(record: dict) -> str:
    key = {
        "title":       record["metadata"]["title"],
        "album":       record["metadata"]["album"],
        "track_number": record["metadata"]["track_number"],
        "disc_number": record["metadata"]["disc_number"],
        "source":      record["metadata"]["source"],
    }
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:12]


def track_output_path(record: dict) -> Path:
    alb_id_str = record["metadata"]["album_id"]
    alb_slug   = ".".join(alb_id_str.split(".")[2:])
    tn         = record["metadata"]["track_number"]
    dn         = record["metadata"]["disc_number"]
    title_slug = slugify(record["metadata"]["title"])

    if dn:
        filename = f"{dn}.{str(tn).zfill(2)}_{title_slug}.json" if tn else f"{dn}.00_{title_slug}.json"
    elif tn:
        filename = f"{str(tn).zfill(2)}_{title_slug}.json"
    else:
        filename = f"{title_slug}.json"

    return LIB_ALBUM / alb_slug / filename


def write_record(record: dict, dry_run: bool) -> bool:
    out_path = track_output_path(record)
    if dry_run:
        return True
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve existing analysis if file already exists
    if out_path.exists():
        try:
            old = json.loads(out_path.read_text(encoding='utf-8'))
            if old.get("analysis"):
                record["analysis"] = old["analysis"]
        except Exception:
            pass
    out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
    return True


def run_ingest(
    music_root: Path = MUSIC_ROOT,
    dry_run: bool = False,
    limit: Optional[int] = None,
    loved_only: bool = False,
    only_exts: Optional[str] = None,
) -> None:
    """Stage 1: Scan music root and ingest all audio tracks into the Helix library."""
    if not music_root.exists():
        print(f"ERROR: Music root not found: {music_root}")
        sys.exit(1)

    print(f"Helix Library Ingestion v2")
    print(f"  Music root:  {music_root}")
    print(f"  Library out: {LIB_ROOT}")

    if only_exts:
        active_exts = {e.strip().lower() if e.strip().startswith('.') else '.' + e.strip().lower()
                       for e in only_exts.split(',')}
        active_exts &= AUDIO_EXTS
    else:
        active_exts = AUDIO_EXTS

    print(f"  Dry run:     {dry_run}")
    print(f"  Loved only:  {loved_only}")
    print(f"  Extensions:  {', '.join(sorted(active_exts)) if only_exts else 'all'}")
    print()

    loved_paths = load_loved_paths(LOVED_M3U8)

    t0 = time.time()
    count = skipped = errors = loved_count = 0

    for dirpath, dirnames, filenames in os.walk(music_root):
        dirnames.sort()
        for fname in sorted(filenames):
            ext = Path(fname).suffix.lower()
            if ext not in active_exts:
                continue

            file_path = Path(dirpath) / fname
            loved = is_loved(file_path, loved_paths)
            if loved_only and not loved:
                skipped += 1
                continue

            try:
                record = build_track_record(file_path, loved_paths)
                write_record(record, dry_run=dry_run)
                count += 1
                if loved:
                    loved_count += 1
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"  ERROR: {file_path}: {e}")
                continue

            if count % 5000 == 0:
                elapsed = time.time() - t0
                rate = count / elapsed if elapsed > 0 else 0
                print(f"  {count:>7,} tracks  ({rate:.0f}/s)  loved={loved_count}  errors={errors}")

            if limit and count >= limit:
                print(f"  Limit of {limit} reached.")
                break
        else:
            continue
        break

    elapsed = time.time() - t0
    print()
    print(f"Done in {elapsed:.1f}s")
    print(f"  Tracks written: {count:,}")
    print(f"  Loved:          {loved_count:,}")
    print(f"  Skipped:        {skipped:,}")
    print(f"  Errors:         {errors:,}")
    if dry_run:
        print("  (DRY RUN — no files written)")


# =============================================================================
# STAGE 2: INDEX
# =============================================================================

def run_index() -> dict:
    """Stage 2: Build field index for fast field-based queries over the library."""
    from collections import defaultdict

    t0 = time.time()
    print("Building field index...")

    by_artist:     dict[str, list[str]] = defaultdict(list)
    by_sound_team: dict[str, list[str]] = defaultdict(list)
    by_fmt_cat:    dict[str, list[str]] = defaultdict(list)
    by_album:      dict[str, list[str]] = defaultdict(list)
    by_featuring:  dict[str, list[str]] = defaultdict(list)
    by_loved:      list[str] = []
    source_map:    dict[str, str] = {}

    count = 0
    for jf in sorted(LIB_ALBUM.rglob("*.json")):
        if jf.name == "album.json":
            continue
        try:
            obj  = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
            meta = obj.get("metadata", {})
            tid  = obj.get("id")
            if not tid:
                continue

            artist   = meta.get("artist", "").lower().strip()
            fmt_cat  = meta.get("format_category", "").strip()
            album    = meta.get("album_id", meta.get("album", "")).lower().strip()
            source   = meta.get("source", "")
            loved    = meta.get("library_state", {}).get("loved", False)

            sound_team = meta.get("sound_team", "").lower().strip()
            featuring  = meta.get("featuring") or ""

            if artist:
                by_artist[artist].append(tid)
            if featuring:
                for feat_name in re.split(r"[\x00;\n,]", featuring):
                    feat_key = feat_name.strip().lower()
                    if feat_key:
                        by_featuring[feat_key].append(tid)
            if sound_team:
                by_sound_team[sound_team].append(tid)
            if fmt_cat:
                by_fmt_cat[fmt_cat].append(tid)
            if album:
                by_album[album].append(tid)
            if loved:
                by_loved.append(tid)
            if source:
                source_map[tid] = source

            count += 1
            if count % 20000 == 0:
                print(f"  {count:,} records scanned...")
        except Exception:
            continue

    import datetime
    index = {
        "_meta": {
            "built_at": datetime.datetime.now().isoformat(),
            "track_count": count,
            "loved_count": len(by_loved),
        },
        "by_artist":     dict(by_artist),
        "by_sound_team": dict(by_sound_team),
        "by_fmt_cat":    dict(by_fmt_cat),
        "by_album":      dict(by_album),
        "by_featuring":  dict(by_featuring),
        "by_loved":      by_loved,
        "source_map":    source_map,
    }

    IDX_OUT_PATH.write_text(json.dumps(index, indent=1), encoding="utf-8")
    elapsed = time.time() - t0

    print(f"\nField index built in {elapsed:.1f}s")
    print(f"  Tracks indexed:   {count:,}")
    print(f"  Unique artists:   {len(by_artist):,}")
    print(f"  Format cats:      {list(by_fmt_cat.keys())}")
    print(f"  Albums:           {len(by_album):,}")
    print(f"  Loved tracks:     {len(by_loved):,}")
    print(f"  Written to:       {IDX_OUT_PATH}")
    return index


# =============================================================================
# STAGE 3: ANALYZE
# =============================================================================

def collect_tracks(
    fmt_cats: set[str] | None,
    album_slug: str | None,
    artist_filter: str | None,
    loved_only: bool,
    force: bool,
) -> list[dict]:
    """Walk library JSONs and collect tracks matching the filters.

    Fast path: when artist_filter is given (and no album_slug / loved_only),
    uses the field index source_map + by_artist for O(1) lookup instead of
    walking all album JSONs.  Falls back to the full walk otherwise.
    """
    already_done: set[str] = set()
    if not force and PROGRESS.exists():
        try:
            done = json.loads(PROGRESS.read_text(encoding="utf-8"))
            already_done = set(done.get("completed", []))
        except Exception:
            pass

    # ── Fast path: artist-only filter with field index ────────────────────────
    if artist_filter and not album_slug and not loved_only and IDX_OUT_PATH.exists():
        try:
            idx        = json.loads(IDX_OUT_PATH.read_text(encoding="utf-8"))
            by_artist  = idx.get("by_artist", {})
            source_map = idx.get("source_map", {})
            needle     = artist_filter.lower()

            candidate_ids: set[str] = set()
            for artist_key, tids in by_artist.items():
                if needle in artist_key:
                    candidate_ids.update(tids)

            tracks: list[dict] = []
            for t_id in sorted(candidate_ids):
                if t_id in already_done and not force:
                    continue
                source = source_map.get(t_id, "")
                if not source or not Path(source).exists():
                    continue
                ext     = Path(source).suffix.lstrip(".").lower()
                fmt_cat = FORMAT_CATEGORY.get(ext, "audio")
                if fmt_cats and fmt_cat not in fmt_cats:
                    continue
                src_path = Path(source)
                tracks.append({
                    "id":      t_id,
                    "source":  source,
                    "fmt_cat": fmt_cat,
                    "title":   src_path.stem,
                    "album":   src_path.parent.name,
                    "artist":  artist_filter,
                })
            return tracks
        except Exception:
            pass  # fall through to slow path on any error

    # ── Slow path: full album JSON walk ───────────────────────────────────────
    tracks = []
    search_root = LIB_ALBUM / album_slug if album_slug else LIB_ALBUM

    for jf in sorted(search_root.rglob("*.json")):
        if jf.name == "album.json":
            continue
        try:
            obj  = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
            meta = obj.get("metadata", {})
            t_id = obj.get("id", jf.stem)
            source   = meta.get("source", "")
            fmt_cat  = meta.get("format_category", "")
            artist   = meta.get("artist", "").lower()
            loved    = meta.get("library_state", {}).get("loved", False)

            if not source or not Path(source).exists():
                continue
            if fmt_cats and fmt_cat not in fmt_cats:
                continue
            if artist_filter and artist_filter.lower() not in artist:
                continue
            if loved_only and not loved:
                continue
            if t_id in already_done and not force:
                continue

            tracks.append({
                "id":      t_id,
                "source":  source,
                "fmt_cat": fmt_cat,
                "title":   meta.get("title", ""),
                "album":   meta.get("album", ""),
                "artist":  meta.get("artist", ""),
            })
        except Exception:
            continue

    return tracks


def _analyze_one(task: dict) -> dict:
    """Worker function — runs in a subprocess."""
    import sys
    sys.path.insert(0, str(ROOT))

    t_id   = task["id"]
    source = task["source"]

    try:
        from model.domains.music.analysis.codec_pipeline import analyze
        result     = analyze(source)
        result_d   = result.to_dict() if hasattr(result, "to_dict") else vars(result)
        error      = result_d.get("error", "")

        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        slug_file = t_id.replace(":", "_").replace(".", "_")
        out = ARTIFACTS / f"{slug_file}.json"
        out.write_text(
            json.dumps({"entity_id": t_id, "source": source, "analysis": result_d},
                       indent=2, default=str),
            encoding="utf-8"
        )
        return {"id": t_id, "source": source, "ok": not error, "error": error}
    except Exception as e:
        return {"id": t_id, "source": source, "ok": False, "error": str(e)}


def _save_progress(completed: list[str], errors: list[dict]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(
        json.dumps({"completed": completed, "errors": errors}, indent=2),
        encoding="utf-8"
    )
    # Write errors to a flat JSONL file for easy review / grep
    if errors:
        with ERROR_LOG.open("w", encoding="utf-8") as f:
            for e in errors:
                f.write(json.dumps(e) + "\n")


def run_analyze(
    fmt_cats: set[str] | None = None,
    album_slug: str | None = None,
    artist_filter: str | None = None,
    loved_only: bool = False,
    force: bool = False,
    dry_run: bool = False,
    workers: int = _optimal_workers(),
    limit: Optional[int] = None,
) -> None:
    """Stage 3: Batch-analyze library tracks (multiprocessing, resume-safe)."""
    print("Helix Library Analysis Runner")
    print(f"  Format cats:  {fmt_cats or 'all'}")
    print(f"  Album:        {album_slug or 'all'}")
    print(f"  Artist:       {artist_filter or 'all'}")
    print(f"  Loved only:   {loved_only}")
    print(f"  Workers:      {workers}  (auto from RAM+CPU)")
    print(f"  Force:        {force}")
    print(f"  Dry run:      {dry_run}")

    print("\nCollecting tracks...")
    tracks = collect_tracks(
        fmt_cats=fmt_cats,
        album_slug=album_slug,
        artist_filter=artist_filter,
        loved_only=loved_only,
        force=force,
    )

    if limit:
        tracks = tracks[:limit]

    print(f"  {len(tracks):,} tracks to analyze")
    if not tracks:
        print("  Nothing to do.")
        return

    if dry_run:
        print("\n[Dry run — first 10 tracks:]")
        for t in tracks[:10]:
            print(f"  [{t['fmt_cat']}] {t['album']} — {t['title']}")
            print(f"    {t['id']}")
        print(f"  ... ({len(tracks)} total)")
        return

    t0 = time.time()
    completed: list[str] = []
    errors:    list[dict] = []
    ok_count = 0

    total = len(tracks)

    def _print_progress(i: int, ok: int, errs: int) -> None:
        elapsed = time.time() - t0
        rate = i / elapsed * 60 if elapsed > 0 else 0
        pct = i / total * 100
        eta_min = (total - i) / (i / elapsed) / 60 if elapsed > 0 and i > 0 else 0
        bar_w = 30
        filled = int(bar_w * i / total)
        bar = "█" * filled + "░" * (bar_w - filled)
        line = (f"\r  [{bar}] {pct:5.1f}%  {i:>7,}/{total:,}  "
                f"{rate:6.0f}/min  ETA {eta_min:.0f}m  ok={ok:,}  err={errs}")
        print(line, end="", flush=True)

    if workers == 1:
        for i, task in enumerate(tracks, 1):
            result = _analyze_one(task)
            if result["ok"]:
                completed.append(result["id"])
                ok_count += 1
            else:
                errors.append(result)
            if i % 50 == 0 or i == total:
                _print_progress(i, ok_count, len(errors))
                if i % 1000 == 0:
                    _save_progress(completed, errors)
    else:
        with mp.Pool(workers) as pool:
            for i, result in enumerate(pool.imap_unordered(_analyze_one, tracks), 1):
                if result["ok"]:
                    completed.append(result["id"])
                    ok_count += 1
                else:
                    errors.append(result)
                if i % 50 == 0 or i == total:
                    _print_progress(i, ok_count, len(errors))
                    if i % 1000 == 0:
                        _save_progress(completed, errors)
    print()  # newline after progress bar

    _save_progress(completed, errors)
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed/60:.1f} min")
    print(f"  OK:     {ok_count:,}")
    print(f"  Errors: {len(errors):,}")
    print(f"  Rate:   {len(tracks)/elapsed*60:.0f} tracks/min")
    if errors:
        # Group errors by file extension for easy second-pass targeting
        from collections import Counter
        ext_errs: Counter = Counter()
        for e in errors:
            src = e.get("source", e.get("id", ""))
            ext = Path(src).suffix.lower() if src else "unknown"
            ext_errs[ext] += 1
        print(f"\nErrors by codec:")
        for ext, n in ext_errs.most_common():
            print(f"  {ext:12} {n:>6,}")
        print(f"\nFull error log: {ERROR_LOG}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Helix Music Library Pipeline")
    parser.add_argument(
        "--stage", choices=["ingest", "index", "analyze", "all"], default="all",
        help="Pipeline stage to run (default: all)"
    )
    # Ingest flags
    parser.add_argument("--dry-run",    action="store_true")
    parser.add_argument("--limit",      type=int, default=None)
    parser.add_argument("--loved-only", action="store_true")
    parser.add_argument("--music-root", type=str, default=str(MUSIC_ROOT))
    parser.add_argument("--only-exts",  type=str, default=None,
                        help="Comma-separated extensions to ingest (e.g. .mini2sf,.miniusf,.wma)")
    # Analyze flags
    parser.add_argument("--fmt-cat",    nargs="+", default=None,
                        help="Format categories to include: hardware_log sequence audio")
    parser.add_argument("--album",      type=str, default=None)
    parser.add_argument("--artist",     type=str, default=None)
    parser.add_argument("--force",      action="store_true")
    parser.add_argument("--workers",    type=int,
                        default=_optimal_workers())
    args = parser.parse_args()

    stage = args.stage

    if stage in ("ingest", "all"):
        print("\n" + "=" * 70)
        print("STAGE 1: INGEST")
        print("=" * 70)
        run_ingest(
            music_root=Path(args.music_root),
            dry_run=args.dry_run,
            limit=args.limit,
            loved_only=args.loved_only,
            only_exts=args.only_exts,
        )

    if stage in ("index", "all"):
        print("\n" + "=" * 70)
        print("STAGE 2: INDEX")
        print("=" * 70)
        run_index()

    if stage in ("analyze", "all"):
        print("\n" + "=" * 70)
        print("STAGE 3: ANALYZE")
        print("=" * 70)
        fmt_cats = set(args.fmt_cat) if args.fmt_cat else None
        run_analyze(
            fmt_cats=fmt_cats,
            album_slug=args.album,
            artist_filter=args.artist,
            loved_only=args.loved_only,
            force=args.force,
            dry_run=args.dry_run,
            workers=args.workers,
            limit=args.limit,
        )


if __name__ == "__main__":
    main()

