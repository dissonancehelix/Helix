"""
Helix Enforcement — Runtime Checks
==================================
Implements hard gates for Helix runtime behavior and filesystem access.
"""
from __future__ import annotations

import os
import inspect
from pathlib import Path
from typing import Any, Optional

import json
from core.validation.failure_states import FAILURE_STATES, Severity
from core.validation.validators import (
    EnforcementError,
    validate_entity_schema,
    validate_id
)

class NonCanonicalExecutionError(EnforcementError):
    """Raised when a non-canonical (non-HSL-origin) run attempts an authoritative action."""
    pass


def require_canonical_provenance(context: "Any | None", action: str = "Atlas write") -> None:
    """
    Verify that the current run carries valid HSL-origin provenance.

    Called before any authoritative action (Atlas writes, compiler persistence).
    Raises NonCanonicalExecutionError if provenance is absent or non-canonical,
    unless an explicit labs_bypass has been declared.

    Args:
        context:  CommandContext or any object with a .provenance attribute, or None.
        action:   Human-readable name of the action being gated (for error messages).
    """
    from core.hsl.provenance import RunProvenance, EntryMode

    prov: "RunProvenance | None" = getattr(context, "provenance", None)

    if prov is None:
        # No provenance at all — non-canonical by default
        raise NonCanonicalExecutionError(
            f"{action} rejected: no HSL-origin provenance attached to this run. "
            "Use the helix CLI or attach explicit RunProvenance to the context.",
            "MISSING_PROVENANCE",
        )

    if prov.canonical:
        return  # canonical HSL-origin run — authorized

    if prov.labs_bypass and prov.bypass_reason:
        # Explicitly declared non-canonical bypass — allow but note it
        import warnings
        warnings.warn(
            f"[Helix] Non-canonical labs bypass authorized for {action}. "
            f"Reason: {prov.bypass_reason}  run_id={prov.run_id}",
            stacklevel=3,
        )
        return

    raise NonCanonicalExecutionError(
        f"{action} rejected: run is non-canonical (entry_mode={prov.entry_mode.value}). "
        "Authoritative paths require HSL-origin provenance. "
        "For dev/labs work, use RunProvenance.labs_bypass_explicit(reason=...) and set it on the context.",
        "NON_CANONICAL_EXECUTION",
    )


class LayerViolationError(EnforcementError):
    """Raised when an illegal cross-layer interaction is detected."""
    pass

class IllegalWriteError(EnforcementError):
    """Raised when an unauthorized ATLAS write is attempted."""
    pass

# ---------------------------------------------------------------------------
# Path Enforcement
# ---------------------------------------------------------------------------

def authorize_atlas_write(caller_stack_depth: int = 1, context: "Any | None" = None) -> None:
    """
    Ensure the current write to ATLAS is authorized.

    Two-layer check:
    1. RunProvenance — preferred. Canonical HSL-origin flag on the context.
    2. Call-stack path — fallback for legacy paths without context.

    Raises IllegalWriteError or NonCanonicalExecutionError on failure.
    """
    from core.hsl.provenance import RunProvenance

    # Layer 1: provenance-based check (preferred)
    if context is not None:
        require_canonical_provenance(context, action="Atlas write")
        return  # provenance check passed — skip stack check

    # Layer 2: legacy call-stack path check (no context provided)
    stack = inspect.stack()
    index = caller_stack_depth + 1
    if index >= len(stack):
        index = len(stack) - 1

    caller_frame = stack[index]
    caller_path = Path(caller_frame.filename).resolve()

    is_authorized = False
    if "core" in caller_path.parts and "compiler" in caller_path.parts:
        is_authorized = True
    if any(p in caller_path.parts for p in ("tests", "pytest", "unit_tests")):
        is_authorized = True

    if not is_authorized:
        rel_caller = ""
        try:
            rel_caller = os.path.relpath(caller_path, os.getcwd())
        except ValueError:
            rel_caller = caller_path.name

        print(f"[!] ENFORCEMENT BREACH DETECTED: Illegal Atlas write attempt from '{rel_caller}'.")
        raise IllegalWriteError(
            f"Unauthorized Atlas write attempt from '{rel_caller}'. "
            "All writes must be routed through the canonical enforcement gateway.",
            "ILLEGAL_ATLAS_WRITE",
        )

