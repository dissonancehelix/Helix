#!/usr/bin/env python3
"""Read-only workstation snapshot.

Inventories the Helix repo and configured sources without modifying anything.
Outputs JSON + Markdown under reports/analyses/workstation/.

Safety rules:
- Never follows symlinks.
- Never recurses into ignored folders.
- Never deep-scans roots flagged shallow unless --deep is supplied.
- Refuses to write outputs outside the repo root.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

# ---- config loading ---------------------------------------------------------

DEFAULT_IGNORE = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}

DEFAULT_CONFIG = {
    "version": 0.1,
    "roots": [
        {"id": "source.repo_root", "path": ".", "recursive": True, "max_depth": 3},
        {"id": "source.data_lake", "path": "data/", "recursive": False, "max_depth": 1},
    ],
    "ignore": sorted(DEFAULT_IGNORE),
    "outputs": {"directory": "reports/analyses/workstation"},
}

LOCKED_ROOT_DIRS = ["model", "data", "system", "labs", "reports", "quarantine"]
LOCKED_ROOT_FILES = ["README.md", "DISSONANCE.md", "AGENTS.md"]
MAP_YAMLS = ["patterns.yaml", "gates.yaml", "examples.yaml", "probes.yaml", "anomalies.yaml", "links.yaml", "sources.yaml"]


def load_config(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return DEFAULT_CONFIG
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
    except ImportError:
        # Minimal fallback: just use defaults if PyYAML missing.
        sys.stderr.write("warn: PyYAML not installed; using built-in defaults\n")
        return DEFAULT_CONFIG
    if not isinstance(data, dict):
        return DEFAULT_CONFIG
    # Fill in missing keys from defaults.
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    if "ignore" not in merged or not merged["ignore"]:
        merged["ignore"] = sorted(DEFAULT_IGNORE)
    return merged


# ---- scanning ---------------------------------------------------------------

def walk_root(root: Path, ignore: set[str], max_depth: int | None, deep: bool) -> tuple[int, int]:
    """Return (file_count, byte_count) for a root, respecting safety rules."""
    if not root.exists():
        return 0, 0
    files = 0
    bytes_ = 0
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        cur = Path(dirpath)
        rel_depth = len(cur.parts) - root_depth
        if max_depth is not None and not deep and rel_depth >= max_depth:
            dirnames[:] = []
        # Prune ignored dirs.
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for name in filenames:
            p = cur / name
            try:
                if p.is_symlink():
                    continue
                bytes_ += p.stat().st_size
                files += 1
            except OSError:
                continue
    return files, bytes_


def top_level_inventory(root: Path, ignore: set[str]) -> list[dict]:
    out: list[dict] = []
    for p in sorted(root.iterdir(), key=lambda x: x.name.lower()):
        if p.name in ignore:
            continue
        if p.name.startswith(".") and p.name not in {".gitignore", ".gitattributes"}:
            continue
        entry: dict = {"name": p.name, "kind": "dir" if p.is_dir() else "file"}
        if p.is_dir():
            entry["has_readme"] = (p / "README.md").is_file()
        out.append(entry)
    return out


def coverage(root: Path, kind_dir: str) -> tuple[list[str], list[str]]:
    """Return (covered, missing) immediate-child folders by README presence."""
    base = root / kind_dir
    if not base.is_dir():
        return [], []
    covered: list[str] = []
    missing: list[str] = []
    skip = {"__pycache__"}
    for p in sorted(base.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir() or p.name.startswith(".") or p.name in skip:
            continue
        has = (p / "README.md").is_file() or (p / "README.template.md").is_file()
        (covered if has else missing).append(p.name)
    return covered, missing


def load_sources(root: Path) -> list[dict]:
    sources_path = root / "model" / "map" / "sources.yaml"
    if not sources_path.is_file():
        return []
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
    except ImportError:
        return []
    except Exception:
        return []
    return []


# ---- snapshot ---------------------------------------------------------------

def build_snapshot(root: Path, config: dict, deep: bool) -> dict:
    ignore = set(config.get("ignore") or DEFAULT_IGNORE)
    warnings: list[str] = []

    # Required-shape checks.
    for f in LOCKED_ROOT_FILES:
        if not (root / f).is_file():
            warnings.append(f"missing root file: {f}")
    for d in LOCKED_ROOT_DIRS:
        if not (root / d).is_dir():
            warnings.append(f"missing root dir: {d}/")

    for y in MAP_YAMLS:
        if not (root / "model" / "map" / y).is_file():
            warnings.append(f"missing map yaml: model/map/{y}")

    # Source registry.
    sources_registry = load_sources(root)
    if not sources_registry:
        warnings.append("model/map/sources.yaml is missing or empty")

    # Source scan.
    sources_out: list[dict] = []
    files_total = 0
    bytes_total = 0
    for r in config.get("roots") or []:
        rid = r.get("id", "")
        rpath = (root / r.get("path", ".")).resolve()
        recursive = bool(r.get("recursive", True))
        max_depth = r.get("max_depth")
        if not rpath.exists():
            sources_out.append({
                "id": rid,
                "path": str(rpath.relative_to(root)) if rpath.is_relative_to(root) else str(rpath),
                "exists": False,
                "files": 0,
                "bytes": 0,
                "skipped": True,
                "skipped_reason": "path not found",
            })
            warnings.append(f"source path not found: {rid} -> {rpath}")
            continue
        skipped = False
        skipped_reason = ""
        if not recursive and not deep:
            # Shallow: just count immediate children.
            files = sum(1 for p in rpath.iterdir() if p.is_file() and not p.is_symlink())
            bytes_ = sum(p.stat().st_size for p in rpath.iterdir() if p.is_file() and not p.is_symlink())
            skipped = True
            skipped_reason = "shallow scan; pass --deep for full recursion"
        else:
            files, bytes_ = walk_root(rpath, ignore, max_depth, deep)
        try:
            rel = str(rpath.relative_to(root))
        except ValueError:
            rel = str(rpath)
        sources_out.append({
            "id": rid,
            "path": rel,
            "exists": True,
            "files": files,
            "bytes": bytes_,
            "skipped": skipped,
            "skipped_reason": skipped_reason,
        })
        files_total += files
        bytes_total += bytes_

    # Coverage.
    domain_cov, domain_miss = coverage(root, "model/domains")
    tools_cov, tools_miss = coverage(root, "system/tools")
    labs_cov, labs_miss = coverage(root, "labs")
    for name in domain_miss:
        warnings.append(f"domain missing README: model/domains/{name}/")
    for name in tools_miss:
        warnings.append(f"tool missing README: system/tools/{name}/")
    for name in labs_miss:
        warnings.append(f"lab missing README: labs/{name}/")

    snapshot = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "repo_root": str(root.resolve()),
        "mode": "deep" if deep else "shallow",
        "sources": sources_out,
        "top_level_inventory": top_level_inventory(root, ignore),
        "files_scanned": files_total,
        "bytes_scanned": bytes_total,
        "warnings": warnings,
        # Auxiliary detail used for the markdown report; not in the schema's
        # required set.
        "_coverage": {
            "domains": {"covered": domain_cov, "missing": domain_miss},
            "tools": {"covered": tools_cov, "missing": tools_miss},
            "labs": {"covered": labs_cov, "missing": labs_miss},
        },
        "_sources_registry": sources_registry,
    }
    return snapshot


# ---- markdown ---------------------------------------------------------------

def fmt_bytes(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PiB"


def render_markdown(snapshot: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Workstation Snapshot — {snapshot['generated_at']}")
    lines.append("")
    lines.append(f"- **Repo root:** `{snapshot['repo_root']}`")
    lines.append(f"- **Mode:** {snapshot['mode']}")
    lines.append(f"- **Files scanned:** {snapshot['files_scanned']}")
    lines.append(f"- **Bytes scanned:** {fmt_bytes(snapshot['bytes_scanned'])}")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.append("| ID | Path | Exists | Files | Bytes | Skipped |")
    lines.append("|---|---|---|---|---|---|")
    for s in snapshot["sources"]:
        skipped = s["skipped_reason"] if s["skipped"] else ""
        lines.append(
            f"| `{s['id']}` | `{s['path']}` | {s['exists']} | {s['files']} | {fmt_bytes(s['bytes'])} | {skipped} |"
        )
    lines.append("")
    reg = snapshot.get("_sources_registry", [])
    if reg:
        lines.append("### Source registry (model/map/sources.yaml)")
        lines.append("")
        for item in reg:
            lines.append(
                f"- `{item.get('id','')}` — {item.get('title','')} "
                f"[{item.get('status','')}, {item.get('mode','')}] @ `{item.get('canonical_home','')}`"
            )
        lines.append("")
    lines.append("## Top-level inventory")
    lines.append("")
    for entry in snapshot["top_level_inventory"]:
        marker = "📄" if entry["kind"] == "file" else "📁"
        readme = ""
        if entry["kind"] == "dir":
            readme = " (README)" if entry.get("has_readme") else " (no README)"
        lines.append(f"- {marker} `{entry['name']}`{readme}")
    lines.append("")
    cov = snapshot.get("_coverage", {})
    labels = {
        "domains": "model/domains",
        "tools": "system/tools",
        "labs": "labs",
    }
    for label in ("domains", "tools", "labs"):
        c = cov.get(label, {})
        if not c:
            continue
        lines.append(f"## {labels[label]} README coverage")
        lines.append("")
        lines.append(f"- Covered ({len(c.get('covered', []))}): {', '.join(c.get('covered', [])) or '(none)'}")
        lines.append(f"- Missing ({len(c.get('missing', []))}): {', '.join(c.get('missing', [])) or '(none)'}")
        lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if snapshot["warnings"]:
        for w in snapshot["warnings"]:
            lines.append(f"- {w}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Next recommended actions")
    lines.append("")
    next_actions: list[str] = []
    if any("missing" in w for w in snapshot["warnings"]):
        next_actions.append("Resolve `missing` warnings above (add READMEs / map files).")
    if snapshot["mode"] == "shallow":
        next_actions.append("Re-run with `--deep` if a complete byte/file count is required.")
    if not snapshot.get("_sources_registry"):
        next_actions.append("Populate `model/map/sources.yaml`.")
    if not next_actions:
        next_actions.append("None — workspace is in good shape.")
    for a in next_actions:
        lines.append(f"- {a}")
    lines.append("")
    return "\n".join(lines)


# ---- main -------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Read-only workstation/repo snapshot.")
    p.add_argument("--root", default=".", help="Repo root (default: .)")
    p.add_argument("--config", default="system/tools/workstation_bridge/config.example.yaml", help="Config YAML")
    p.add_argument("--out", default="reports/analyses/workstation", help="Output directory (within repo)")
    p.add_argument("--deep", action="store_true", help="Recurse fully, including shallow-flagged roots")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: --root not a directory: {root}", file=sys.stderr)
        return 2

    config_path = (root / args.config) if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_path)

    out_dir = (root / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out).resolve()
    if not out_dir.is_relative_to(root):
        print(f"error: --out resolves outside repo root: {out_dir}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot = build_snapshot(root, config, deep=args.deep)

    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"workstation_snapshot_{ts}.json"
    md_path = out_dir / f"workstation_snapshot_{ts}.md"

    # Strip private fields from the JSON serialization so it matches the schema.
    public = {k: v for k, v in snapshot.items() if not k.startswith("_")}
    json_path.write_text(json.dumps(public, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(snapshot), encoding="utf-8")

    print(f"wrote {json_path.relative_to(root)}")
    print(f"wrote {md_path.relative_to(root)}")
    if snapshot["warnings"]:
        print(f"({len(snapshot['warnings'])} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

