"""
make_snapshot.py — Helix Snapshot Export
=========================================
Canonical snapshot command for the Helix repository.

Produces a compact, LLM-ingestible zip of the repo structure:
  helix_snapshot.zip   (single stable output — overwrites on each run)

What is included:
  - All human-readable source code and docs under the file-size limit:
    .py  .md  .yaml  .yml  .json  .toml  .txt  .ps1  .bat  .sh  .cfg  .ini
  - All docs/, domain manifests, app manifests, core/governance
  - codex/atlas: small schema/manifest files only (< ATLAS_SMALL_FILE_MB)
  - Snapshot metadata (README, MANIFEST, TREE.txt, TREE.json, OMISSIONS)

What is excluded:
  - .git/, __pycache__/, venv / virtualenvs
  - Secrets: .env, .env.*, private keys, token/credential files
  - codex/library/ bulk data (structural skeleton provided instead)
  - codex/atlas/ heavy payloads above ATLAS_SMALL_FILE_MB
  - domains/music/model/outputs/ generated artifacts
  - Binary media (.png, .mp3, .pyc, etc.)
  - Any single text file exceeding MAX_FILE_MB

Excluded paths appear in SNAPSHOT_OMISSIONS.json and SNAPSHOT_TREE.txt
with full path, reason, size, extension, and mtime.

Usage:
    python scripts/make_snapshot.py
    python scripts/make_snapshot.py --include-library
    python scripts/make_snapshot.py --include-atlas-heavy
    python scripts/make_snapshot.py --max-file-mb 1.0
    python scripts/make_snapshot.py --output /path/to/out.zip

Schema version: snapshot_schema_v2
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SNAPSHOT_SCHEMA = "snapshot_schema_v2"

# ── Resolve repo root ─────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = next(
    p for p in [SCRIPT_DIR, *SCRIPT_DIR.parents]
    if (p / "MANIFEST.yaml").exists()
)

# ── Inclusion / exclusion policy constants ────────────────────────────────────
DEFAULT_MAX_FILE_MB   = 0.5   # text files above this are indexed, not included
ATLAS_SMALL_FILE_MB   = 0.05  # atlas files below this are always included

# Human-readable extensions to include (within size limit)
INCLUDED_EXTENSIONS = frozenset({
    ".py", ".md", ".yaml", ".yml", ".json", ".toml",
    ".txt", ".ps1", ".bat", ".sh", ".cfg", ".ini",
})

# Binary / compiled extensions to always skip
SKIP_EXTENSIONS = frozenset({
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".pdb",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
    ".mp4", ".avi", ".mov", ".webm", ".mkv",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pkl", ".h5", ".hdf5", ".npz", ".npy", ".pt", ".onnx",
    ".db", ".sqlite", ".sqlite3", ".dat", ".bin",
    ".lock",
})

# Secrets filename patterns — exclude content, still index as OMITTED_SECRET
SECRETS_PATTERNS = frozenset({
    ".env", ".env.local", ".env.production", ".env.development",
    ".env.test", ".env.staging",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "private_key", "secret_key", "credentials.json",
    "token.json", "auth.json", "session.json",
    ".netrc", ".npmrc", ".pypirc",
})

# Directory names to skip entirely (no content, no index entry)
ALWAYS_SKIP_DIRS = frozenset({
    ".git", "__pycache__", ".claude", ".gemini",
    ".agents", ".agent", "_agents", "_agent",
    "artifacts",
    "venv", ".venv", "env", ".env",
    "node_modules", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".hypothesis",
})

# Directories whose entire content is excluded — structural skeleton provided
BULK_INDEX_DIRS = frozenset({
    "codex/library",
    "domains/music/model/outputs",
})

# Atlas: exclude heavy payloads, include small files
ATLAS_PREFIX = "codex/atlas"


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()

def _mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""

def _size_mb(size_bytes: int) -> float:
    return size_bytes / (1024 * 1024)

def _is_secret(fname: str) -> bool:
    return fname.lower() in SECRETS_PATTERNS or fname.startswith(".env")

def _should_skip_dir(name: str) -> bool:
    return name in ALWAYS_SKIP_DIRS or (name.startswith(".") and name not in (".",))

def _in_bulk_zone(rel: str) -> Optional[str]:
    for prefix in BULK_INDEX_DIRS:
        if rel == prefix or rel.startswith(prefix + "/"):
            return prefix
    return None

def _in_atlas(rel: str) -> bool:
    return rel == ATLAS_PREFIX or rel.startswith(ATLAS_PREFIX + "/")


# ═══════════════════════════════════════════════════════════════════════════════
# Codex/library structural skeleton
# ═══════════════════════════════════════════════════════════════════════════════

def build_library_skeleton() -> dict:
    """
    Walk codex/library and produce a structural skeleton:
    directory counts, file counts, sizes — without content.
    """
    lib_root = ROOT / "codex" / "library"
    if not lib_root.exists():
        return {"exists": False}

    subdirs: dict[str, dict] = {}
    total_files = 0
    total_bytes = 0

    for dirpath, dirnames, filenames in os.walk(lib_root, topdown=True):
        dirnames[:] = [d for d in sorted(dirnames) if not _should_skip_dir(d)]
        dir_p = Path(dirpath)
        rel = _rel(dir_p)

        ext_counts: dict[str, int] = {}
        dir_bytes = 0
        for fname in filenames:
            fp = dir_p / fname
            try:
                sz = fp.stat().st_size
            except OSError:
                sz = 0
            ext = fp.suffix.lower() or "(none)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            dir_bytes += sz
            total_files += 1
            total_bytes += sz

        if rel != "codex/library":
            subdirs[rel] = {
                "file_count": len(filenames),
                "size_bytes": dir_bytes,
                "extensions": ext_counts,
            }

    return {
        "exists": True,
        "path": "codex/library",
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_mb": round(_size_mb(total_bytes), 2),
        "subdirectories": subdirs,
        "note": "Full content excluded from snapshot by default. Use --include-library to include.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Repo walk
# ═══════════════════════════════════════════════════════════════════════════════

def walk_repo(
    max_file_mb: float,
    include_library: bool,
    include_atlas_heavy: bool,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Returns:
      included — list of {rel, abs, size_bytes, ext, mtime}
      indexed  — list of {rel, size_bytes, ext, mtime, category, reason}
      omitted  — list of {rel, size_bytes, ext, mtime, reason}
    """
    included: list[dict] = []
    indexed:  list[dict] = []
    omitted:  list[dict] = []

    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True):
        dir_p = Path(dirpath)

        # Prune directories in-place (stable sort for determinism)
        dirnames[:] = sorted(d for d in dirnames if not _should_skip_dir(d))

        for fname in sorted(filenames):
            file_p = dir_p / fname
            try:
                stat = file_p.stat()
            except OSError:
                continue

            rel        = _rel(file_p)
            ext        = file_p.suffix.lower()
            size_bytes = stat.st_size
            mtime      = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

            base_entry = {
                "rel": rel,
                "size_bytes": size_bytes,
                "ext": ext or "(none)",
                "mtime": mtime,
            }

            # ── Secrets ──────────────────────────────────────────────────
            if _is_secret(fname):
                omitted.append({**base_entry, "reason": "OMITTED_SECRET"})
                continue

            # ── Always-skip extensions ────────────────────────────────────
            if ext in SKIP_EXTENSIONS:
                omitted.append({**base_entry, "reason": "SKIP_EXTENSION"})
                continue

            # ── Bulk index zones (library, outputs) ───────────────────────
            bulk_zone = _in_bulk_zone(rel)
            if bulk_zone:
                if include_library and bulk_zone == "codex/library":
                    pass  # fall through to normal inclusion
                else:
                    indexed.append({**base_entry, "category": bulk_zone, "reason": "BULK_EXCLUDED"})
                    continue

            # ── Atlas: smart handling ─────────────────────────────────────
            if _in_atlas(rel):
                if include_atlas_heavy:
                    pass  # include everything
                elif ext in INCLUDED_EXTENSIONS and _size_mb(size_bytes) <= ATLAS_SMALL_FILE_MB:
                    pass  # include small schema/manifest files
                else:
                    indexed.append({**base_entry, "category": "codex/atlas", "reason": "ATLAS_HEAVY_EXCLUDED"})
                    continue

            # ── Unknown extensions ────────────────────────────────────────
            if ext not in INCLUDED_EXTENSIONS:
                omitted.append({**base_entry, "reason": "UNKNOWN_EXTENSION"})
                continue

            # ── Oversized ────────────────────────────────────────────────
            if _size_mb(size_bytes) > max_file_mb:
                omitted.append({**base_entry, "reason": f"OVERSIZED_{_size_mb(size_bytes):.2f}MB"})
                continue

            included.append({**base_entry, "abs": str(file_p)})

    return included, indexed, omitted