# ---------------------------------------------------------------------------
# Entity Persistence Gate (CANONICAL GATED GATEWAY)
# ---------------------------------------------------------------------------

def enforce_persistence(
    entity: dict[str, Any],
    path: Path,
    is_atlas: bool = True,
    context: "Any | None" = None,
) -> Path:
    """
    The ONLY authorized path for persisting Helix knowledge.
    Ensures authorization, validation, and atomic filesystem commit.

    Args:
        entity:    The entity dict to persist.
        path:      Target filesystem path.
        is_atlas:  True if writing to codex/atlas/ (stricter checks).
        context:   Optional CommandContext carrying RunProvenance.
                   When provided, provenance is checked as Layer 1 (HSL-origin required).
                   When absent, falls back to call-stack path check (legacy).

    Pipeline:
      authorize → validate → clean → atomic_write
    """
    # 1. Authorize — provenance check (Layer 1) or call-stack check (Layer 2)
    authorize_atlas_write(caller_stack_depth=1, context=context)
    
    # 2. Schema / ID validation
    # This also enforces Substrate Capability Vector for atlas entities
    pre_persistence_check(entity, path)
    
    # 3. Path authorization check for atlas target
    if is_atlas and "atlas" not in path.parts:
        # Caller claims it's Atlas, but path is not
        raise IllegalWriteError(f"Target path '{path}' is not in the Atlas.", "ILLEGAL_ATLAS_WRITE")
    
    # 4. Canonical formatting & Clean-up
    # Strip internal compiler/private keys beginning with '_'
    clean_data = {k: v for k, v in entity.items() if not k.startswith("_")}
    
    # 5. Atomic Persistence
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        # Indent=2 is the Helix standard for JSON storage
        content = json.dumps(clean_data, indent=2, ensure_ascii=False)
        temp_path.write_text(content, encoding="utf-8")
        
        # Replace replaces and is atomic on most systems
        if os.name == 'nt' and path.exists():
            # os.replace on Windows may fail if the file is open, 
            # but for this repo it should be fine as it's append-only/locked
            pass
        os.replace(temp_path, path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise EnforcementError(f"Persistence operation failed for {path}: {e}", "UNLOGGED_MUTATION")
    
    return path

# ---------------------------------------------------------------------------
# Entity Pre-persistence Internal Checks
# ---------------------------------------------------------------------------

def pre_persistence_check(entity: dict[str, Any], path: Path) -> None:
    """
    Internal hard-gate check before data hits the filesystem logic.
    Used by enforce_persistence().
    """
    # SKIP schema check for recognized structural files
    if path.name in ("registry.json", "atlas_graph.json", "index.json"):
        return

    # Atlas entities must pass full schema + ID check
    if "atlas" in path.parts:
        # Atlas entities require full Substrate Capability Vector schema
        validate_entity_schema(entity, is_atlas=True)
    elif "codex" in path.parts and "library" in path.parts:
        # Library entities require core schema but not Substrate Capability Vector
        validate_entity_schema(entity, is_atlas=False)
    else:
        # Fallback to base schema validation
        validate_entity_schema(entity, is_atlas=False)

# ---------------------------------------------------------------------------
# Layer Separation Checks
# ---------------------------------------------------------------------------

def enforce_layer_isolation() -> None:
    """
    Audit for layer-skipping imports. (Self-audit probe).
    """
    # Placeholder for dynamic import graph auditing
    # For now, it's just a warning.
    pass
