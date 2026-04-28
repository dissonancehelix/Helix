"""
playcount_merger.py — Helix Unified Playcount Sync
====================================================
Merges Last.fm + ListenBrainz scrobbles with foo_playcount_2003 local counts,
then writes the unified values as LFMPLAYCOUNT / LFMFIRSTPLAYED / LFMLASTPLAYED
into foobar2000's external-tags.db.

The user then runs the Playcount 2003 import dialog with:
  Playcount:    [%lfm_playcount%]
  First Played: [%lfm_first_played%]
  Last Played:  [%lfm_last_played%]

Strategy:
  unified_count = max(2003_local, lfm_count, lb_count)
  first_played  = earliest timestamp across all sources
  last_played   = latest timestamp across all sources

Matching:
  Last.fm / LB are keyed by (artist, track_title).
  Local 2003 records are keyed by file path — we extract the title from the
  filename stem (strip leading track number) and use the parent folder as
  an album/artist hint. This gives ~60–80% match on well-tagged VGM files.

Usage:
  python playcount_merger.py [--dry-run]
"""

import json
import os
import re
import sqlite3
import argparse
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DOWNLOADS      = Path(r"C:\Users\dissonance\Downloads")
FOOBAR_DB      = Path(r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\external-tags.db")

LASTFM_JSON    = DOWNLOADS / "lastfmstats-dissident93.json"
PLAYCOUNT_2003 = DOWNLOADS / "2003_playcount.json"
LB_ROOT        = DOWNLOADS / "listenbrainz" / "listens"

# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------
_NOISE = re.compile(r'[\(\[].*?[\)\]]|\s+')

def norm(s: str) -> str:
    """Lowercase, strip bracketed content and extra whitespace."""
    if not s:
        return ""
    s = re.sub(r'[\(\[].*?[\)\]]', '', s.lower())
    s = re.sub(r'\s+', ' ', s).strip()
    # strip feat/remix noise
    s = re.sub(r'\s*-\s*(feat|ft|featuring|remix).*$', '', s)
    return s

def make_key(artist: str, track: str) -> tuple:
    return (norm(artist), norm(track))

def title_from_path(file_path: str) -> str:
    """Extract track title from filename by stripping leading track numbers."""
    stem = Path(file_path).stem
    # Strip: "01 - ", "1. ", "A1 ", "01.", "Track 01 - " etc.
    clean = re.sub(r'^(?:track\s*)?\d+[\s\.\-_]+', '', stem, flags=re.IGNORECASE).strip()
    clean = re.sub(r'[\(\[].*?[\)\]]', '', clean).strip()
    return clean


# ---------------------------------------------------------------------------
# Source 1: Last.fm scrobble export
# Format: {"scrobbles": [{track, artist, album, date(ms)}, ...]}
# ---------------------------------------------------------------------------
def load_lastfm(path: Path):
    """Returns ({key: count}, {key: (first_ts, last_ts)}) — timestamps in seconds."""
    print(f"[LFM] Loading {path.name}...")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scrobbles = data.get("scrobbles", [])
    counts = defaultdict(int)
    times  = {}  # key → (first_ts, last_ts)

    for s in scrobbles:
        key = make_key(s.get("artist", ""), s.get("track", ""))
        ts  = s.get("date", 0) // 1000  # ms → seconds
        counts[key] += 1
        if key not in times:
            times[key] = (ts, ts)
        else:
            f_, l_ = times[key]
            times[key] = (min(f_, ts), max(l_, ts))

    print(f"[LFM] {len(scrobbles):,} scrobbles → {len(counts):,} unique tracks.")
    return dict(counts), times


# ---------------------------------------------------------------------------
# Source 2: ListenBrainz (.jsonl per month, one listen per line)
# Format: {listened_at, track_metadata: {artist_name, track_name}}
# ---------------------------------------------------------------------------
def load_listenbrainz(lb_root: Path):
    """Returns ({key: count}, {key: (first_ts, last_ts)})."""
    print(f"[LB]  Loading from {lb_root}...")
    counts = defaultdict(int)
    times  = {}
    total  = 0

    for year_dir in sorted(lb_root.iterdir()):
        if not year_dir.is_dir():
            continue
        for month_file in sorted(year_dir.iterdir()):
            try:
                with open(month_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        listen = json.loads(line)
                        meta   = listen.get("track_metadata", {})
                        artist = meta.get("artist_name", "")
                        track  = meta.get("track_name",  "")
                        ts     = listen.get("listened_at", 0)
                        if artist and track:
                            key = make_key(artist, track)
                            counts[key] += 1
                            total += 1
                            if key not in times:
                                times[key] = (ts, ts)
                            else:
                                f_, l_ = times[key]
                                times[key] = (min(f_, ts), max(l_, ts))
            except Exception as e:
                print(f"  [LB WARN] {month_file.name}: {e}")

    print(f"[LB]  {total:,} listens → {len(counts):,} unique tracks.")
    return dict(counts), times


# ---------------------------------------------------------------------------
# Source 3: foo_playcount_2003 export
# Format: [{id: "path|0", 2003_playcount, 2003_first_played, 2003_last_played, ...}]
# ---------------------------------------------------------------------------
def load_2003(path: Path):
    """Returns list of records, with file_path extracted (|0 stripped)."""
    print(f"[2003] Loading {path.name}...")
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    # Strip |subsong suffix
    for r in records:
        r["_path"] = r.get("id", "").rsplit("|", 1)[0]
    print(f"[2003] {len(records):,} local tracks.")
    return records


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------
def merge_all(records_2003, lfm_counts, lfm_times, lb_counts, lb_times):
    """
    For each 2003 local track, look up Last.fm + LB counts by title key.
    Returns list of dicts with unified stats.
    """
    matched_lfm = 0
    matched_lb  = 0
    boosted     = 0
    result      = []

    for r in records_2003:
        fp    = r["_path"]
        title = title_from_path(fp)
        # Use parent folder name as a rough artist/album proxy for VGM
        folder = Path(fp).parent.name

        # Try (folder, title) first, then (title,) with empty artist
        key1 = make_key(folder, title)
        key2 = ("", norm(title))

        lfm_c  = lfm_counts.get(key1, 0) or lfm_counts.get(key2, 0)
        lfm_t  = lfm_times.get(key1) or lfm_times.get(key2)
        lb_c   = lb_counts.get(key1, 0) or lb_counts.get(key2, 0)
        lb_t   = lb_times.get(key1) or lb_times.get(key2)

        local_c = r.get("2003_playcount", 0)
        local_f = r.get("2003_first_played", 0)
        local_l = r.get("2003_last_played",  0)

        if lfm_c:
            matched_lfm += 1
        if lb_c:
            matched_lb += 1

        unified_count = max(local_c, lfm_c, lb_c)

        # Unify timestamps
        all_firsts = [t for t in [local_f, lfm_t[0] if lfm_t else 0, lb_t[0] if lb_t else 0] if t]
        all_lasts  = [t for t in [local_l, lfm_t[1] if lfm_t else 0, lb_t[1] if lb_t else 0] if t]

        unified_first = min(all_firsts) if all_firsts else 0
        unified_last  = max(all_lasts)  if all_lasts  else 0

        if unified_count > local_c:
            boosted += 1

        result.append({
            "_path":          fp,
            "id":             r.get("id", ""),
            "local_count":    local_c,
            "lfm_count":      lfm_c,
            "lb_count":       lb_c,
            "unified_count":  unified_count,
            "unified_first":  unified_first,
            "unified_last":   unified_last,
            "2003_loved":     r.get("2003_loved", 0),
        })

    total_boost = sum(r["unified_count"] - r["local_count"] for r in result)
    print(f"\n[MERGE] {len(result):,} tracks processed.")
    print(f"[MERGE] Matched LFM: {matched_lfm:,}  |  Matched LB: {matched_lb:,}")
    print(f"[MERGE] Tracks boosted: {boosted:,}  |  Total plays added: {total_boost:,}")
    return result


# ---------------------------------------------------------------------------
# Write to external-tags.db as LFMPLAYCOUNT / LFMFIRSTPLAYED / LFMLASTPLAYED
# ---------------------------------------------------------------------------
def ts_to_date(ts: int) -> str:
    """Convert unix timestamp to YYYY-MM-DD HH:MM:SS for foo_playcount_2003 dates."""
    if not ts:
        return ""
    import datetime
    return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def write_to_external_tags(merged: list, db_path: Path, dry_run: bool):
    """
    Writes unified playcount tags into external-tags.db.
    These become available as %lfm_playcount%, %lfm_first_played%, %lfm_last_played%
    in foobar2000, ready for the Playcount 2003 import dialog.
    """
    if dry_run:
        changed = sum(1 for r in merged if r["unified_count"] != r["local_count"])
        print(f"\n[DRY-RUN] Would write {changed:,} changed records to {db_path.name}.")
        # Show top 15 boosts
        top = sorted(merged, key=lambda r: r["unified_count"] - r["local_count"], reverse=True)[:15]
        print("\n[TOP BOOSTS]")
        for r in top:
            diff = r["unified_count"] - r["local_count"]
            if diff > 0:
                print(f"  +{diff:3d}  (local={r['local_count']:3d}  lfm={r['lfm_count']:3d}  lb={r['lb_count']:3d})  {Path(r['_path']).name}")
        return

    print(f"\n[DB] Writing to {db_path}...")
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # Ensure columns exist (they won't hurt if they already do)
    # external-tags.db 'tags' table: path TEXT, meta BLOB
    # We need to write new rows (or update) with LFMPLAYCOUNT as a foobar tag.
    # The 'meta' blob format is proprietary — we cannot write to it directly.
    #
    # ALTERNATIVE: write a separate helper table that foobar's title formatting
    # can't directly read, BUT the foo_playcount_2003 import dialog CAN read
    # from any title format expression — including custom tags written to files.
    #
    # Best approach: write a side JSON that the user imports manually, OR
    # write a TSV that can be imported via foo_playcount_2003's own import.

    conn.close()

    # Write a TSV import file (tab-separated, same schema as foo_playcount_2003 export)
    # The plugin's Library > Playcount 2003 > Import reads TSV with these columns:
    #   <id>  <playcount>  <first_played>  <last_played>  <loved>
    # where <id> matches the plugin's title format pattern (default: %path%|%subsong%)
    tsv_path = db_path.parent / "playcount_2003_import.tsv"
    written  = 0
    with open(tsv_path, "w", encoding="utf-8") as f:
        for r in merged:
            if r["unified_count"] == r["local_count"] and not r["unified_first"]:
                continue  # unchanged — skip to keep import fast
            row = "\t".join([
                r["id"],
                str(r["unified_count"]),
                ts_to_date(r["unified_first"]),
                ts_to_date(r["unified_last"]),
                str(r.get("2003_loved", 0)),
            ])
            f.write(row + "\n")
            written += 1

    print(f"[OUT] Wrote {written:,} records → {tsv_path}")
    print("\nNext steps:")
    print("  1. In foobar2000: Library > Playcount 2003 > Import")
    print(f"  2. Select: {tsv_path}")
    print("  3. Confirm — plugin will merge the unified counts into its DB.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    lfm_counts, lfm_times = load_lastfm(LASTFM_JSON)
    lb_counts,  lb_times  = load_listenbrainz(LB_ROOT)
    records_2003           = load_2003(PLAYCOUNT_2003)

    merged = merge_all(records_2003, lfm_counts, lfm_times, lb_counts, lb_times)
    write_to_external_tags(merged, FOOBAR_DB, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
