# INSTRUMENT PATCH PLAN: HIGHEST-LEVERAGE CHANGES
**Objective:** Formalize minimal code patches to enforce the Instrument Contract. Big refactors are rejected in favor of targeted risk mitigation.

## 1. Eliminate Silent Drops in Ingestion (Rust Alignment)
- **Files Touched:** `02_runtime/infra/io.py`, parsing utilities in Workspaces/Forge.
- **Improvement:** Risk Delta (-). Forces deterministic abortion or explicit logged null-nodes rather than silent connectivity loss.
- **Test:** Run against a corrupted dataset; output MUST explicitly log rejection counts instead of skipping implicitly.
- **Rollback:** Disable explicit panic wrappers if it prematurely breaks multi-domain large batch operations.

## 2. Manifest Hashing for Immutability (Git Alignment)
- **Files Touched:** `02_runtime/infra/hashing.py`, `helix.py` execution shim.
- **Improvement:** Determinism Delta (+). Ensures generated artifacts in `06_artifacts/` cannot be retroactively altered or accidentally overwritten without invalidating the manifest.
- **Test:** Attempt to manually edit an artifact file post-run. `helix.py audit` should throw an invalidation error.
- **Rollback:** Remove hashing requirements if I/O overhead exceeds budget limits for very large artifact writes.

## 3. Strict Boundary Schemas for Outputs (Unix Alignment)
- **Files Touched:** `01_protocol/truth_layer/schemas.py`.
- **Improvement:** Risk Delta (-). Prevents `03_forge` researchers from outputting whatever arbitrary dict structures they want. Forces all outcomes to share identical topological reporting schemas.
- **Test:** Have a `03_forge` experiment yield a forbidden key in JSON. Protocol must reject the write entirely.
- **Rollback:** Downgrade to warnings if schema strictness blocks mathematically novel metrics prematurely.

## 4. Import / Write AST Firewall (Nix Alignment)
- **Files Touched:** `01_protocol/validate_rings.py`.
- **Improvement:** Risk Delta (-). Prevents Ring 3 modules from circumventing bounds by importing Ring 0 internals directly or writing arbitrary files outside `06_artifacts/`. 
- **Test:** Null control test introducing `import 00_core.bases` inside the `03_forge` folder. The script must fail pre-flight validation.
- **Rollback:** Remove the AST hook if it creates execution cycle latency or breaks nested dynamic imports legitimately needed by modules.

## 5. Automated Hostility Twin Generation
- **Files Touched:** `02_runtime/orchestration/pyramid.py` (or equivalent execution scheduler).
- **Improvement:** Determinism Delta (+). Forces an Adversarial Twin test generation (e.g. random edge rewiring preserving degree sequence) on every domain dataset ingested automatically.
- **Test:** Verify every generated run in `06_artifacts` automatically contains a counterpart `_twin_baseline.json`.
- **Rollback:** Make it an opt-in CLI flag if compute time for multi-family synthetic runs limits operational cadence.

---

## OPTIONAL ENFORCEMENT SPEC: ROOT QUARANTINE
**Goal:** Prevent accidental schema drift or temporary file accumulation in the Helix root directory without disrupting IDE tools / Windows UX.

**Mechanism (Non-Destructive Git Hook / Workflow Trigger):**
- A lightweight script (`.git/hooks/pre-commit` or a `helix.py verify` step) scans the directory root.
- Any file NOT explicitly listed in the `HELIX.md` Canonical Root Manifesto (e.g. random `test.py`, `.DS_STORE`, `temp_output.json`) is immediately halted from commit.
- Optional Action: Move unapproved files into `06_artifacts/_quarantine/` automatically.
- *Status:* Spec-only. Safe, relies exclusively on Python execution boundaries, no native OS lockdowns needed.

---

## NEXT TESTS (VALIDATION CHECKLIST)
To prove the Instrument Contract is computationally enforced, we must execute the following verifications:
1. [ ] Force a missing metric field during batch execution. Ensure panic/log, not skip.
2. [ ] Manually modify a successfully generated artifact in `06_artifacts`. Verify the system flags it as tainted / hash-mismatch.
3. [ ] Attempt to `import 00_core` from a new mock script in `03_forge/experiments/` and ensure pre-validation blocks it.
4. [ ] Attempt to write an artifact directly to the Project Root instead of `06_artifacts/`. Verify failure.
5. [ ] Pass a standard artifact generation payload without a `run_id` and verify rejection.
6. [ ] Inject 10% capacity noise into a domain and trigger the automated baseline twin generator.
7. [ ] Modify an Enum in `00_core`. Ensure protocol validation fails unless `MANIFEST.md` schema version is bumped simultaneously.