# ═══════════════════════════════════════════════════════════════════════════════
# Metadata generators
# ═══════════════════════════════════════════════════════════════════════════════

def make_tree_txt(included: list[dict], indexed: list[dict], omitted: list[dict]) -> str:
    lines = [
        "HELIX SNAPSHOT — COMPLETE REPOSITORY TREE",
        "=" * 64,
        "LEGEND: (space)=included  ~=indexed/skeleton  x=omitted",
        "",
    ]
    all_paths = (
        [(e["rel"], "  ", e.get("reason", "")) for e in included] +
        [(e["rel"], "~ ", e.get("reason", "BULK_INDEXED")) for e in indexed] +
        [(e["rel"], "x ", e.get("reason", "OMITTED")) for e in omitted]
    )
    for rel, prefix, reason in sorted(all_paths, key=lambda x: x[0]):
        suffix = f"  [{reason}]" if reason and prefix != "  " else ""
        lines.append(f"{prefix}{rel}{suffix}")
    return "\n".join(lines)


def make_tree_json(included: list[dict], indexed: list[dict], omitted: list[dict]) -> str:
    return json.dumps({
        "schema": SNAPSHOT_SCHEMA,
        "included":  sorted([{"rel": e["rel"], "size_bytes": e["size_bytes"], "ext": e["ext"]} for e in included], key=lambda x: x["rel"]),
        "indexed":   sorted([{"rel": e["rel"], "size_bytes": e["size_bytes"], "ext": e["ext"], "category": e.get("category",""), "reason": e.get("reason","")} for e in indexed], key=lambda x: x["rel"]),
        "omitted":   sorted([{"rel": e["rel"], "size_bytes": e["size_bytes"], "ext": e["ext"], "reason": e.get("reason","")} for e in omitted], key=lambda x: x["rel"]),
    }, indent=2)


