"""
report_generator.py — Composer Summary Table + Knowledge Graph Report
======================================================================
Generates structured output tables from ComposerGraph + analysis results.

Output formats
--------------
- Markdown (.md)   — always available
- JSON (.json)     — always available
- CSV (.csv)       — always available (stdlib)

Report types
------------
generate_composer_table(graph, out_dir)
    One-row-per-composer: biography overview, external links, major works,
    stylistic fingerprint summary, cluster memberships, style traits.

generate_track_attribution_report(game_id, graph, out_dir)
    Per-track attribution table with composer names, confidence, source.

generate_knowledge_graph_summary(graph, out_dir)
    Node/edge counts, most-connected composers, cluster statistics.

generate_style_fingerprint_report(composers, vectors, out_dir)
    Composer fingerprint vector summary with PCA projection if available.

generate_all(game_id, graph, vectors, out_dir)
    Calls all generators and returns dict of {report_name: path}.
"""

from __future__ import annotations

import csv
import json
import logging
import math
from io import StringIO
from pathlib import Path
from typing import Any

from domains.music.atlas_integration.composer_graph import ComposerGraph

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Composer table
# ---------------------------------------------------------------------------

def generate_composer_table(
    graph:   ComposerGraph,
    out_dir: Path,
) -> dict[str, Path]:
    """
    Generate per-composer summary tables.
    Columns: composer_id, full_name, nationality, years_active, instruments,
             studios, teams, wikidata, vgmdb, musicbrainz, lastfm_url,
             bio_summary, style_traits_summary, track_count.
    """
    rows: list[dict[str, Any]] = []

    for c in sorted(graph.all_composers(), key=lambda x: x.full_name):
        track_nodes = graph.tracks_for_composer(c.composer_id)
        game_nodes  = graph.games_for_composer(c.composer_id)

        ext = c.external_ids
        rows.append({
            "composer_id":    c.composer_id,
            "full_name":      c.full_name,
            "aliases":        " | ".join(c.aliases[:3]) if c.aliases else "",
            "nationality":    c.nationality or "",
            "birth_year":     c.birth_year or "",
            "years_active":   c.years_active or "",
            "instruments":    ", ".join(c.instruments[:4]) if c.instruments else "",
            "studios":        " | ".join(c.studios[:3]) if c.studios else "",
            "teams":          " | ".join(c.sound_teams[:2]) if c.sound_teams else "",
            "track_count":    len(track_nodes),
            "game_count":     len(game_nodes),
            "games":          " | ".join(g.title for g in game_nodes[:3]),
            "major_works":    " | ".join(
                (t.title or t.track_id) for t in track_nodes[:4]
            ),
            "wikidata":       ext.get("wikidata", ""),
            "wikipedia":      ext.get("wikipedia", ""),
            "musicbrainz":    ext.get("musicbrainz", ""),
            "vgmdb":          ext.get("vgmdb", ""),
            "lastfm_url":     ext.get("lastfm_url", ""),
            "bio_summary":    (c.bio_summary or "")[:200].replace("\n", " "),
            "primary_chip":   c.style_traits.get("primary_chip", ""),
            "driver":         c.style_traits.get("driver", ""),
            "mb_tags":        ", ".join(c.style_traits.get("mb_tags", [])[:4]),
            "cluster_ids":    ", ".join(c.cluster_memberships[:3]) if c.cluster_memberships else "",
            "fingerprint_dim": len(c.fingerprint_vector) if c.fingerprint_vector else 0,
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    # JSON
    json_path = out_dir / "composer_table.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    paths["json"] = json_path

    # CSV
    csv_path = out_dir / "composer_table.csv"
    if rows:
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        csv_path.write_text(buf.getvalue(), encoding="utf-8")
    paths["csv"] = csv_path

    # Markdown
    md_path = out_dir / "composer_table.md"
    md_path.write_text(_rows_to_markdown(
        rows,
        title="## Composer Summary Table",
        cols=["full_name", "nationality", "track_count", "wikidata",
              "vgmdb", "musicbrainz", "primary_chip", "driver", "bio_summary"],
    ), encoding="utf-8")
    paths["md"] = md_path

    log.info("report_generator: wrote composer table (%d rows) → %s", len(rows), out_dir)
    return paths


# ---------------------------------------------------------------------------
# Track attribution report
# ---------------------------------------------------------------------------

def generate_track_attribution_report(
    game_id: str,
    graph:   ComposerGraph,
    out_dir: Path,
) -> dict[str, Path]:
    """
    Per-track attribution for a single game.
    Columns: track_id, title, track_number, duration_sec,
             composers (names), attribution_confidence, sources.
    """
    game = graph.get_game(game_id)
    if not game:
        log.warning("report_generator: game '%s' not found", game_id)
        return {}

    tracks = sorted(
        [t for t in graph.all_tracks() if t.game_id == game_id],
        key=lambda t: (t.track_number or 999, t.track_id),
    )

    rows: list[dict[str, Any]] = []
    for t in tracks:
        composers   = graph.composers_for_track(t.track_id)
        comp_names  = " | ".join(c.full_name for c in composers)
        comp_conf   = t.attribution_confidence

        # Gather attribution source from relationships
        attribution_rels = [
            r for r in graph.all_relationships()
            if r.target == f"track:{t.track_id}" and r.relation in ("attributed_to", "wrote", "arranged")
        ]
        sources = " | ".join(sorted({r.source_name for r in attribution_rels if r.source_name}))

        rows.append({
            "track_number":          t.track_number or "",
            "track_id":              t.track_id,
            "title":                 t.title or t.track_id,
            "duration_sec":          round(t.duration_sec, 1) if t.duration_sec else "",
            "chip":                  t.chip or "",
            "composers":             comp_names,
            "attribution_confidence": round(comp_conf, 2) if comp_conf is not None else "",
            "attribution_sources":   sources,
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    json_path = out_dir / f"track_attribution_{game_id}.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    paths["json"] = json_path

    csv_path = out_dir / f"track_attribution_{game_id}.csv"
    if rows:
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        csv_path.write_text(buf.getvalue(), encoding="utf-8")
    paths["csv"] = csv_path

    md_lines = [
        f"## Track Attribution: {game.title}",
        "",
        f"Platform: {game.platform}  |  Year: {game.year}  |  Developer: {game.developer}",
        "",
    ]
    md_lines += _rows_to_markdown_lines(
        rows,
        cols=["track_number", "title", "duration_sec", "composers",
              "attribution_confidence", "attribution_sources"],
    )
    md_path = out_dir / f"track_attribution_{game_id}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    paths["md"] = md_path

    log.info("report_generator: wrote track attribution (%d tracks) → %s", len(rows), out_dir)
    return paths


# ---------------------------------------------------------------------------
# Knowledge graph summary
# ---------------------------------------------------------------------------

def generate_knowledge_graph_summary(
    graph:   ComposerGraph,
    out_dir: Path,
) -> dict[str, Path]:
    """
    High-level summary of the knowledge graph state.
    """
    stats = graph.graph_stats()

    # Most-connected composers (by relationship count)
    composer_rel_counts: dict[str, int] = {}
    for rel in graph.all_relationships():
        for part in (rel.source, rel.target):
            if part.startswith("composer:"):
                cid = part.removeprefix("composer:")
                composer_rel_counts[cid] = composer_rel_counts.get(cid, 0) + 1

    top_composers = sorted(composer_rel_counts.items(), key=lambda x: -x[1])[:10]
    top_composer_rows = []
    for cid, count in top_composers:
        c = graph.get_composer(cid)
        top_composer_rows.append({
            "composer_id": cid,
            "full_name":   c.full_name if c else cid,
            "relationships": count,
        })

    # Relation type distribution
    rel_type_dist: dict[str, int] = {}
    for rel in graph.all_relationships():
        rel_type_dist[rel.relation] = rel_type_dist.get(rel.relation, 0) + 1

    summary = {
        "entity_counts":       stats,
        "top_composers_by_connections": top_composer_rows,
        "relationship_type_distribution": sorted(
            rel_type_dist.items(), key=lambda x: -x[1]
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    json_path = out_dir / "knowledge_graph_summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    paths["json"] = json_path

    md_lines = [
        "## Knowledge Graph Summary",
        "",
        "### Entity Counts",
        "",
    ]
    for k, v in stats.items():
        md_lines.append(f"- **{k}**: {v}")
    md_lines += [
        "",
        "### Top Composers by Connections",
        "",
    ]
    md_lines += _rows_to_markdown_lines(
        top_composer_rows,
        cols=["full_name", "relationships"],
    )
    md_lines += [
        "",
        "### Relationship Type Distribution",
        "",
    ]
    for rel_type, count in summary["relationship_type_distribution"]:
        md_lines.append(f"- `{rel_type}`: {count}")

    md_path = out_dir / "knowledge_graph_summary.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    paths["md"] = md_path

    log.info("report_generator: wrote knowledge graph summary → %s", out_dir)
    return paths


# ---------------------------------------------------------------------------
# Style fingerprint report
# ---------------------------------------------------------------------------

def generate_style_fingerprint_report(
    graph:   ComposerGraph,
    vectors: dict[str, list[float]],
    out_dir: Path,
) -> dict[str, Path]:
    """
    Per-composer fingerprint vector statistics.
    Includes: mean, std-dev, top-5 dimensions by magnitude, cosine similarity matrix.
    """
    # Build composer centroid vectors
    centroids: dict[str, list[float]] = {}
    for c in graph.all_composers():
        if c.fingerprint_vector:
            centroids[c.composer_id] = c.fingerprint_vector
        else:
            tracks = graph.tracks_for_composer(c.composer_id)
            vecs = [vectors[t.track_id] for t in tracks if t.track_id in vectors]
            if vecs:
                dim = len(vecs[0])
                centroids[c.composer_id] = [
                    sum(v[i] for v in vecs) / len(vecs) for i in range(dim)
                ]

    rows: list[dict[str, Any]] = []
    comp_ids = sorted(centroids.keys())

    for cid in comp_ids:
        c   = graph.get_composer(cid)
        vec = centroids[cid]
        mean = sum(vec) / len(vec) if vec else 0.0
        std  = math.sqrt(sum((x - mean) ** 2 for x in vec) / len(vec)) if len(vec) > 1 else 0.0
        top5_dims = sorted(enumerate(vec), key=lambda x: -abs(x[1]))[:5]

        rows.append({
            "composer_id":   cid,
            "full_name":     c.full_name if c else cid,
            "vector_dim":    len(vec),
            "mean":          round(mean, 4),
            "std_dev":       round(std, 4),
            "top5_dims":     str([f"dim{i}={v:.3f}" for i, v in top5_dims]),
        })

    # Cosine similarity matrix (JSON only)
    sim_matrix = {}
    for a in comp_ids:
        sim_matrix[a] = {}
        for b in comp_ids:
            sim_matrix[a][b] = round(_cosine(centroids[a], centroids[b]), 4)

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    json_payload = {"fingerprint_stats": rows, "cosine_similarity_matrix": sim_matrix}
    json_path = out_dir / "style_fingerprint_report.json"
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    paths["json"] = json_path

    if rows:
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        csv_path = out_dir / "style_fingerprint_report.csv"
        csv_path.write_text(buf.getvalue(), encoding="utf-8")
        paths["csv"] = csv_path

    md_path = out_dir / "style_fingerprint_report.md"
    md_path.write_text(_rows_to_markdown(
        rows,
        title="## Composer Style Fingerprint Report",
        cols=["full_name", "vector_dim", "mean", "std_dev", "top5_dims"],
    ), encoding="utf-8")
    paths["md"] = md_path

    # Similarity matrix as Markdown grid (composers only)
    if len(comp_ids) <= 12:
        sim_md_path = out_dir / "composer_similarity_matrix.md"
        _write_sim_matrix_md(comp_ids, sim_matrix, graph, sim_md_path)
        paths["sim_matrix_md"] = sim_md_path

    log.info("report_generator: wrote style fingerprint report (%d composers)", len(rows))
    return paths


# ---------------------------------------------------------------------------
# generate_all
# ---------------------------------------------------------------------------

def generate_all(
    game_id:  str,
    graph:    ComposerGraph,
    vectors:  dict[str, list[float]],
    out_dir:  Path,
) -> dict[str, dict[str, Path]]:
    """Run all report generators. Returns nested dict of report → format → path."""
    return {
        "composer_table":        generate_composer_table(graph, out_dir),
        "track_attribution":     generate_track_attribution_report(game_id, graph, out_dir),
        "graph_summary":         generate_knowledge_graph_summary(graph, out_dir),
        "style_fingerprint":     generate_style_fingerprint_report(graph, vectors, out_dir),
    }


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def _rows_to_markdown(
    rows:  list[dict[str, Any]],
    title: str = "",
    cols:  list[str] | None = None,
) -> str:
    lines = []
    if title:
        lines += [title, ""]
    lines += _rows_to_markdown_lines(rows, cols)
    return "\n".join(lines)


def _rows_to_markdown_lines(
    rows: list[dict[str, Any]],
    cols: list[str] | None = None,
) -> list[str]:
    if not rows:
        return ["*(no data)*"]
    cols = cols or list(rows[0].keys())
    header   = "| " + " | ".join(cols) + " |"
    divider  = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, divider]
    for row in rows:
        cells = [str(row.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _write_sim_matrix_md(
    comp_ids: list[str],
    matrix:   dict[str, dict[str, float]],
    graph:    ComposerGraph,
    path:     Path,
) -> None:
    names = {cid: (graph.get_composer(cid).full_name if graph.get_composer(cid) else cid)
             for cid in comp_ids}
    short = {cid: names[cid].split()[0] for cid in comp_ids}

    lines = ["## Composer Cosine Similarity Matrix", ""]
    header  = "| | " + " | ".join(short[c] for c in comp_ids) + " |"
    divider = "| --- | " + " | ".join("---" for _ in comp_ids) + " |"
    lines += [header, divider]
    for a in comp_ids:
        cells = [f"{matrix[a][b]:.2f}" for b in comp_ids]
        lines.append(f"| **{short[a]}** | " + " | ".join(cells) + " |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na > 1e-10 and nb > 1e-10 else 0.0
