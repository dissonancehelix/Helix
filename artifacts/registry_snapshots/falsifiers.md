# Helix — Falsifiers

The stabilization archetypes mapped to the Helix repository are falsifiable through the following concrete signatures.

## 1. SEED_42_DETERMINISM (ARCH_DETERMINISTIC_Harness)
- **Falsification Signature:** Use of `random.*` or `np.random.*` in any `engine/*.py` file BEFORE or WITHOUT calling `modules.init_random(seed)`.
- **Counterexample Test:** If a run produces non-bit-exact identical results across consecutive executions of the same engine, the determinism claim is falsified for that component.

## 2. SHA_256_INTEGRITY_WRAP (ARCH_INTEGRITY_Lock)
- **Falsification Signature:** Any direct call to `json.dump()` or `open().write()` in an engine script that bypasses the `save_wrapped` function.
- **Counterexample Test:** If an artifact exists in `artifacts/` without a valid `artifact_hash` field in its wrapper JSON, the integrity lock claim is falsified.

## 3. DOC_TRACE_ENFORCEMENT (ARCH_SYMBOLIC_Consistency)
- **Falsification Signature:** A numeric string in `/docs/*.md` (formatted `\b\d+\.\d+\b`) that is NOT present in any referenced `/artifacts/*.json` file.
- **Counterexample Test:** If `helix.py run` (specifically `enforce_doc_traces`) completes successfully while such a "hallucinated" or "drifted" number is present in documentation, the C4/Symbolic Depth claim is falsified.

## 4. DATASET_HASH_ENCLOSURE (ARCH_INTEGRITY_Lock)
- **Falsification Signature:** Successfully running `helix.py run` where an underlying `.json` database file in `/data/domains` has been modified but its hash remains unchanged.
- **Counterexample Test:** If a dataset change does not trigger an archive event or a hash rotation in `run_manifest.json`, the closure claim is falsified.

---
© 2026 Helix Project