def make_omissions_json(indexed: list[dict], omitted: list[dict]) -> str:
    return json.dumps({
        "schema": SNAPSHOT_SCHEMA,
        "omission_policy": {
            "ALWAYS_SKIP_DIRS": sorted(ALWAYS_SKIP_DIRS),
            "BULK_INDEX_DIRS": sorted(BULK_INDEX_DIRS),
            "ATLAS_PREFIX": ATLAS_PREFIX,
            "ATLAS_SMALL_FILE_MB": ATLAS_SMALL_FILE_MB,
            "SKIP_EXTENSIONS": sorted(SKIP_EXTENSIONS),
            "SECRETS_PATTERNS": sorted(SECRETS_PATTERNS),
            "MAX_FILE_MB": "configurable (default 0.5)",
            "note": (
                "Indexed paths are excluded from content but appear here with full metadata. "
                "Omitted paths include binary, oversized, secrets, and unknown-extension files. "
                "Secret contents are never included; their existence is recorded only."
            ),
        },
        "indexed_count": len(indexed),
        "omitted_count": len(omitted),
        "indexed_paths": sorted(indexed, key=lambda x: x["rel"]),
        "omitted_paths": sorted(omitted, key=lambda x: x["rel"]),
    }, indent=2)


def make_snapshot_manifest(
    included: list[dict],
    indexed: list[dict],
    omitted: list[dict],
    lib_skeleton: dict,
    opts: argparse.Namespace,
    ts: str,
) -> str:
    total_bytes = sum(e["size_bytes"] for e in included)

    # Count by reason category
    indexed_by_reason: dict[str, int] = {}
    for e in indexed:
        r = e.get("reason", "UNKNOWN")
        indexed_by_reason[r] = indexed_by_reason.get(r, 0) + 1
    omitted_by_reason: dict[str, int] = {}
    for e in omitted:
        r = e.get("reason", "UNKNOWN")
        omitted_by_reason[r] = omitted_by_reason.get(r, 0) + 1

    return json.dumps({
        "schema": SNAPSHOT_SCHEMA,
        "generated_at": ts,
        "canonical_command": "python scripts/make_snapshot.py",
        "output": "helix_snapshot.zip",
        "options_used": {
            "max_file_mb": opts.max_file_mb,
            "include_library": opts.include_library,
            "include_atlas_heavy": opts.include_atlas_heavy,
        },
        "inclusion_policy": {
            "included_extensions": sorted(INCLUDED_EXTENSIONS),
            "max_file_mb": opts.max_file_mb,
            "atlas_small_file_mb": ATLAS_SMALL_FILE_MB,
            "note": "All human-readable text/code files under size limit are included, unless in an excluded zone.",
        },
        "exclusion_policy": {
            "always_skip_dirs": sorted(ALWAYS_SKIP_DIRS),
            "bulk_index_dirs": sorted(BULK_INDEX_DIRS),
            "atlas_heavy_excluded": not opts.include_atlas_heavy,
            "skip_extensions": sorted(SKIP_EXTENSIONS),
            "secrets_excluded": True,
            "secrets_patterns": sorted(SECRETS_PATTERNS),
            "note": "Excluded files appear in SNAPSHOT_OMISSIONS.json with full metadata but no content.",
        },
        "stats": {
            "files_included": len(included),
            "files_indexed": len(indexed),
            "files_omitted": len(omitted),
            "total_included_bytes": total_bytes,
            "total_included_mb": round(_size_mb(total_bytes), 2),
            "indexed_by_reason": indexed_by_reason,
            "omitted_by_reason": omitted_by_reason,
        },
        "library_skeleton": lib_skeleton,
        "metadata_files_in_zip": [
            "SNAPSHOT_README.md",
            "SNAPSHOT_MANIFEST.json",
            "SNAPSHOT_TREE.txt",
            "SNAPSHOT_TREE.json",
            "SNAPSHOT_OMISSIONS.json",
        ],
    }, indent=2)


