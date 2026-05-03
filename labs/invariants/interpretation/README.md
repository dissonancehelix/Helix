# labs/invariants/interpretation/

Research working notes from a prior formal math research session (EIP/DCP theorem development). These are **not pipeline code** — they are the research artifact trail.

**Do not modify the pipeline based solely on these files.** Current pipeline truth lives in `labs/invariants/pipeline.py`, `labs/invariants/e2e.py`, and `labs/invariants/README.md`.

---

## File Categories

### Foundational / Theory
Core structural definitions and axioms. Load-bearing for understanding the theoretical basis.

| File | Contents |
|------|----------|
| `axioms.md` | Foundational axioms of the formal system |
| `basis_declaration.md` | Basis vector declarations |
| `composition.md` | Composition rules for structural operators |
| `kernels.md` | Kernel definitions |
| `kernels_interaction.md` | Kernel interaction rules |
| `kernels_interaction_blind.md` | Blind interaction variant |
| `kernel_history.md` | Kernel evolution trace |
| `irreversibility.md` | Irreversibility formal treatment |
| `universality.md` | Universality claims |
| `symmetry.md` | Symmetry analysis |
| `locality.md` | Locality constraints |
| `necessity.md` | Necessity conditions |
| `observability.md` | Observability requirements |
| `philosophy.md` | Philosophical framing of the formal system |

### Architecture / History
System design decisions and evolution.

| File | Contents |
|------|----------|
| `architecture.md` | Phase 6 architectural stabilization |
| `history.md` | Research session history |
| `kernel_history.md` | Kernel design evolution |
| `wsl2.md` | WSL2 substrate notes |
| `amendments_dual_track_evolution.md` | Dual-track evolution amendments |
| `amendment_micro_kernel_workspace.md` | Micro-kernel workspace amendment |

### Falsifiers
Active falsification criteria and test results. These feed directly into DCP/EIP promotion decisions.

| File | Contents |
|------|----------|
| `falsifiers.md` | Master falsifier list |
| `falsifiers_suite.md` | Organized falsifier suite |
| `eip_falsifiers.md` | EIP-specific falsifiers |
| `expression_falsifiers.md` | Expression-layer falsifiers |
| `expression_kernel_falsifiers.md` | Expression kernel falsifiers |
| `expression_pack_falsifiers.md` | Expression pack falsifiers |
| `external_pack_v1_falsifiers.md` | External pack v1 falsifiers |
| `k2_falsifiers_update.md` | K2 falsifier updates |
| `kernel2_falsifiers.md` | Kernel2 falsifiers |
| `meta_kernel_falsifiers.md` | Meta-kernel falsifiers |
| `sf_falsifiers.md` | SF falsifiers |
| `triad_falsifiers.md` | Triad falsifiers |
| `tsm_falsifiers.md` | TSM falsifiers |
| `counterexample_falsifiers.md` | Counterexample-based falsifiers |
| `failure_modes.md` | Documented failure modes |

### Phase Analysis (numbered)
Sequential experiment phases with locked predictions and results.

| File | Contents |
|------|----------|
| `phase1a_structural_gaps.md` | Phase 1a: structural gap analysis |
| `phase2b_obstruction_*.md` | Phase 2b: obstruction analysis (3 files) |
| `phase3[a-e]_*.md` | Phase 3: obstruction geometry through minimal basis (5 files) |
| `phase4_*.md` / `phase4b_*.md` | Phase 4: reduction and stress tests |
| `phase9_*.md` | Phase 9: isotopic rotations + substrate tagging |
| `phase12b_*.md` + lock hash | Phase 12b: predictions locked |
| `phase15_eip_t1_verdict.md` | Phase 15: EIP T1 verdict |
| `phase20_hybrid_failure_analysis.md` | Phase 20: hybrid failure analysis |
| `phase22_domain_additions.md` | Phase 22: domain additions |
| `phase23_*.md` | Phase 23: bootstrap + confusion matrices |
| `phase25_*.md` | Phase 25: adversarial rotation, entropy vs yield, substrate reconstruction |
| `phase26_*.md` | Phase 26: holdout generalization + reconstruction |
| `phase27_beam_selection.md` | Phase 27: beam selection |

