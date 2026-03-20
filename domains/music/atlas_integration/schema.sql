-- Helix Music Lab — SQLite Schema
-- All feature tables carry provenance_version, tier, extraction_ts, confidence.
-- Bump the schema version comment when tables change.
-- Schema version: 1

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Core entities
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tracks (
    id                TEXT PRIMARY KEY,   -- sha1(file_path) hex
    file_path         TEXT NOT NULL UNIQUE,
    file_name         TEXT,
    title             TEXT,
    artist            TEXT,
    album             TEXT,
    album_artist      TEXT,
    date              TEXT,
    genre             TEXT,
    featuring         TEXT,
    sound_team        TEXT,
    franchise         TEXT,
    track_number      TEXT,
    disc_number       TEXT,
    platform          TEXT,
    sound_chip        TEXT,
    comment           TEXT,
    format            TEXT,               -- VGM, SPC, OPUS, MP3, etc.
    duration_sec      REAL DEFAULT 0,
    file_size         INTEGER DEFAULT 0,
    max_tier          INTEGER DEFAULT 1,  -- highest tier completed
    play_count        INTEGER DEFAULT 0,
    rating            INTEGER DEFAULT 0,  -- 0–5
    loved             INTEGER DEFAULT 0,  -- 1 if 2003_loved tag set
    ingested_ts       TEXT                -- ISO8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_tracks_artist    ON tracks(artist);
CREATE INDEX IF NOT EXISTS idx_tracks_platform  ON tracks(platform);
CREATE INDEX IF NOT EXISTS idx_tracks_sound_chip ON tracks(sound_chip);
CREATE INDEX IF NOT EXISTS idx_tracks_format    ON tracks(format);
CREATE INDEX IF NOT EXISTS idx_tracks_loved     ON tracks(loved);

-- ---------------------------------------------------------------------------
-- Composers
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS composers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    aliases         TEXT,                 -- JSON array of alternate names
    known_platforms TEXT,                 -- JSON array
    games_count     INTEGER DEFAULT 0,
    notes           TEXT
);

-- ---------------------------------------------------------------------------
-- Chip features (Tier A+B)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS chip_features (
    track_id            TEXT PRIMARY KEY REFERENCES tracks(id),
    -- YM2612 / FM
    keyon_density       REAL,
    rhythmic_entropy    REAL,
    pitch_center        REAL,
    pitch_range         INTEGER,
    pitch_entropy       REAL,
    psg_to_fm_ratio     REAL,
    ams_fms_usage       REAL,
    silence_ratio       REAL,
    tl_mean_op1         REAL,
    tl_mean_op2         REAL,
    algorithm_dist      TEXT,             -- JSON {alg: count}
    channel_activity    TEXT,             -- JSON {ch: count}
    -- SPC700 (when available)
    spc_active_voices   INTEGER,
    spc_echo_enabled    INTEGER,
    spc_sample_count    INTEGER,
    -- NSF/NES
    nsf_expansion_chips TEXT,             -- JSON array
    -- SID
    sid_chip_model      TEXT,
    sid_waveform_dist   TEXT,             -- JSON {wave: count}
    -- Provenance
    provenance_version  TEXT NOT NULL DEFAULT 'chip_features:1.0',
    tier                INTEGER NOT NULL DEFAULT 1,
    confidence          REAL NOT NULL DEFAULT 0.6,
    extraction_ts       TEXT
);

-- ---------------------------------------------------------------------------
-- Symbolic features (Tier C)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS symbolic_features (
    track_id            TEXT PRIMARY KEY REFERENCES tracks(id),
    note_count          INTEGER,
    unique_pitches       INTEGER,
    pitch_range         INTEGER,
    avg_duration_sec    REAL,
    keyon_events        INTEGER,
    keyoff_events       INTEGER,
    orphan_keyons       INTEGER,
    -- Provenance
    provenance_version  TEXT NOT NULL DEFAULT 'symbolic_features:1.0',
    tier                INTEGER NOT NULL DEFAULT 3,
    confidence          REAL NOT NULL DEFAULT 1.0,
    extraction_ts       TEXT
);

-- ---------------------------------------------------------------------------
-- Theory features (Tier C/D)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS theory_features (
    track_id            TEXT PRIMARY KEY REFERENCES tracks(id),
    key_estimate        TEXT,             -- e.g. "D minor"
    key_confidence      REAL,
    mode                TEXT,             -- "major" | "minor"
    tempo_bpm           REAL,
    beat_regularity     REAL,
    syncopation_index   REAL,
    motif_count         INTEGER,
    top_motif_freq      INTEGER,
    harmonic_density    REAL,
    -- Provenance
    provenance_version  TEXT NOT NULL DEFAULT 'theory_features:1.0',
    tier                INTEGER NOT NULL DEFAULT 3,
    confidence          REAL NOT NULL DEFAULT 0.6,
    extraction_ts       TEXT
);

-- ---------------------------------------------------------------------------
-- Audio MIR features (Tier D, rendered audio only)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audio_features (
    track_id            TEXT PRIMARY KEY REFERENCES tracks(id),
    tempo_bpm           REAL,
    beat_strength       REAL,
    spectral_centroid   REAL,
    spectral_rolloff    REAL,
    zcr                 REAL,
    rms_mean            REAL,
    mfcc_json           TEXT,             -- JSON array of 13 floats
    chroma_json         TEXT,             -- JSON array of 12 floats
    -- Provenance
    provenance_version  TEXT NOT NULL DEFAULT 'audio_features:1.0',
    tier                INTEGER NOT NULL DEFAULT 4,
    confidence          REAL NOT NULL DEFAULT 1.0,
    extraction_ts       TEXT
);

-- ---------------------------------------------------------------------------
-- Feature vectors (Tier D)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS feature_vectors (
    track_id            TEXT PRIMARY KEY REFERENCES tracks(id),
    schema_version      TEXT NOT NULL,    -- e.g. "v0"
    vector_dim          INTEGER NOT NULL,
    vector_blob         BLOB NOT NULL,    -- numpy float32 array, raw bytes
    tier                INTEGER NOT NULL DEFAULT 4,
    confidence          REAL NOT NULL DEFAULT 1.0,
    provenance_version  TEXT NOT NULL DEFAULT 'feature_vector:1.0',
    extraction_ts       TEXT
);

-- ---------------------------------------------------------------------------
-- Composer attributions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS attributions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id        TEXT NOT NULL REFERENCES tracks(id),
    composer_id     INTEGER REFERENCES composers(id),
    composer_name   TEXT NOT NULL,
    probability     REAL NOT NULL,
    rank            INTEGER NOT NULL,     -- 1 = top candidate
    method          TEXT,                 -- "bayesian_gaussian" | "cosine_sim" | "manual"
    confidence      REAL NOT NULL DEFAULT 0.6,
    tier            INTEGER NOT NULL DEFAULT 1,
    provenance_version TEXT NOT NULL DEFAULT 'attribution:1.0',
    extraction_ts   TEXT
);

CREATE INDEX IF NOT EXISTS idx_attributions_track    ON attributions(track_id);
CREATE INDEX IF NOT EXISTS idx_attributions_composer ON attributions(composer_name);

-- ---------------------------------------------------------------------------
-- Recommendations cache
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id        TEXT NOT NULL REFERENCES tracks(id),
    mode            TEXT NOT NULL,        -- "near_core" | "frontier"
    rank            INTEGER NOT NULL,
    similarity      REAL NOT NULL,
    confidence      REAL NOT NULL,
    generated_ts    TEXT
);

CREATE INDEX IF NOT EXISTS idx_recs_mode ON recommendations(mode, rank);
