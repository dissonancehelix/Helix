Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Kernel Deprecation History

This document records the lineage of Helix kernel objects: what each kernel claimed, why it was deprecated, and what survived into the next generation.

---

## kernel-000 → DEPRECATED

**Claim:** In far-from-equilibrium systems, structural persistence requires maintenance capacity M to exceed perturbation amplitude δ (M > δ).

**Survived as:** Class B (THROUGHPUT) in kernel-001 and kernel-002. The M > δ condition is correct for actively maintained systems.

**Deprecated because:** M > δ fails as a universal necessary condition. Three independent countermodel classes break it:

| Countermodel class | System | Why it breaks M > δ |
|---|---|---|
| BARRIER | Diamond (sp³ lattice) | M ≈ 0 active throughput; persists via kinetic barrier E_a ≈ 7 eV >> kT ≈ 0.025 eV |
| CRITICAL | SOC sandpile (Bak et al.) | Maximum structural complexity at M ≈ δ (the critical manifold), not M >> δ |
| STOCHASTIC RESONANCE | Noise-enhanced detection | δ > M can be constructive; structure peaks at optimal δ |

**Decay chain:** `["kernel-000", "kernel-001"]`

---

## kernel-001 → DEPRECATED

**Claim:** Structural persistence in far-from-equilibrium systems is explained by at least one of three independent sufficient conditions: (A) BARRIER E_a/δ >> 1; (B) THROUGHPUT M/δ > 1; (C) CRITICAL — proximity to critical manifold with divergent ξ or χ.

**Survived as:** Classes A, B, C in kernel-002. All three survive intact. No class from kernel-001 is retracted.

**Deprecated because — Phase 1–4 adversarial audit findings (see `docs/kernel-002_audit.md`):**

### Incompleteness (Phase 1 + Phase 4)

Two synthetic systems break all three classes simultaneously:

1. **Topologically protected dissipative soliton:** E_a/δ ≈ 1 (no dominant barrier), M/δ < 1 (no throughput dominance), ξ/χ finite (not critical). Persists via integer winding number Q — a discrete topological invariant. This is Class D (TOPOLOGICAL), absent from kernel-001.

2. **Noise-induced order (Horsthemke-Lefever type):** M and δ are not independently operationalizable (same physical process). φ(σ=0) = 0 (no structure without noise). M/δ ≡ 1 by construction — Class B is undefined. This is Class E (NOISE_CONSTRUCTIVE), absent from kernel-001.

Three additional gaps not covered by A/B/C:
- Neutral persistence (evolutionary neutral networks)
- Pattern persistence (intermediate-disturbance diversity)
- Edge-of-stability dynamics (DNN training traversal)

### Taxonomy only (Phase 3)

Kernel-001 generates no novel predictions not derivable from standard TST, ISS, or RG theory individually. A generative kernel must add: (1) transition rules between classes, (2) HYBRID composition rules, (3) class-specific predictions that cross the boundaries of constituent theories.

### Reduction non-result (Phase 2)

No single framework (basin geometry, Lyapunov, FEP, control theory) subsumes all three classes without failure for at least one. Class C (CRITICAL) is mechanistically non-equivalent to Lyapunov stability (trajectory vs. distribution), to FEP (FEP scope is narrower than FFNEQ systems), and to control-theoretic marginal stability (linear vs. nonlinear RG scaling). This confirms A/B/C are genuinely distinct but proves they are mechanistically irreducible to each other — not that they are exhaustive.

**What kernel-001 got right:**
- Mechanistic non-equivalence of A/B/C is confirmed (Phase 2)
- The trichotomy correctly partitions the FFNEQ stability space it covers
- All three break tests in kernel-001 (diamond, SOC, stochastic resonance) are valid evidence

**Decay chain:** `["kernel-000", "kernel-001", "kernel-002"]`

---

## kernel-002 → CAPTURE (current)

**Claim:** Five independent sufficient conditions (A–E) plus explicit UNCLASSIFIED buckets with test plans. Minimal generative interface: Mechanism Interface Template, HYBRID composition rules, three falsifiable predictions (P1: topological threshold-gating, P2: noise-constructive non-monotonicity, P3: HYBRID(B↔C) warning-signal suppression).

**Status:** CAPTURE — pending stress testing. Not yet STRESS_TESTED.

**Known gaps remaining:**
- Neutral persistence (Class F candidate — test plan in KERNEL.md §3.1)
- Pattern persistence (requires separate PATTERN kernel)
- P3 full test harness not yet implemented
- No domain examples of Class D or Class E have been fully stress-tested against break tests from outside their own definitions

**Next expected deprecation trigger:** Any far-from-equilibrium system with structural persistence that (a) fails all five conditions and (b) does not fall into any UNCLASSIFIED bucket.

**Decay chain:** `["kernel-000", "kernel-001", "kernel-002"]`
