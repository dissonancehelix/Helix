"""
Helix Music Lab — Central Configuration
========================================
All paths, constants, and capability flags for the Music Lab.
No other module should hardcode paths or schema versions.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Root paths
# ---------------------------------------------------------------------------

ROOT       = Path(__file__).resolve().parents[3]       # Helix repo root
LAB        = Path(__file__).parent                     # domains/music/model/ingestion/
DATA       = LAB / "data"
TOOLS      = LAB / "tools"
TOOLS_RT   = TOOLS / "runtime"                        # runtime algorithmic tools
TOOLS_EMU  = TOOLS / "emulation"                      # compiled C libs (Tier B)
TOOLS_REF  = TOOLS / "reference"                      # source study only
ARTIFACTS  = LAB / "artifacts"
REPORTS    = LAB / "reports"
PARSERS    = LAB / "parsers"
EMULATION  = LAB / "emulation"
ANALYSIS   = LAB / "analysis"
SIMILARITY = LAB / "similarity"
TASTE      = LAB / "taste_model"

# ---------------------------------------------------------------------------
# Library paths
# ---------------------------------------------------------------------------

LIBRARY_ROOT   = Path("C:/Users/dissonance/Music")
VGM_ROOT       = LIBRARY_ROOT / "VGM"
TEMP_DIR       = Path("C:/Users/dissonance/Desktop/temp")
S3K_PATH       = VGM_ROOT / "S" / "Sonic 3 & Knuckles"
FOOBAR_APPDATA = Path("C:/Users/dissonance/AppData/Roaming/foobar2000-v2")
CODEX_LIBRARY_ROOT = ROOT / "codex" / "library"
TECH_LIBRARY_ROOT = CODEX_LIBRARY_ROOT / "tech"

# ---------------------------------------------------------------------------
# Database / artifact paths
# ---------------------------------------------------------------------------

DB_PATH                = DATA / "helix_music.db"
SMPS_VOICE_LIBRARY_PATH = TECH_LIBRARY_ROOT / "smps_voice_library.json"
TASTE_PATH             = DATA / "taste_vector.json"
COMPOSER_PROFILES_PATH = DATA / "composer_profiles.json"
CHIP_STATS_PATH        = DATA / "chip_usage_stats.json"
TRACK_VECTORS_PATH     = DATA / "track_feature_vectors.json"
FAISS_INDEX_PATH       = DATA / "track_index.faiss"
FAISS_IDS_PATH         = DATA / "track_index_ids.npy"

# Parquet outputs from metadata_processor
METADATA_DIR      = DATA / "metadata"
FILE_INDEX_PATH   = DATA / "file_index.parquet"
FORMAT_INDEX_PATH = DATA / "format_index.parquet"

# ---------------------------------------------------------------------------
# Recommendation output paths
# ---------------------------------------------------------------------------

RECS_DIR        = REPORTS / "recommendations"
NEAR_CORE_PATH  = RECS_DIR / "near_core_500.json"
FRONTIER_PATH   = RECS_DIR / "frontier_500.json"
TOP_COMPOSERS_PATH = RECS_DIR / "top_50_composers.json"
HIDDEN_GEMS_PATH   = RECS_DIR / "hidden_gems.json"

# ---------------------------------------------------------------------------
# Feature vector schema version
# ---------------------------------------------------------------------------

FEATURE_VECTOR_VERSION = "v0"
FEATURE_VECTOR_DIM     = 64

# Bump FEATURE_VECTOR_VERSION when dims or normalization changes.
# Old vectors in DB with a different version are invalid and must be recomputed.

# ---------------------------------------------------------------------------
# Capability tiers
# ---------------------------------------------------------------------------

TIER_A_STATIC    = 1   # static parse only
TIER_B_EMULATED  = 2   # full emulated playback
TIER_C_SYMBOLIC  = 3   # symbolic reconstruction (note events / MIDI)
TIER_D_MIR       = 4   # MIR + fingerprinting + recommendation

# Default confidence scores by tier source
CONFIDENCE_BY_TIER = {
    TIER_B_EMULATED: 1.0,
    TIER_A_STATIC:   0.6,
    "proxy_only":    0.3,
}

# ---------------------------------------------------------------------------
# Taste weights (separate from confidence weights)
# ---------------------------------------------------------------------------

TASTE_WEIGHT = {
    "loved_foobar": 2.0,    # 03_loved tag in Foobar
    "desktop_temp": 1.5,    # C:/Users/dissonance/Desktop/temp
    "rated_high":   1.2,    # RATING >= 4
    "general":      1.0,
}

# Foobar custom field name for favorites (without % signs)
FOOBAR_LOVED_FIELD = "2003_loved"

# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

PARALLEL_WORKERS = 8
VGM_BATCH_SIZE   = 500    # tracks per parallel batch
SPC_BATCH_SIZE   = 500

# Emulated formats — need parsers/emulation
EMULATED_FORMATS = {
    "VGM", "VGZ", "SPC", "NSF", "NSFE", "GBS", "HES", "KSS",
    "2SF", "USF", "NCSF", "GSF", "PSF", "PSF2", "S98", "SSF",
    "DSF", "QSF", "SID", "AY", "SAP",
}

# Rendered formats — use audio MIR
RENDERED_FORMATS = {
    "OPUS", "MP3", "AAC", "OGG", "VORBIS", "FLAC", "WAV",
    "M4A", "WMA", "MP2",
}


def ensure_dirs() -> None:
    """Create all required data/artifact/report directories."""
    for d in [DATA, ARTIFACTS, REPORTS, METADATA_DIR, RECS_DIR,
              LAB / "analysis" / "theory_features",
              LAB / "analysis" / "audio_features",
              LAB / "similarity",
              LAB / "taste_model",
              LAB / "parsers",
              LAB / "emulation",
              TOOLS_RT, TOOLS_EMU, TOOLS_REF]:
        d.mkdir(parents=True, exist_ok=True)

