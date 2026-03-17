"""
visualizer.py — Knowledge Graph Visualization
==============================================
Generates static and interactive graph visualizations from ComposerGraph.

Output formats
--------------
- GEXF  (.gexf)  — Gephi-compatible XML; always available
- DOT   (.dot)   — Graphviz format; always available
- PNG   (.png)   — matplotlib spring layout; requires matplotlib + networkx
- HTML  (.html)  — interactive Plotly force-directed graph; requires plotly + networkx

Visualization types
-------------------
render_collaboration_network(graph, out_dir)
    Composer nodes; edges = collaborated_with + member_of.

render_stylistic_similarity(graph, vectors, out_dir)
    Composer nodes sized by track count; edges = cosine similarity > threshold.

render_soundtrack_clusters(game_id, graph, vectors, out_dir)
    Track nodes coloured by cluster; composer nodes as hubs.

render_studio_influence_network(graph, out_dir)
    Studio + sound team nodes; edges = worked_at + member_of.

render_all(game_id, graph, vectors, out_dir)
    Calls all four renderers.
"""

from __future__ import annotations

import json
import logging
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from substrates.music.atlas_integration.composer_graph import ComposerGraph

log = logging.getLogger(__name__)

# Optional imports
try:
    import networkx as _nx
    _HAS_NX = True
except ImportError:
    _nx = None  # type: ignore
    _HAS_NX = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt
    import matplotlib.colors as _mcolors
    _HAS_MPL = True
except ImportError:
    _plt = None  # type: ignore
    _mcolors = None  # type: ignore
    _HAS_MPL = False

try:
    import plotly.graph_objects as _go
    _HAS_PLOTLY = True
except ImportError:
    _go = None  # type: ignore
    _HAS_PLOTLY = False


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

_PALETTE = {
    "composer":   "#4E79A7",
    "track":      "#F28E2B",
    "game":       "#E15759",
    "team":       "#76B7B2",
    "soundtrack": "#59A14F",
    "studio":     "#EDC948",
    "platform":   "#B07AA1",
    "driver":     "#FF9DA7",
    "default":    "#BAB0AC",
}

_EDGE_COLOURS = {
    "collaborated_with": "#999999",
    "member_of":         "#59A14F",
    "worked_at":         "#EDC948",
    "influenced_by":     "#E15759",
    "wrote":             "#4E79A7",
    "worked_on":         "#76B7B2",
    "runs_on":           "#B07AA1",
    "default":           "#CCCCCC",
}


def _node_colour(node_type: str) -> str:
    return _PALETTE.get(node_type, _PALETTE["default"])


def _edge_colour(relation: str) -> str:
    return _EDGE_COLOURS.get(relation, _EDGE_COLOURS["default"])


# ---------------------------------------------------------------------------
# GEXF export (always available)
# ---------------------------------------------------------------------------

