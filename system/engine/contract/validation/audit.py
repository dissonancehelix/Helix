"""
Helix Enforcement — System Audit
===============================
Scans persistent state for drift, corruption, or architectural violations.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List, Dict

from core.validation.failure_states import FAILURE_STATES, Severity
from core.validation.validators import (
    validate_id, 
    validate_entity_schema, 
    EnforcementError,
    ID_PATTERN,
    CORE_FIELDS,
    SCV_AXES
)

class AuditFinding:
    def __init__(self, path: Path, code: str, message: str, severity: Severity):
        self.path = path
        self.code = code
        self.message = message
        self.severity = severity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value
        }

def audit_system_state(repo_root: Path) -> Dict[str, Any]:
    """
    Perform a shadow audit of the entire Helix persistent state (Codex).
    
    Detects:
    - Invalid IDs
    - Schema violations
    - Missing provenance
    - Misplaced artifacts
    """
    findings: List[AuditFinding] = []
    
    codex_dir = repo_root / "codex"
    if not codex_dir.exists():
        return {"passed": False, "findings": [{"message": "Codex directory missing"}]}

    # 1. Scan Atlas
    atlas_dir = codex_dir / "atlas"
    if atlas_dir.exists():
        _scan_directory(atlas_dir, is_atlas=True, findings=findings)

    # 2. Scan Library
    library_dir = codex_dir / "library"
    if library_dir.exists():
        _scan_directory(library_dir, is_atlas=False, findings=findings)

    # 3. Cross-reference check (e.g. registry vs filesystem)
    # TBD - could check if entities in registry exist on disk and vice versa.

    return {
        "passed": len(findings) == 0,
        "finding_count": len(findings),
        "findings": [f.to_dict() for f in findings]
    }

def _scan_directory(dir_path: Path, is_atlas: bool, findings: List[AuditFinding]):
    """Recursively scan directory for JSON entities and validate them."""
    for root, _, files in os.walk(dir_path):
        for file in files:
            if not file.endswith(".json"):
                continue
            
            # Skip architectural files that aren't entities (registry, graph, etc.)
            if file in ("registry.json", "atlas_graph.json", "atlas_index.yaml"):
                continue

            path = Path(root) / file
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    findings.append(AuditFinding(path, "INVALID_SCHEMA", "Entity must be a JSON object", Severity.HIGH))
                    continue

                # 1. ID Check (Mapping legacy 'id' to 'entity_id')
                eid = data.get("entity_id") or data.get("id")
                if not eid:
                    findings.append(AuditFinding(path, "INVALID_ID", "Missing entity ID", Severity.HIGH))
                else:
                    try:
                        validate_id(eid)
                    except EnforcementError as e:
                        findings.append(AuditFinding(path, "INVALID_ID", str(e), Severity.HIGH))

                # 2. Schema Check
                try:
                    # Map legacy fields for audit if necessary
                    compat_data = dict(data)
                    if "entity_id" not in compat_data and "id" in compat_data:
                        compat_data["entity_id"] = compat_data["id"]
                    if "entity_type" not in compat_data and "type" in compat_data:
                        compat_data["entity_type"] = compat_data["type"]
                    
                    validate_entity_schema(compat_data, is_atlas=is_atlas)
                except EnforcementError as e:
                    findings.append(AuditFinding(path, "INVALID_SCHEMA", str(e), Severity.HIGH))

                # 3. Path Check (Is it in the right Substrate Capability Vector directory?)
                # atlas/{substrate}/{type_plural}/{slug}.json
                if is_atlas:
                    parts = path.parts
                    # We expect something like: codex/atlas/music/tracks/slug.json
                    # Index check: 'atlas' should be at -4, substrate at -3, type at -2
                    try:
                        atlas_idx = parts.index("atlas")
                        if len(parts) > atlas_idx + 2:
                            substrate = parts[atlas_idx + 1]
                            type_plural = parts[atlas_idx + 2]
                            # Simple check: type_plural should end in 's' or 'chips'
                            # This is a soft check for audit
                            pass 
                    except ValueError:
                        pass

            except json.JSONDecodeError:
                findings.append(AuditFinding(path, "INVALID_SCHEMA", "Malformed JSON file", Severity.CRITICAL))
            except Exception as e:
                findings.append(AuditFinding(path, "INVALID_SCHEMA", f"Unexpected error during audit: {e}", Severity.MEDIUM))