SNAPSHOT_README = """\
# HELIX SNAPSHOT

**Schema:** snapshot_schema_v2
**Purpose:** LLM-ingestible structural export of the Helix repository.

This snapshot is optimised for model inspection, not backup or deployment.
It is NOT the full repository. Heavy data and binary files are excluded.

---

## How to read this snapshot

### Full content files (read normally)
All `.py`, `.md`, `.yaml`, `.yml`, `.json`, `.toml`, `.txt` files under the
size limit are included at their real repo-relative paths.
Read them exactly as you would the actual repository files.

### Indexed-only paths (structural visibility, no content)
Heavy zones are excluded from content but fully represented in:
  - `SNAPSHOT_TREE.txt`      — complete repo tree with FULL/INDEXED/OMITTED markers
  - `SNAPSHOT_TREE.json`     — machine-readable version of the same
  - `SNAPSHOT_OMISSIONS.json` — every excluded file with path, reason, size, mtime

The `codex/library/` skeleton summary is embedded in `SNAPSHOT_MANIFEST.json`
under `library_skeleton` — directory counts, file counts, sizes.

### Intentionally excluded
  - `.git/`, `__pycache__/`, virtual environments (silently dropped)
  - Secrets and credential files (indexed as OMITTED_SECRET, no content)
  - Binary files (.pyc, .png, .mp3, etc.) — indexed as SKIP_EXTENSION
  - `codex/library/` bulk data — skeleton in manifest, paths in OMISSIONS
  - `codex/atlas/` heavy payloads — small schemas included; blobs indexed
  - `domains/music/model/outputs/` generated artifacts — indexed BULK_EXCLUDED

---

## Read in this order

| File | Why |
|------|-----|
| `MANIFEST.yaml` | System-wide operational index — start here |
| `README.md` | System overview |
| `docs/README.md` | Documentation tree map |
| `docs/architecture/ARCHITECTURE.md` | Layer model |
| `docs/governance/GOVERNANCE.md` | Promotion gates, enforcement |
| `docs/invariants/INVARIANTS.md` | Named invariants registry |
| `docs/governance/AUTHORITY.md` | What each doc type is authoritative for |
| `domains/*/<DOMAIN>.md` | Domain status |
| `domains/*/manifest.yaml` | Machine-readable domain facts |
| `core/engine/store/compiler/atlas_compiler.py` | The sole Atlas write authority |
| `core/engine/contract/validation/` | Manifest + structure enforcement |
| `SNAPSHOT_MANIFEST.json` | Snapshot stats, policies, library skeleton |
| `SNAPSHOT_OMISSIONS.json` | Every excluded file |

---

## Run command

    python scripts/make_snapshot.py

Optional flags:
    --include-library       Include codex/library/ bulk contents
    --include-atlas-heavy   Include large atlas payloads
    --max-file-mb <N>       Override file size limit (default 0.5)
    --output <path>         Custom output path
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Build and validate
# ═══════════════════════════════════════════════════════════════════════════════

def build_snapshot(opts: argparse.Namespace) -> Path:
    ts       = datetime.now(tz=timezone.utc).isoformat()
    zip_path = Path(opts.output) if opts.output else ROOT / "helix_snapshot.zip"

    print(f"Scanning repo at: {ROOT}")
    included, indexed, omitted = walk_repo(
        max_file_mb=opts.max_file_mb,
        include_library=opts.include_library,
        include_atlas_heavy=opts.include_atlas_heavy,
    )
    print(f"  included: {len(included)}  indexed: {len(indexed)}  omitted: {len(omitted)}")

    print("Building library skeleton…")
    lib_skeleton = build_library_skeleton()
    print(f"  library: {lib_skeleton.get('total_files','?')} files, {lib_skeleton.get('total_mb','?')} MB")

    print("Generating metadata…")
    tree_txt       = make_tree_txt(included, indexed, omitted)
    tree_json      = make_tree_json(included, indexed, omitted)
    omissions_json = make_omissions_json(indexed, omitted)
    manifest_json  = make_snapshot_manifest(included, indexed, omitted, lib_skeleton, opts, ts)

    print(f"Writing {zip_path.name}…")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as zf:
        for entry in sorted(included, key=lambda x: x["rel"]):
            zf.write(entry["abs"], arcname=entry["rel"])

        zf.writestr("SNAPSHOT_README.md",      SNAPSHOT_README)
        zf.writestr("SNAPSHOT_MANIFEST.json",  manifest_json)
        zf.writestr("SNAPSHOT_TREE.txt",       tree_txt)
        zf.writestr("SNAPSHOT_TREE.json",      tree_json)
        zf.writestr("SNAPSHOT_OMISSIONS.json", omissions_json)

    zip_size_mb = _size_mb(zip_path.stat().st_size)
    print(f"  Done: {zip_path.name} ({zip_size_mb:.1f} MB)")

    # ── Validate ──────────────────────────────────────────────────────────────
    print("Validating…")
    errors: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        for req in ["SNAPSHOT_README.md", "SNAPSHOT_MANIFEST.json",
                    "SNAPSHOT_TREE.txt", "SNAPSHOT_TREE.json", "SNAPSHOT_OMISSIONS.json"]:
            if req not in names:
                errors.append(f"MISSING metadata: {req}")
        if "MANIFEST.yaml" not in names:
            errors.append("MISSING: MANIFEST.yaml")
        if "docs/README.md" not in names:
            errors.append("MISSING: docs/README.md")
        if not any(n.startswith("domains/") and n.endswith("manifest.yaml") for n in names):
            errors.append("MISSING: domain manifest.yaml files")

    if errors:
        print("  VALIDATION FAILED:")
        for e in errors:
            print(f"    ✗ {e}")
        sys.exit(1)
    else:
        print("  Passed.")

    print(f"\nSnapshot: {zip_path}  ({zip_size_mb:.1f} MB)")
    print(f"  {len(included)} files included  |  {len(indexed)} indexed  |  {len(omitted)} omitted")
    return zip_path


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a compact LLM-ingestible Helix snapshot zip."
    )
    p.add_argument("--include-library",     action="store_true",
                   help="Include codex/library/ bulk content")
    p.add_argument("--include-atlas-heavy", action="store_true",
                   help="Include large atlas payloads (> ATLAS_SMALL_FILE_MB)")
    p.add_argument("--max-file-mb",         type=float, default=DEFAULT_MAX_FILE_MB,
                   help=f"Max file size to include in MB (default {DEFAULT_MAX_FILE_MB})")
    p.add_argument("--output",              type=str, default=None,
                   help="Custom output path (default: helix_snapshot.zip in repo root)")
    return p.parse_args()


if __name__ == "__main__":
    build_snapshot(parse_args())


