"""
Graph Builder — Helix Phase 10
================================
Scans Atlas markdown entries and atlas_index.yaml to build the
Atlas Knowledge Graph automatically.

Sources of edges:
  1. atlas_index.yaml explicit links (linked_model, linked_operator, etc.)
  2. "## Linked Experiments" sections in atlas entry markdown
  3. "## Evidence" sections referencing other atlas entries
  4. Shared probe/dataset references across entries
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.kernel.graph.storage.atlas_graph import AtlasGraph, Node, Edge

REPO_ROOT    = Path(__file__).parent.parent.parent
ATLAS_DIR    = REPO_ROOT / "atlas"
INDEX_YAML   = ATLAS_DIR / "atlas_index.yaml"

TYPE_DIR_MAP = {
    "invariants":  ("INVARIANT",  ATLAS_DIR / "invariants"),
    "experiments": ("EXPERIMENT", ATLAS_DIR / "experiments"),
    "models":      ("MODEL",      ATLAS_DIR / "models"),
    "regimes":     ("REGIME",     ATLAS_DIR / "regimes"),
    "operators":   ("OPERATOR",   ATLAS_DIR / "operators"),
}

# Regex to pull atlas entry references from markdown text
ATLAS_REF_RE = re.compile(
    r"codex/atlas/(?:invariants|experiments|models|regimes|operators)/([\w]+)\.md",
    re.IGNORECASE,
)


def _parse_yaml_simple(text: str) -> dict:
    """Minimal YAML parser — avoids PyYAML dependency."""
    result: dict = {}
    current_list: list | None = None
    current_item: dict | None = None

    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent  = len(line) - len(line.lstrip())
        content = line.strip()   # content without any leading/trailing whitespace

        if indent == 0 and content.endswith(":"):
            key = content[:-1]
            result[key] = []
            current_list = result[key]
            current_item = None
        elif indent == 2 and content.startswith("- id:"):
            current_item = {"id": content.split(":", 1)[1].strip()}
            if current_list is not None:
                current_list.append(current_item)
        elif indent >= 4 and current_item is not None and ":" in content:
            k, _, v = content.partition(":")
            current_item[k.strip()] = v.strip()

    return result


def _parse_entry_sections(md_text: str) -> dict[str, str]:
    """Extract section bodies from a Phase 8 atlas markdown file."""
    sections: dict[str, str] = {}
    section_re = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    parts = section_re.split(md_text)
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i].strip().lower().replace(" ", "_")
        body    = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections[heading] = body
    # Extract bold metadata fields
    for m in re.finditer(r"\*\*(.+?)\*\*[:\s]+(.+)", md_text):
        key = m.group(1).strip().lower().replace(" ", "_").rstrip(":")
        sections[key] = m.group(2).strip()
    return sections


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", s.lower()).strip("_")


def _extract_atlas_refs(text: str) -> list[str]:
    """Find all atlas entry IDs referenced in a block of text."""
    return ATLAS_REF_RE.findall(text)


def build_graph() -> AtlasGraph:
    """
    Build the complete Atlas Knowledge Graph from current atlas state.
    Returns a populated AtlasGraph.
    """
    g = AtlasGraph()

    # ── 1. Load registry ─────────────────────────────────────────────────────
    registry: dict = {}
    if INDEX_YAML.exists():
        registry = _parse_yaml_simple(INDEX_YAML.read_text())

    # ── 2. Create nodes from all atlas entries ────────────────────────────────
    for section_key, (node_type, directory) in TYPE_DIR_MAP.items():
        if not directory.exists():
            continue
        registry_entries = {
            e.get("id", ""): e
            for e in (registry.get(section_key) or [])
            if isinstance(e, dict)
        }
        for md_path in sorted(directory.glob("*.md")):
            slug   = md_path.stem
            reg    = registry_entries.get(slug, {})
            status = reg.get("status", "unknown")

            # Parse domain info
            domains_raw = reg.get("domains", "")
            if isinstance(domains_raw, str):
                # "[games, language]" or "games, language"
                domains = [d.strip().strip("[]'\"") for d in domains_raw.split(",") if d.strip()]
            else:
                domains = list(domains_raw) if domains_raw else []

            g.add_node(Node(
                id=slug,
                type=node_type,
                status=status,
                domains=domains,
                path=str(md_path.relative_to(REPO_ROOT)),
                metadata={k: v for k, v in reg.items() if k not in ("id", "type", "status", "domains", "path")},
            ))

    node_ids = {n.id for n in g.nodes}

    # ── 3. Build edges from registry explicit links ───────────────────────────
    for inv_entry in (registry.get("invariants") or []):
        if not isinstance(inv_entry, dict):
            continue
        inv_id = inv_entry.get("id", "")
        if not inv_id or inv_id not in node_ids:
            continue

        # linked_model -> DERIVES_FROM (model derives from invariant)
        model_id = inv_entry.get("linked_model", "").strip()
        if model_id and model_id != "null" and model_id in node_ids:
            try:
                g.add_edge(Edge(source=model_id, target=inv_id, type="DERIVES_FROM"))
            except (ValueError, KeyError):
                pass

        # linked_operator -> IMPLEMENTS (operator implements invariant)
        op_id = inv_entry.get("linked_operator", "").strip()
        if op_id and op_id != "null" and op_id in node_ids:
            try:
                g.add_edge(Edge(source=op_id, target=inv_id, type="IMPLEMENTS"))
            except (ValueError, KeyError):
                pass

    for exp_entry in (registry.get("experiments") or []):
        if not isinstance(exp_entry, dict):
            continue
        exp_id = exp_entry.get("id", "")
        if not exp_id or exp_id not in node_ids:
            continue
        inv_id = exp_entry.get("linked_invariant", "").strip()
        if inv_id and inv_id != "null" and inv_id in node_ids:
            outcome = exp_entry.get("outcome", "").strip().lower()
            edge_type = "SUPPORTED_BY" if outcome == "pass" else "TESTED_BY"
            try:
                g.add_edge(Edge(source=inv_id, target=exp_id, type=edge_type))
            except (ValueError, KeyError):
                pass

    for model_entry in (registry.get("models") or []):
        if not isinstance(model_entry, dict):
            continue
        model_id = model_entry.get("id", "")
        if not model_id or model_id not in node_ids:
            continue
        explains = model_entry.get("explains", "").strip()
        if explains and explains != "null" and explains in node_ids:
            try:
                g.add_edge(Edge(source=model_id, target=explains, type="DERIVES_FROM"))
            except (ValueError, KeyError):
                pass

    for op_entry in (registry.get("operators") or []):
        if not isinstance(op_entry, dict):
            continue
        op_id = op_entry.get("id", "")
        if not op_id or op_id not in node_ids:
            continue
        used_in_raw = op_entry.get("used_in", "[]")
        # Parse "[exp1, exp2]"
        used_in = [s.strip().strip("[]'\"") for s in used_in_raw.split(",") if s.strip()]
        for exp_id in used_in:
            exp_id = exp_id.strip().strip("[]").strip("'\"")
            if exp_id in node_ids:
                try:
                    g.add_edge(Edge(source=op_id, target=exp_id, type="IMPLEMENTS"))
                except (ValueError, KeyError):
                    pass

    # ── 4. Build edges from markdown section text ─────────────────────────────
    for node in g.nodes:
        if not node.path:
            continue
        md_path = REPO_ROOT / node.path
        if not md_path.exists():
            continue
        try:
            text     = md_path.read_text()
            sections = _parse_entry_sections(text)
        except OSError:
            continue

        # Linked Experiments section
        linked_text = sections.get("linked_experiments", "")
        for ref_id in _extract_atlas_refs(linked_text):
            if ref_id in node_ids and ref_id != node.id:
                try:
                    # Invariant -> Experiment: TESTED_BY; others: generic SUPPORTED_BY
                    if node.type == "INVARIANT":
                        g.add_edge(Edge(source=node.id, target=ref_id, type="TESTED_BY"))
                    elif node.type == "MODEL":
                        g.add_edge(Edge(source=node.id, target=ref_id, type="DERIVES_FROM"))
                    else:
                        g.add_edge(Edge(source=node.id, target=ref_id, type="SUPPORTED_BY"))
                except (ValueError, KeyError):
                    pass

        # Evidence section
        evidence_text = sections.get("evidence", "")
        for ref_id in _extract_atlas_refs(evidence_text):
            if ref_id in node_ids and ref_id != node.id:
                try:
                    g.add_edge(Edge(source=node.id, target=ref_id, type="SUPPORTED_BY"))
                except (ValueError, KeyError):
                    pass

    # ── 5. Shared-probe cluster edges (same probe file -> EMERGES_FROM) ───────
    probe_users: dict[str, list[str]] = {}
    for node in g.nodes:
        if not node.path:
            continue
        md_path = REPO_ROOT / node.path
        if not md_path.exists():
            continue
        try:
            text = md_path.read_text()
        except OSError:
            continue
        for probe_match in re.finditer(r"labs/invariants/(\w+_probe)\.py", text):
            probe_name = probe_match.group(1)
            probe_users.setdefault(probe_name, []).append(node.id)

    for probe_name, users in probe_users.items():
        if len(users) < 2:
            continue
        # Nodes sharing a probe are loosely linked via EMERGES_FROM
        for i in range(len(users)):
            for j in range(i + 1, len(users)):
                a, b = users[i], users[j]
                try:
                    g.add_edge(Edge(source=a, target=b, type="EMERGES_FROM",
                                    weight=0.5, notes=f"shared probe: {probe_name}"))
                except (ValueError, KeyError):
                    pass

    return g
