"""
Helix Snapshot Generator
========================
Produces helix_snapshot.zip — a compact, deterministic export of the repo
optimised for LLM context ingestion.

Usage:
    python scripts/make_snapshot.py
    python scripts/make_snapshot.py --include-library
    python scripts/make_snapshot.py --include-atlas-heavy
    python scripts/make_snapshot.py --max-file-mb 1.0
    python scripts/make_snapshot.py --output C:/exports/helix.zip

Schema version: snapshot_schema_v1
"""

import argparse
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "snapshot_schema_v1"
DEFAULT_MAX_FILE_MB = 0.5
DEFAULT_OUTPUT = "helix_snapshot.zip"

# File extensions included at full content (under size limit)
FULL_CONTENT_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".ps1", ".ebnf",
    ".hsl", ".jsonl", ".cfg", ".ini", ".env.example",
}

# Directories always excluded entirely
EXCLUDE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules",
    "outputs", ".mypy_cache", ".venv", "venv", "env",
    "model/domains/music/toolkits",  # large external submodules
}

# Paths indexed but not included in full (too large or bulk data)
INDEX_ONLY_PREFIXES = (
    "codex/library/music",
    "codex/library/tech",
    "codex/atlas/embeddings",
    "model/domains/music/data",
    "model/domains/music/outputs",
    "model/domains/music/artifacts",
    "model/domains/language/artifacts",
    "model/domains/language/data/datasets",
)