def _write_gexf(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    path:  Path,
    description: str = "Helix Music Lab graph",
) -> None:
    """
    Write a GEXF 1.3 file compatible with Gephi.
    nodes: list of {id, label, type, ...attrs}
    edges: list of {source, target, relation, weight}
    """
    gexf = ET.Element("gexf", {
        "xmlns":          "http://gexf.net/1.3",
        "xmlns:viz":      "http://gexf.net/1.3/viz",
        "version":        "1.3",
    })
    meta = ET.SubElement(gexf, "meta", {"lastmodifieddate": "2026-01-01"})
    ET.SubElement(meta, "creator").text  = "HelixMusicLab"
    ET.SubElement(meta, "description").text = description

    graph_el = ET.SubElement(gexf, "graph", {
        "defaultedgetype": "directed",
        "mode": "static",
    })

    # Node attributes declaration
    node_attrs = ET.SubElement(graph_el, "attributes", {
        "class": "node", "mode": "static",
    })
    ET.SubElement(node_attrs, "attribute", {"id": "0", "title": "type",  "type": "string"})
    ET.SubElement(node_attrs, "attribute", {"id": "1", "title": "notes", "type": "string"})

    # Edge attributes declaration
    edge_attrs = ET.SubElement(graph_el, "attributes", {
        "class": "edge", "mode": "static",
    })
    ET.SubElement(edge_attrs, "attribute", {"id": "0", "title": "relation", "type": "string"})

    # Nodes
    nodes_el = ET.SubElement(graph_el, "nodes")
    for n in nodes:
        nid  = str(n["id"])
        node_el = ET.SubElement(nodes_el, "node", {"id": nid, "label": str(n.get("label", nid))})
        attvals = ET.SubElement(node_el, "attvalues")
        ET.SubElement(attvals, "attvalue", {"for": "0", "value": str(n.get("type", ""))})
        ET.SubElement(attvals, "attvalue", {"for": "1", "value": str(n.get("notes", ""))})
        # viz colour
        colour = n.get("colour", _node_colour(n.get("type", "")))
        r, g, b = _hex_to_rgb(colour)
        ET.SubElement(node_el, "viz:color", {"r": str(r), "g": str(g), "b": str(b), "a": "1.0"})
        sz = str(n.get("size", 10))
        ET.SubElement(node_el, "viz:size", {"value": sz})

    # Edges
    edges_el = ET.SubElement(graph_el, "edges")
    for i, e in enumerate(edges):
        edge_el = ET.SubElement(edges_el, "edge", {
            "id":     str(i),
            "source": str(e["source"]),
            "target": str(e["target"]),
            "weight": str(e.get("weight", 1.0)),
        })
        attvals = ET.SubElement(edge_el, "attvalues")
        ET.SubElement(attvals, "attvalue", {"for": "0", "value": str(e.get("relation", ""))})

    tree = ET.ElementTree(gexf)
    ET.indent(tree, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(path), encoding="unicode", xml_declaration=True)
    log.info("visualizer: wrote GEXF → %s (%d nodes, %d edges)", path, len(nodes), len(edges))


# ---------------------------------------------------------------------------
# DOT export (always available)
# ---------------------------------------------------------------------------

def _write_dot(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    path:  Path,
    title: str = "helix_graph",
) -> None:
    lines = [f'digraph {json.dumps(title)} {{', '  rankdir=LR;', '  node [shape=box fontname=Helvetica];']
    for n in nodes:
        nid    = str(n["id"]).replace(":", "_").replace("-", "_")
        label  = str(n.get("label", nid)).replace('"', '\\"')
        colour = n.get("colour", _node_colour(n.get("type", "")))
        lines.append(f'  {nid} [label="{label}" style=filled fillcolor="{colour}" fontcolor="white"];')
    for e in edges:
        src    = str(e["source"]).replace(":", "_").replace("-", "_")
        tgt    = str(e["target"]).replace(":", "_").replace("-", "_")
        rel    = str(e.get("relation", ""))
        colour = _edge_colour(rel)
        lines.append(f'  {src} -> {tgt} [label="{rel}" color="{colour}"];')
    lines.append("}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("visualizer: wrote DOT → %s", path)


# ---------------------------------------------------------------------------
# matplotlib PNG export
# ---------------------------------------------------------------------------

def _write_png(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    path:  Path,
    title: str = "",
) -> None:
    if not _HAS_NX or not _HAS_MPL:
        log.debug("visualizer: skipping PNG (networkx=%s, matplotlib=%s)", _HAS_NX, _HAS_MPL)
        return

    G = _nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **{k: v for k, v in n.items() if k != "id"})
    for e in edges:
        G.add_edge(e["source"], e["target"], **{k: v for k, v in e.items()
                                                if k not in ("source", "target")})

    try:
        pos = _nx.spring_layout(G, seed=42, k=2.5)
    except Exception:
        pos = _nx.random_layout(G, seed=42)

    node_ids    = list(G.nodes())
    node_colours = [_node_colour(G.nodes[n].get("type", "")) for n in node_ids]
    node_sizes   = [G.nodes[n].get("size", 10) * 80 for n in node_ids]

    fig, ax = _plt.subplots(figsize=(14, 10))
    _nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=node_ids,
                            node_color=node_colours, node_size=node_sizes, alpha=0.9)
    _nx.draw_networkx_labels(G, pos, ax=ax,
                             labels={n: G.nodes[n].get("label", n.split(":")[-1])
                                     for n in node_ids},
                             font_size=7, font_color="white", font_weight="bold")

    edge_cols = [_edge_colour(G.edges[e].get("relation", "")) for e in G.edges()]
    _nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_cols,
                            arrows=True, arrowsize=12, alpha=0.7, width=1.5)

    if title:
        ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.axis("off")
    _plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    _plt.savefig(str(path), dpi=150, bbox_inches="tight")
    _plt.close(fig)
    log.info("visualizer: wrote PNG → %s", path)


