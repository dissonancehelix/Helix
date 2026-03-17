"""
Graph Visualizer — Helix Phase 10
===================================
Exports the Atlas Knowledge Graph to Graphviz DOT format.
Output: atlas/atlas_graph.dot

Render with:
  dot -Tpng atlas/atlas_graph.dot -o atlas/atlas_graph.png
  dot -Tsvg atlas/atlas_graph.dot -o atlas/atlas_graph.svg
"""

from __future__ import annotations

from pathlib import Path
from core.kernel.graph.storage.atlas_graph import AtlasGraph

ATLAS_DIR    = Path(__file__).parent.parent.parent / "atlas"
DOT_OUTPUT   = ATLAS_DIR / "atlas_graph.dot"

# Visual style per node type
NODE_STYLES: dict[str, dict] = {
    "INVARIANT":  {"shape": "ellipse",  "color": "#2E86AB", "fontcolor": "white",  "style": "filled"},
    "EXPERIMENT": {"shape": "box",      "color": "#A23B72", "fontcolor": "white",  "style": "filled"},
    "MODEL":      {"shape": "diamond",  "color": "#F18F01", "fontcolor": "white",  "style": "filled"},
    "REGIME":     {"shape": "hexagon",  "color": "#C73E1D", "fontcolor": "white",  "style": "filled"},
    "OPERATOR":   {"shape": "pentagon", "color": "#3B1F2B", "fontcolor": "white",  "style": "filled"},
}

# Edge style per edge type
EDGE_STYLES: dict[str, dict] = {
    "SUPPORTED_BY":   {"color": "#2E86AB", "style": "solid",  "arrowhead": "normal"},
    "TESTED_BY":      {"color": "#A23B72", "style": "dashed", "arrowhead": "open"},
    "DERIVES_FROM":   {"color": "#F18F01", "style": "solid",  "arrowhead": "vee"},
    "IMPLEMENTS":     {"color": "#3B1F2B", "style": "dotted", "arrowhead": "box"},
    "EMERGES_FROM":   {"color": "#888888", "style": "dashed", "arrowhead": "dot"},
    "CONTRADICTS":    {"color": "#C73E1D", "style": "bold",   "arrowhead": "tee"},
    "TRANSITIONS_TO": {"color": "#666666", "style": "solid",  "arrowhead": "normal"},
    "PRODUCES":       {"color": "#999999", "style": "dotted", "arrowhead": "open"},
}


def _attr_str(attrs: dict) -> str:
    parts = [f'{k}="{v}"' for k, v in attrs.items()]
    return "[" + ", ".join(parts) + "]"


def to_dot(graph: AtlasGraph) -> str:
    lines = [
        "digraph HelixAtlas {",
        "  rankdir=LR;",
        "  node [fontname=Helvetica fontsize=11];",
        "  edge [fontname=Helvetica fontsize=9];",
        "",
        "  // Legend",
        "  subgraph cluster_legend {",
        "    label='Node Types'; style=filled; color=lightgrey;",
        "    INVARIANT  [shape=ellipse  style=filled color="#2E86AB" fontcolor=white];",
        "    EXPERIMENT [shape=box      style=filled color="#A23B72" fontcolor=white];",
        "    MODEL      [shape=diamond  style=filled color="#F18F01" fontcolor=white];",
        "    REGIME     [shape=hexagon  style=filled color="#C73E1D" fontcolor=white];",
        "    OPERATOR   [shape=pentagon style=filled color="#3B1F2B" fontcolor=white];",
        "  }",
        "",
        "  // Nodes",
    ]

    for n in sorted(graph.nodes, key=lambda x: x.id):
        style = NODE_STYLES.get(n.type, {})
        label = n.id.replace("_", "\\n")
        attrs = {
            "label":     label,
            "tooltip":   f"{n.type}: {n.status}",
            **style,
        }
        lines.append(f"  {n.id} {_attr_str(attrs)};")

    lines.append("")
    lines.append("  // Edges")

    for e in sorted(graph.edges, key=lambda x: (x.source, x.target, x.type)):
        style = EDGE_STYLES.get(e.type, {})
        attrs = {
            "label":   e.type,
            "tooltip": e.notes or e.type,
            **style,
        }
        if e.weight != 1.0:
            attrs["penwidth"] = str(round(e.weight * 2, 1))
        lines.append(f"  {e.source} -> {e.target} {_attr_str(attrs)};")

    lines.append("}")
    return "\n".join(lines)


def export_dot(graph: AtlasGraph, path: Path = DOT_OUTPUT) -> Path:
    """Write DOT file and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    dot = to_dot(graph)
    path.write_text(dot)
    return path
