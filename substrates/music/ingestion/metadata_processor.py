import os
import sys
from pathlib import Path

# Helix Root — Ensures substrates can be imported when run as a script
helix_root = Path(__file__).resolve().parent.parent.parent.parent
if str(helix_root) not in sys.path:
    sys.path.insert(0, str(helix_root))

import json
import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import mutagen
from mutagen import File as MutagenFile

from substrates.music.ingestion.config import (
    LIBRARY_ROOT as LIBRARY_PATH,
    ARTIFACTS as ARTIFACTS_DIR,
    REPORTS as REPORTS_DIR,
    DB_PATH,
    FOOBAR_APPDATA,
)
from substrates.music.ingestion.adapters.metadb_sqlite import MetadbSqliteReader
from substrates.music.atlas_integration.track_db import TrackDB

# Format Definitions
EMULATED_FORMATS = {
    'VGM', 'VGZ', 'SPC', '2SF', 'USF', 'NCSF', 'GSF', 'PSF', 'PSF2', 'S98', 'SSF', 'DSF', 'GBS', 'HES', 'KSS'
}
RENDERED_FORMATS = {
    'OPUS', 'MP3', 'AAC', 'VORBIS', 'WMA', 'MP2', 'WAV', 'FLAC', 'M4A'
}

METADATA_DIR = ARTIFACTS_DIR / "metadata"
ENTITIES_DIR = ARTIFACTS_DIR / "entities"