# ---------------------------------------------------------------------------
# Plotly HTML export
# ---------------------------------------------------------------------------

def _write_html(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    path:  Path,
    title: str = "Helix Graph",
) -> None:
    if not _HAS_NX or not _HAS_PLOTLY:
        log.debug("visualizer: skipping HTML (networkx=%s, plotly=%s)", _HAS_NX, _HAS_PLOTLY)
        return

    G = _nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **{k: v for k, v in n.items() if k != "id"})
    for e in edges:
        G.add_edge(e["source"], e["target"], **{k: v for k, v in e.items()
                                                if k not in ("source", "target")})

    try:
        pos = _nx.spring_layout(G, seed=42, k=2.5)
    except Exception:
        pos = _nx.random_layout(G, seed=42)

    # Edge traces
    edge_x, edge_y = [], []
    for src, tgt in G.edges():
        x0, y0 = pos[src]
        x1, y1 = pos[tgt]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = _go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line={"width": 1, "color": "#888"},
        hoverinfo="none",
    )

    # Node trace
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_colours = [_node_colour(G.nodes[n].get("type", "")) for n in G.nodes()]
    node_labels  = [G.nodes[n].get("label", n.split(":")[-1]) for n in G.nodes()]
    node_sizes   = [G.nodes[n].get("size", 10) * 3 for n in G.nodes()]

    node_trace = _go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_labels,
        textposition="top center",
        textfont={"size": 9},
        hoverinfo="text",
        marker={
            "color": node_colours,
            "size": node_sizes,
            "line": {"width": 1, "color": "white"},
        },
    )

    fig = _go.Figure(
        data=[edge_trace, node_trace],
        layout=_go.Layout(
            title={"text": title, "font": {"size": 16}},
            showlegend=False,
            hovermode="closest",
            margin={"b": 20, "l": 5, "r": 5, "t": 40},
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#1a1a2e",
            font={"color": "white"},
        ),
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs="cdn")
    log.info("visualizer: wrote HTML → %s", path)


# ---------------------------------------------------------------------------
# High-level renderers
# ---------------------------------------------------------------------------