# Binary extensions — indexed only, never full content
BINARY_EXTENSIONS = {
    ".mp3", ".ogg", ".flac", ".wav", ".opus", ".m4a",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico",
    ".vgm", ".vgz", ".spc", ".nsf", ".psf",
    ".db", ".sqlite", ".sqlite3",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo",
    ".fpl", ".m3u", ".m3u8",
}


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def should_exclude_dir(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for excl in EXCLUDE_DIRS:
        excl_parts = excl.split("/")
        if parts[: len(excl_parts)] == excl_parts:
            return True
    return False


def classify_file(rel_path: str, size_bytes: int, max_bytes: int) -> str:
    """Returns 'FULL', 'INDEXED', or 'OMITTED'."""
    rel_path_fwd = rel_path.replace("\\", "/")
    ext = Path(rel_path).suffix.lower()

    # Always omit binaries
    if ext in BINARY_EXTENSIONS:
        return "INDEXED"

    # Index-only path prefixes
    for prefix in INDEX_ONLY_PREFIXES:
        if rel_path_fwd.startswith(prefix):
            return "INDEXED"

    # Text files within size limit
    if ext in FULL_CONTENT_EXTENSIONS and size_bytes <= max_bytes:
        return "FULL"

    # Text files over size limit
    if ext in FULL_CONTENT_EXTENSIONS and size_bytes > max_bytes:
        return "INDEXED"

    return "OMITTED"


def build_tree_line(rel_path: str, classification: str) -> str:
    return f"{classification:<8} {rel_path}"


def make_snapshot(
    output_path: str = DEFAULT_OUTPUT,
    max_file_mb: float = DEFAULT_MAX_FILE_MB,
    include_library: bool = False,
    include_atlas_heavy: bool = False,
) -> None:
    repo_root = get_repo_root()
    max_bytes = int(max_file_mb * 1024 * 1024)
    output_abs = Path(output_path) if Path(output_path).is_absolute() else repo_root / output_path

    # Adjust index-only prefixes based on flags
    index_prefixes = list(INDEX_ONLY_PREFIXES)
    if include_library:
        index_prefixes = [p for p in index_prefixes if not p.startswith("codex/library")]
    if include_atlas_heavy:
        index_prefixes = [p for p in index_prefixes if not p.startswith("codex/atlas/embeddings")]

    files_full = []       # (rel_path, abs_path)
    files_indexed = []    # (rel_path, size_bytes, reason)
    files_omitted = []    # (rel_path, size_bytes, reason)

    for dirpath, dirnames, filenames in os.walk(repo_root):
        rel_dir = os.path.relpath(dirpath, repo_root).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""

        # Prune excluded dirs in-place
        dirnames[:] = [
            d for d in sorted(dirnames)
            if not should_exclude_dir(
                (rel_dir + "/" + d).lstrip("/")
            )
        ]

        for fname in sorted(filenames):
            abs_path = Path(dirpath) / fname
            rel_path = (rel_dir + "/" + fname).lstrip("/") if rel_dir else fname
            rel_path_fwd = rel_path.replace("\\", "/")

            # Skip the output file itself
            try:
                if abs_path.resolve() == output_abs.resolve():
                    continue
            except Exception:
                pass

            try:
                size = abs_path.stat().st_size
            except OSError:
                continue

            classification = classify_file(rel_path_fwd, size, max_bytes)

            if classification == "FULL":
                files_full.append((rel_path_fwd, abs_path))
            elif classification == "INDEXED":
                reason = "binary" if Path(rel_path).suffix.lower() in BINARY_EXTENSIONS else (
                    "index_only_path" if any(rel_path_fwd.startswith(p) for p in index_prefixes)
                    else "over_size_limit"
                )
                files_indexed.append((rel_path_fwd, size, reason))
            else:
                files_omitted.append((rel_path_fwd, size, "unknown_type"))

    # Build metadata
    timestamp = datetime.now(timezone.utc).isoformat()
    total_files = len(files_full) + len(files_indexed) + len(files_omitted)

    snapshot_manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "options": {
            "max_file_mb": max_file_mb,
            "include_library": include_library,
            "include_atlas_heavy": include_atlas_heavy,
        },
        "stats": {
            "total_files_found": total_files,
            "files_included_full": len(files_full),
            "files_indexed": len(files_indexed),
            "files_omitted": len(files_omitted),
        },
        "included_files": [p for p, _ in files_full],
    }

    tree_lines = (
        [build_tree_line(p, "FULL") for p, _ in files_full]
        + [build_tree_line(p, "INDEXED") for p, _, _ in files_indexed]
        + [build_tree_line(p, "OMITTED") for p, _, _ in files_omitted]
    )
    tree_lines.sort(key=lambda x: x[9:])  # sort by path (after classification prefix)

    omissions = [
        {"path": p, "size_bytes": s, "reason": r}
        for p, s, r in sorted(files_indexed + files_omitted)
    ]

    snapshot_readme = f"""# Helix Snapshot

Generated: {timestamp}
Schema: {SCHEMA_VERSION}

This zip is a structural export of the Helix repository for LLM context ingestion.
It is NOT a backup. It contains source code, documentation, and manifests — not bulk data.

## How to read this snapshot

1. Read README.md first — it describes the full system architecture
2. Read MANIFEST.yaml — machine-readable structural index
3. Explore docs/ for formal specifications
4. Check SNAPSHOT_TREE.txt to see what was included vs indexed vs omitted

## What is NOT included

Bulk data (codex/library/, large atlas payloads, audio files) is listed in
SNAPSHOT_OMISSIONS.json with sizes and reasons. Everything that exists in the
repo is accounted for — either FULL content or an index entry.

## Stats

- Files included (full content): {len(files_full)}
- Files indexed (path + size only): {len(files_indexed)}
- Files omitted: {len(files_omitted)}
"""

    print(f"Writing snapshot to {output_abs}")
    print(f"  Full content: {len(files_full)} files")
    print(f"  Indexed only: {len(files_indexed)} files")
    print(f"  Omitted:      {len(files_omitted)} files")

    with zipfile.ZipFile(output_abs, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Write source files
        for rel_path, abs_path in files_full:
            try:
                zf.write(abs_path, rel_path)
            except (OSError, PermissionError) as e:
                print(f"  WARNING: could not read {rel_path}: {e}")

        # Write metadata
        zf.writestr("SNAPSHOT_README.md", snapshot_readme)
        zf.writestr("SNAPSHOT_MANIFEST.json", json.dumps(snapshot_manifest, indent=2))
        zf.writestr("SNAPSHOT_TREE.txt", "\n".join(tree_lines))
        zf.writestr("SNAPSHOT_OMISSIONS.json", json.dumps(omissions, indent=2))

    size_mb = output_abs.stat().st_size / (1024 * 1024)
    print(f"Done. Output: {output_abs} ({size_mb:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Helix repo snapshot for LLM ingestion")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output zip path")
    parser.add_argument("--max-file-mb", type=float, default=DEFAULT_MAX_FILE_MB,
                        help="Max file size to include in full (default: 0.5 MB)")
    parser.add_argument("--include-library", action="store_true",
                        help="Include codex/library/ bulk content")
    parser.add_argument("--include-atlas-heavy", action="store_true",
                        help="Include codex/atlas/embeddings/ payloads")
    args = parser.parse_args()

    make_snapshot(
        output_path=args.output,
        max_file_mb=args.max_file_mb,
        include_library=args.include_library,
        include_atlas_heavy=args.include_atlas_heavy,
    )


if __name__ == "__main__":
    main()