class MetadataProcessor:
    def __init__(self, library_path: Path):
        self.library_path = library_path
        self.results = []
        
    def run_pipeline(self):
        print(f"--- Music Lab: Comprehensive Metadata Pipeline ---")
        if not self.library_path.exists():
            print(f"Error: Library path {self.library_path} not found.")
            return

        # 0. metadb.sqlite Ingestion
        metadb_paths = [
            self.library_path / "metadb.sqlite",
            FOOBAR_APPDATA / "metadb.sqlite"
        ]
        for metadb_path in metadb_paths:
            if metadb_path.exists():
                print(f"Ingesting from metadb.sqlite at {metadb_path}...")
                reader = MetadbSqliteReader(str(metadb_path))
                sqlite_records = reader.read_all()
                if sqlite_records:
                    db = TrackDB(DB_PATH)
                    normalized = [reader.normalize(r) for r in sqlite_records]
                    db.populate_from_records(normalized)
                    print(f"Ingested {len(normalized)} tracks from {metadb_path.name}")
                # We only need to ingest from one if they are duplicates, 
                # but searching multiple locations is safer.
                break

        # 1. Scanning
        all_files = []
        print("Scanning library for audio files...")
        for root, dirs, files in os.walk(self.library_path):
            file_set = set(files)
            for file in files:
                fpath = Path(root) / file
                ext = fpath.suffix.lstrip('.').upper()
                if ext in EMULATED_FORMATS or ext in RENDERED_FORMATS:
                    all_files.append((fpath, file_set))
        
        print(f"Found {len(all_files)} target files. Starting extraction...")

        # 2. Parallel Extraction
        with ThreadPoolExecutor(max_workers=8) as executor:
            # We process in chunks to show progress
            chunk_size = 1000
            for i in range(0, len(all_files), chunk_size):
                chunk = all_files[i:i+chunk_size]
                futures = [executor.submit(self._process_file, f[0], f[1]) for f in chunk]
                for future in futures:
                    res = future.result()
                    if res:
                        self.results.append(res)
                print(f"Progress: {min(i + chunk_size, len(all_files))}/{len(all_files)} files processed.")

        # 3. Save Outputs
        df = pd.DataFrame(self.results)
        
        # Robustness: convert all metadata columns to string to avoid mixed-type Parquet errors
        string_cols = [
            'title', 'artist', 'album', 'date', 'genre', 'featuring', 'album_artist',
            'sound_team', 'franchise', 'platform', 'sound_chip', 'comment', 'codec',
            'track_number', 'total_tracks', 'disc_number', 'total_discs'
        ]
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('None', np.nan).replace('', np.nan)

        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)

        # Step 1: File Index
        file_index_cols = ['file_path', 'file_name', 'file_size', 'codec', 'duration', 'bitrate', 'sample_rate']
        valid_file_cols = [c for c in file_index_cols if c in df.columns]
        df[valid_file_cols].to_parquet(ARTIFACTS_DIR / "file_index.parquet", compression='snappy')

        # Step 2: Metadata Catalog
        metadata_cols = [
            'title', 'artist', 'album', 'date', 'genre', 'featuring', 'album_artist', 
            'sound_team', 'franchise', 'track_number', 'total_tracks', 'disc_number', 
            'total_discs', 'comment', 'platform', 'sound_chip', 'file_path', 'codec'
        ]
        valid_meta_cols = [c for c in metadata_cols if c in df.columns]
        df[valid_meta_cols].to_parquet(METADATA_DIR / "metadata_catalog.parquet", compression='snappy')

        # Step 3: Format Index
        format_df = df[['file_path', 'codec', 'format_category']]
        format_df.to_parquet(ARTIFACTS_DIR / "format_index.parquet", compression='snappy')

        # Step 4: Normalization
        self._normalize_entities(df)

        # Step 5: Comment Signals
        self._extract_comment_signals(df)

        # Step 6: Metadata Graph
        self._generate_graph(df)

        # Step 7: Statistics
        self._generate_stats_report(df)
        
        # Step 8: Priority Plan
        self._generate_priority_plan()

        print("Pipeline Complete.")

    def _process_file(self, file_path: Path, dir_files_set: set) -> Dict[str, Any]:
        try:
            stats = file_path.stat()
            meta = {}
            audio_info = None

            # 1. Check sidecar (.meta.json or .tag)
            meta_filename = file_path.name + ".meta.json"
            tag_filename  = file_path.name + ".tag"
            
            if meta_filename in dir_files_set:
                try:
                    with open(file_path.parent / meta_filename, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                except:
                    pass
            elif tag_filename in dir_files_set:
                try:
                    from mutagen.apev2 import APEv2
                    ape = APEv2(file_path.parent / tag_filename)
                    for key, val in ape.items():
                        # APE keys are often simple strings
                        norm_key = str(key).upper().replace(' ', '_')
                        if norm_key not in meta:
                            # Handle multi-value APE tags (Mutagen lists)
                            if isinstance(val.value, list):
                                meta[norm_key] = " / ".join(str(v) for v in val.value)
                            else:
                                meta[norm_key] = str(val.value)
                except Exception as e:
                    pass

            # 2. Mutagen (Internal Metadata)
            # For chip-based emulated formats (VGM/VGZ/SPC/etc.), the external .tag
            # sidecar is authoritative.  Only fall back to internal tags if no sidecar
            # was found, and even then only use it for audio_info (duration/sample_rate).
            codec_upper = file_path.suffix.lstrip('.').upper()
            is_chip_format = codec_upper in EMULATED_FORMATS
            sidecar_found = bool(meta)  # non-empty if .tag or .meta.json was loaded
            try:
                m = MutagenFile(file_path)
                if m:
                    audio_info = m.info
                    if not is_chip_format or not sidecar_found:
                        # Merge internal tags only when: not a chip format,
                        # OR chip format but no sidecar exists.
                        for key in m.keys():
                            norm_key = key.upper().replace(':', '_')
                            if norm_key not in meta:
                                val = m[key]
                                meta[norm_key] = val[0] if isinstance(val, list) else str(val)
            except:
                pass

            codec = file_path.suffix.lstrip('.').upper()
            is_emulated = codec in EMULATED_FORMATS
            
            # Map common internal tags to standard columns
            record = {
                # File Index
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": stats.st_size,
                "codec": codec,
                "duration": audio_info.length if audio_info else 0,
                "bitrate": audio_info.bitrate if audio_info and hasattr(audio_info, 'bitrate') else 0,
                "sample_rate": audio_info.sample_rate if audio_info and hasattr(audio_info, 'sample_rate') else 0,
                
                # Format Index
                "format_category": "emulated_audio" if is_emulated else "rendered_audio",

                # Metadata
                # Metadata Mapping with Canon Precedence
                # If sidecar (APE/JSON) has Title/Artist, it will be in meta['TITLE'] / meta['ARTIST']
                # We specifically look for these first.
                
                "title": (meta.get('TITLE') or 
                          meta.get('TIT2') or 
                          meta.get('title') or 
                          file_path.stem),
                          
                "artist": (meta.get('ARTIST') or 
                           meta.get('TPE1') or 
                           meta.get('COMPOSER') or 
                           meta.get('artist') or 
                           'Unknown'),
                           
                "album": meta.get('ALBUM', meta.get('TALB', meta.get('album', file_path.parent.name))),
                "date": meta.get('DATE', meta.get('TDRC', meta.get('YEAR', meta.get('TYER', meta.get('date'))))),
                "genre": meta.get('GENRE', meta.get('TCON', meta.get('genre'))),
                "featuring": meta.get('FEATURING', meta.get('featuring')),
                "album_artist": meta.get('ALBUM ARTIST', meta.get('ALBUMARTIST', meta.get('TPE2', meta.get('album_artist')))),
                "sound_team": meta.get('SOUND TEAM', meta.get('SOUND_TEAM', meta.get('sound_team'))),
                "franchise": meta.get('FRANCHISE', meta.get('franchise')),
                "track_number": meta.get('TRACKNUMBER', meta.get('TRCK', meta.get('TRACK', meta.get('track_number')))),
                "total_tracks": meta.get('TOTALTRACKS', meta.get('total_tracks')),
                "disc_number": meta.get('DISCNUMBER', meta.get('TPOS', meta.get('disc_number'))),
                "total_discs": meta.get('TOTALDISCS', meta.get('total_discs')),
                "comment": meta.get('COMMENT', meta.get('COMM', meta.get('comment'))),
                "platform": meta.get('PLATFORM', meta.get('platform')),
                "sound_chip": meta.get('SOUND_CHIP', meta.get('SOUND CHIP', meta.get('SOUNDCHIP', meta.get('sound_chip'))))
            }
            return record
        except Exception as e:
            # print(f"Error processing {file_path}: {e}")
            return None

    def _normalize_entities(self, df: pd.DataFrame):
        ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
        
        def clean(val):
            if pd.isna(val): return None
            v = str(val).strip()
            # Remove repeated punctuation like ??? or !!!
            v = re.sub(r'([?!.]{2,})', r'\1', v) # Keep at least one, simplified
            return v if v else None

        for col, filename in [
            ('artist', 'composers.parquet'),
            ('sound_team', 'sound_teams.parquet'),
            ('franchise', 'franchises.parquet'),
            ('platform', 'platforms.parquet'),
            ('sound_chip', 'sound_chips.parquet')
        ]:
            if col in df.columns:
                entities = df[col].dropna().apply(clean).unique()
                pd.DataFrame({"name": sorted([e for e in entities if e])}).to_parquet(ENTITIES_DIR / filename)

    def _extract_comment_signals(self, df: pd.DataFrame):
        if 'comment' not in df.columns: return
        
        comments = df[['file_path', 'comment']].dropna()
        signals = []
        
        # Patterns for extraction
        patterns = {
            "source_system": re.compile(r'(Genesis|Mega Drive|SNES|Super Famicom|NES|Famicom|PC-98|Arcade|Master System|Game Boy|Project2612)', re.I),
            "driver": re.compile(r'(SMPS|GEMS|Terpsichore|MML|PMD|FMP|Z80|68000|Sound Driver)', re.I),
            "port": re.compile(r'(Port of|from|ripped by)', re.I)
        }
        
        for idx, row in comments.iterrows():
            comm = str(row['comment'])
            sig = {"file_path": row['file_path'], "raw_comment": comm}
            for key, pattern in patterns.items():
                match = pattern.search(comm)
                if match:
                    sig[key] = match.group(0)
            if len(sig) > 2:
                signals.append(sig)
        
        pd.DataFrame(signals).to_parquet(ARTIFACTS_DIR / "comment_signals.parquet")

    def _generate_graph(self, df: pd.DataFrame):
        # Link tracks to entities
        graph_cols = ['file_path', 'artist', 'sound_team', 'platform', 'sound_chip', 'franchise']
        valid_cols = [c for c in graph_cols if c in df.columns]
        df[valid_cols].to_parquet(ARTIFACTS_DIR / "metadata_graph.parquet")

    def _generate_stats_report(self, df: pd.DataFrame):
        try:
            total = len(df)
            codec_counts = df['codec'].value_counts()
            format_counts = df['format_category'].value_counts()
            
            top_composers = df['artist'].value_counts().head(20)
            top_platforms = df['platform'].value_counts().head(10) if 'platform' in df.columns else pd.Series()
            top_chips = df['sound_chip'].value_counts().head(10) if 'sound_chip' in df.columns else pd.Series()
            top_franchises = df['franchise'].value_counts().head(10) if 'franchise' in df.columns else pd.Series()

            report = f"""# Helix Music Lab: Library Structure Report
Generated: {pd.Timestamp.now()}

## Dataset Overview
- **Total Tracks Identified**: {total}
- **Emulated Tracks**: {format_counts.get('emulated_audio', 0)}
- **Rendered Audio Tracks**: {format_counts.get('rendered_audio', 0)}

## Distribution by Codec
{codec_counts.to_markdown()}

## Top Composers (by Track Count)
{top_composers.to_markdown()}

## Top Platforms
{top_platforms.to_markdown()}

## Top Sound Chips
{top_chips.to_markdown()}

## Top Franchises
{top_franchises.to_markdown()}
"""
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            with open(REPORTS_DIR / "library_structure_report.md", 'w') as f:
                f.write(report)
        except Exception as e:
            print(f"Stats report error: {e}")

    def _generate_priority_plan(self):
        plan = """# deep Analysis Processing Priority Plan

To optimize the extraction of structural and synthesis data, deep analysis should proceed in the following order:

1. **VGM / VGZ**: Canonical chip instruction logs. Best for FM patch reconstruction and cycle-accurate behavior.
2. **SPC**: SNES memory/DSP dumps. High priority for sample library extraction and rhythm analysis.
3. **2SF / NCSF**: DS/3DS sequence formats. Rich in instrument and MIDI-like command data.
4. **USF / GSF**: N64/GBA memory traces.
5. **PSF / PSF2**: PlayStation sequence/driver bundles.
6. **S98**: PC-98 and other Japanese computer formats.
7. **Rendered Audio (Opus / MP3 / FLAC)**: Use for acoustic profiling, genre classification, and audio-based similarity when instructions are unavailable.

## Next Step
- Initialize Deep Extraction for VGM corpus (Sonic 3 & Knuckles focus).
"""
        with open(REPORTS_DIR / "analysis_plan.md", 'w') as f:
            f.write(plan)

if __name__ == "__main__":
    import time
    start = time.time()
    processor = MetadataProcessor(LIBRARY_PATH)
    processor.run_pipeline()
    print(f"Total time: {time.time() - start:.2f} seconds.")