def render_collaboration_network(
    graph:   ComposerGraph,
    out_dir: Path,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """
    Composer collaboration + team membership network.
    Nodes: composers + sound teams.
    Edges: collaborated_with, member_of, worked_at.
    """
    formats = formats or ["gexf", "dot", "png"]

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for c in graph.all_composers():
        cid = f"composer:{c.composer_id}"
        track_count = len(graph.tracks_for_composer(c.composer_id))
        nodes.append({
            "id":    cid,
            "label": c.full_name,
            "type":  "composer",
            "size":  max(10, track_count * 5),
            "notes": c.bio_summary or "",
        })

    for tm in graph.all_teams():
        nodes.append({
            "id":    f"team:{tm.team_id}",
            "label": tm.name,
            "type":  "team",
            "size":  15,
        })

    for st in graph.all_studios():
        nodes.append({
            "id":    f"studio:{st.studio_id}",
            "label": st.name,
            "type":  "studio",
            "size":  12,
        })

    collab_relations = {"collaborated_with", "member_of", "worked_at", "influenced_by"}
    for rel in graph.all_relationships():
        if rel.relation in collab_relations:
            edges.append({
                "source":   rel.source,
                "target":   rel.target,
                "relation": rel.relation,
                "weight":   rel.confidence,
            })

    return _write_formats(nodes, edges, out_dir, "collaboration_network", formats,
                          "Composer Collaboration Network")


def render_stylistic_similarity(
    graph:     ComposerGraph,
    vectors:   dict[str, list[float]],
    out_dir:   Path,
    threshold: float = 0.75,
    formats:   list[str] | None = None,
) -> dict[str, Path]:
    """
    Stylistic similarity graph: composer nodes linked by fingerprint cosine similarity.
    Edge weight = cosine similarity between composer centroid vectors.
    """
    formats = formats or ["gexf", "dot", "png"]

    composers = graph.all_composers()
    centroids: dict[str, list[float]] = {}
    for c in composers:
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

    nodes: list[dict[str, Any]] = [
        {
            "id":    f"composer:{c.composer_id}",
            "label": c.full_name,
            "type":  "composer",
            "size":  max(10, len(centroids.get(c.composer_id, [])) // 4),
        }
        for c in composers
        if c.composer_id in centroids
    ]

    edges: list[dict[str, Any]] = []
    comp_ids = list(centroids.keys())
    for i in range(len(comp_ids)):
        for j in range(i + 1, len(comp_ids)):
            a, b  = comp_ids[i], comp_ids[j]
            sim   = _cosine(centroids[a], centroids[b])
            if sim >= threshold:
                edges.append({
                    "source":   f"composer:{a}",
                    "target":   f"composer:{b}",
                    "relation": "similar_to",
                    "weight":   round(sim, 4),
                })

    return _write_formats(nodes, edges, out_dir, "stylistic_similarity", formats,
                          "Stylistic Similarity Graph")


def render_soundtrack_clusters(
    game_id:  str,
    graph:    ComposerGraph,
    vectors:  dict[str, list[float]],
    out_dir:  Path,
    formats:  list[str] | None = None,
) -> dict[str, Path]:
    """
    Track cluster graph for a single soundtrack.
    Track nodes coloured by greedy cosine cluster; composer nodes as hubs.
    """
    formats = formats or ["gexf", "dot", "png"]

    game_tracks = [
        t for t in graph.all_tracks()
        if t.game_id == game_id and t.track_id in vectors
    ]
    if not game_tracks:
        log.warning("visualizer: no tracks with vectors found for game '%s'", game_id)
        return {}

    # Greedy cosine clusters
    tids  = [t.track_id for t in game_tracks]
    vecs  = [vectors[tid] for tid in tids]
    clusters = _greedy_clusters(tids, vecs, threshold=0.78)

    colours = _cluster_colour_map(len(clusters))

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_composers: set[str] = set()

    for ci, cluster in enumerate(clusters):
        colour = colours[ci]
        for tid in cluster:
            track = graph.get_track(tid)
            label = track.title if track and track.title else tid
            nodes.append({
                "id":    f"track:{tid}",
                "label": label,
                "type":  "track",
                "size":  10,
                "colour": colour,
                "notes":  f"cluster_{ci}",
            })
            # Composer → track edges
            for c in graph.composers_for_track(tid):
                cnode_id = f"composer:{c.composer_id}"
                if c.composer_id not in seen_composers:
                    seen_composers.add(c.composer_id)
                    nodes.append({
                        "id":    cnode_id,
                        "label": c.full_name,
                        "type":  "composer",
                        "size":  20,
                    })
                edges.append({
                    "source":   cnode_id,
                    "target":   f"track:{tid}",
                    "relation": "wrote",
                    "weight":   1.0,
                })

    return _write_formats(nodes, edges, out_dir, f"soundtrack_clusters_{game_id}", formats,
                          f"Soundtrack Clusters: {game_id}")


def render_studio_influence_network(
    graph:   ComposerGraph,
    out_dir: Path,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """
    Studio and sound team influence network.
    Nodes: studios, platforms, sound teams, sound drivers, games.
    Edges: works_at, uses_sound_driver, runs_on, developed_by.
    """
    formats = formats or ["gexf", "dot", "png"]
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for st in graph.all_studios():
        nodes.append({"id": f"studio:{st.studio_id}", "label": st.name, "type": "studio", "size": 20})
    for p in graph.all_platforms():
        nodes.append({"id": f"platform:{p.platform_id}", "label": p.name, "type": "platform", "size": 15})
    for d in graph.all_drivers():
        nodes.append({"id": f"driver:{d.driver_id}", "label": d.name, "type": "driver", "size": 12})
    for g in graph.all_games():
        nodes.append({"id": f"game:{g.game_id}", "label": g.title, "type": "game", "size": 18})
    for tm in graph.all_teams():
        nodes.append({"id": f"team:{tm.team_id}", "label": tm.name, "type": "team", "size": 12})
    for c in graph.all_composers():
        nodes.append({"id": f"composer:{c.composer_id}", "label": c.full_name, "type": "composer", "size": 10})

    infra_relations = {
        "runs_on", "uses_sound_driver", "developed_by", "published_by",
        "worked_at", "member_of", "documents", "released_by",
    }
    for rel in graph.all_relationships():
        if rel.relation in infra_relations:
            edges.append({
                "source":   rel.source,
                "target":   rel.target,
                "relation": rel.relation,
                "weight":   rel.confidence,
            })

    return _write_formats(nodes, edges, out_dir, "studio_influence_network", formats,
                          "Studio & Infrastructure Network")


def render_all(
    game_id:  str,
    graph:    ComposerGraph,
    vectors:  dict[str, list[float]],
    out_dir:  Path,
    formats:  list[str] | None = None,
) -> dict[str, dict[str, Path]]:
    """Run all four renderers. Returns dict of renderer_name → {format → path}."""
    formats = formats or ["gexf", "dot", "png"]
    return {
        "collaboration":      render_collaboration_network(graph, out_dir, formats),
        "stylistic":          render_stylistic_similarity(graph, vectors, out_dir, formats=formats),
        "soundtrack_clusters": render_soundtrack_clusters(game_id, graph, vectors, out_dir, formats),
        "studio_influence":   render_studio_influence_network(graph, out_dir, formats),
    }


# ---------------------------------------------------------------------------
# Internal dispatch
# ---------------------------------------------------------------------------

def _write_formats(
    nodes:    list[dict],
    edges:    list[dict],
    out_dir:  Path,
    stem:     str,
    formats:  list[str],
    title:    str,
) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if "gexf" in formats:
        p = out_dir / f"{stem}.gexf"
        _write_gexf(nodes, edges, p, title)
        out["gexf"] = p
    if "dot" in formats:
        p = out_dir / f"{stem}.dot"
        _write_dot(nodes, edges, p, stem)
        out["dot"] = p
    if "png" in formats:
        p = out_dir / f"{stem}.png"
        _write_png(nodes, edges, p, title)
        out["png"] = p
    if "html" in formats:
        p = out_dir / f"{stem}.html"
        _write_html(nodes, edges, p, title)
        out["html"] = p
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot  = sum(x * y for x, y in zip(a, b))
    na   = math.sqrt(sum(x * x for x in a))
    nb   = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na > 1e-10 and nb > 1e-10 else 0.0


def _greedy_clusters(
    ids:       list[str],
    vecs:      list[list[float]],
    threshold: float,
) -> list[list[str]]:
    clusters:  list[list[str]]   = []
    centroids: list[list[float]] = []
    for tid, vec in zip(ids, vecs):
        best_i, best_sim = -1, threshold
        for i, c in enumerate(centroids):
            s = _cosine(c, vec)
            if s > best_sim:
                best_sim, best_i = s, i
        if best_i >= 0:
            clusters[best_i].append(tid)
            cv = [vecs[ids.index(t)] for t in clusters[best_i]]
            dim = len(cv[0])
            centroids[best_i] = [sum(v[k] for v in cv) / len(cv) for k in range(dim)]
        else:
            clusters.append([tid])
            centroids.append(list(vec))
    return clusters


def _cluster_colour_map(n: int) -> list[str]:
    """Return n hex colour strings from a qualitative palette."""
    palette = [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
        "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    ]
    return [palette[i % len(palette)] for i in range(n)]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) != 6:
        return 180, 180, 180
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