### Phase Analysis (lettered — post-numbered)
| File | Contents |
|------|----------|
| `phaseA_*.md` | Phase A: beam ablation, loadings, confusion geometry, minimal features |
| `phaseB_*.md` + lock hash | Phase B: adversarial suite, corruption robustness, false friends, gate flips, merge tests |
| `phaseC_*.md` | Phase C: beams v2 SVD, bootstrap stability, new domains index |
| `phaseD*.md` | Phase D: baselines, threshold projection, coverage, location targets, obstruction prediction, sensitivity |
| `phase_2_substrate.md` / `phase_3_runtime.md` / `phase_4_probes.md` | Alternate phase numbering |
| `phase_gates.md` | Phase gate definitions |

### Beams / Algebra
Beam and algebraic structure analysis.

| File | Contents |
|------|----------|
| `beams_v1_algebra.md` | Beam v1 algebraic structure |
| `beams_v1_confusion_cells.md` | Beam confusion cell analysis |
| `comp_expr.md` | Composite expression structure |

### Metrics / Embedding
| File | Contents |
|------|----------|
| `substrate_axis.md` | Substrate axis definitions |
| `entropy_surface.md` | Entropy surface analysis |
| `structural_fingerprint.md` | Structural fingerprint methodology |
| `measurement_layer_M1.md` | M1 measurement layer |
| `mlayer_*.md` | M-layer coverage, hybrid, invariance, obstructions (4 files) |
| `baselines_phase12b.md` | Phase 12b baselines |
| `falsifiers_psc_embedding.md` / `falsifiers_psc_tabular.md` | PSC embedding/tabular falsifiers |
| `psc_claims.md` / `psc_suite_overview.md` | PSC claims and suite |
| `rank.md` | Rank analysis |

### Domain Applications (Ops)
DCP/EIP applied to specific external domains. Exploratory probes.

| File | Contents |
|------|----------|
| `adaptive_immunity_ops.md` | Adaptive immune system as DCP domain |
| `constitutional_law_ops.md` | Constitutional law as DCP domain |
| `language_grammar_ops.md` | Language grammar as DCP domain |
| `llm_structural_mapping.md` / `llm_runaway_thresholds.md` | LLM structural DCP mapping |
| `lotka_volterra_ops.md` | Lotka-Volterra ecosystem |
| `nakamoto_consensus_ops.md` | Nakamoto consensus |
| `protein_folding_ops.md` | Protein folding |
| `quantum_error_correction_ops.md` | Quantum error correction |
| `supply_chain_ops.md` | Supply chain |
| `tokamak_plasma_ops.md` | Tokamak plasma |
| `traffic_shockwaves_ops.md` / `traffic_shockwaves_graph.md` | Traffic shockwaves |
| `wikimedia_integration.md` | Wikimedia integration probe |

### Other
| File | Contents |
|------|----------|
| `compatibility_limit_validation.md` / `compatibility_risk.md` | Compatibility analysis |
| `convergence_attack_verdict.md` | Convergence attack verdict |
| `eip_experiment_notes.md` | EIP experiment notes |
| `gate_comparison.md` | Gate comparison analysis |
| `grant_theorems.md` | Grant theorems |
| `k2_generator_bias.md` / `k2_minimality.md` | K2 generator bias + minimality |
| `longitudinal_beam_drift.md` | Longitudinal beam drift |
| `manifold_atlas.md` | Manifold atlas |
| `meta_kernel_lab.md` | Meta-kernel lab notes |
| `numeric_domain_index.md` | Numeric domain index |
| `obstruction_entropy.md` / `obstruction_spectrum.md` | Obstruction entropy/spectrum |
| `operator_grounding.md` | Operator grounding |
| `phase12b_lock_hash.txt` / `phaseB_lock_hash.txt` | Locked prediction hashes |
| `predictions.md` | Prediction registry |
| `representation_invariance_suite.md` | Representation invariance suite |
| `simulation_stack.md` | Simulation stack |
| `stabilization_feasibility_overlay.md` | Stabilization feasibility |
| `verdict.md` | Research verdict summary |

