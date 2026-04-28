# Helix Enforcement: System Law

This directory contains the central enforcement authority for the Helix repository. It transforms the architectural philosophy of the system into explicit, machine-enforced runtime guarantees.

## Authoritative Laws

Helix is a governed system. All operations must comply with these laws or fail immediately.

### 1. Layer Separation Laws
- **Immutable Codex**: The `core` may not depend on the `codex/atlas` as a mutable source.
- **Unauthorized Writes**: `applications` may not write to the `atlas/` directly. 
- **Compiler Authority**: All persistent state changes to the Atlas must flow through the central compiler (`system/engine/store/compiler/atlas_compiler.py`).

### 2. Identity Laws
- **Deterministic Existence**: All persisted knowledge objects must possess a deterministic, unique ID.
- **Canonical Format**: IDs MUST follow the `domain.type:slug` pattern (lowercase, underscores, and digits only).
- **ID Integrity**: Missing or malformed IDs are treated as critical system failures.

### 3. Schema Laws
- **Full Validation**: Every entity written to the Atlas or Library must pass structural and semantic validation against the canonical schema specified in `docs/ENTITY_SCHEMA.md`.
- **Mandatory Provenance**: Entities must include `entity_id`, `entity_type`, `created_at`, and `source`.
- **Cognitive Embedding**: Atlas entities must includes a 6-axis Substrate Capability Vector (SCV) embedding.

### 4. Relationship Laws
- **Explicit Linkage**: Implicit relationships are forbidden. All graph links must be explicitly declared in the entity schema.
- **Link Validity**: A link is only valid if the target ID is canonical.

### 5. Mutation Laws
- **Observability**: Hidden mutations are illegal. Every architectural transformation must be logged in metadata.
- **Pre-Commit Gate**: No entity may be committed to persistence without passing the `pre_persistence_check`.

## Canonical Persistence Gateway

Helix enforces a single canonical entry point for all persistent data. No module is permitted to write directly to JSON storage using raw filesystem calls.

### The `enforce_persistence` Protocol
The `enforce_persistence(data, path)` function serves as the system's hard gate:
1.  **Authorize**: Verifies the call-stack origin (Only `core/compiler/` or `tests/` are authorized).
2.  **Audit**: Checks the target path against the claimed layer (e.g., Atlas vs Library).
3.  **Validate**: Runs full schema, ID, and relationship validation.
4.  **Log**: Ensures mutation metadata is present.
5.  **Commit**: Performs an atomic filesystem swap to prevent data corruption.

## Shadow Audit Layer

The system includes a shadow audit layer to detect drift in already-persisted states.

### `audit_system_state(root_path)`
This function scans the Codex (`codex/atlas` and `codex/library`) for:
-   **Invalid IDs**: Non-canonical identifiers.
-   **Schema Drift**: Entities missing required core or Substrate Capability Vector fields.
-   **Misplacement**: Artifacts located in the wrong substrate or plural directory.
-   **Corruption**: Malformed JSON or unparseable entities.

Run the audit periodically to ensure the repository remains in a valid architectural state.

## Failure Response

Enforcement violations are treated as critical system breaches.
-   **Runtime**: Unauthorized write attempts raise `IllegalWriteError` and print a `[!] ENFORCEMENT BREACH` alert to stdout.
-   **Validation**: Failed entities raise `ValidationError`.
-   **Persistence**: Corruption or atomic swap failures raise `EnforcementError`.

