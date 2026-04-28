# Changelog
## Inhabited Interiority Research Program

---

## [0.3.0] — 2026-04-26

### Major restructure: research program harness

- Restructured module from theory document + code to full single-person research harness
- Added PROJECT_CONSTITUTION.md (12 governing principles)
- Added RESEARCH_PROGRAM.md (central questions, research modes, publication plan)
- Added HARDNESS_PROTOCOL.md (kill conditions, forbidden classifications, empirical proxy map)
- Added LITERATURE_MAP.md (primary empirical anchors, philosophy, rival theories)
- Added ROADMAP.md (phased plan)
- Added CHANGELOG.md (this file)
- Created claims/ directory: claim_ledger.yaml, claim_schema.json, status markdown files
- Created theory/ directory: component docs
- Created notes/ directory: raw conjectures, research log, anomalies, future experiments
- Created docs_for_external_review/ directory
- Migrated fixtures/ → cases/ with subdirectory standardization
- Renamed: self_continuity/ → self_continuity_cases/, sports_action_fields/ → sports_fields/,
  simulation_and_transfer/ → simulation_transfer/, ai_and_agi/ → agi_ai_cases/
- Added consciousness_edge_cases YAML files: blindsight, split_brain, absence_seizure,
  depersonalization, pain_asymbolia
- Added false_positives YAML files: llm_chatbot, llm_agent_with_memory, fictional_character,
  trails_inhabited_universe, religion_symbolic_field, ideology_safe_possession,
  wikipedia_article, helix_workspace, scientific_institution, corporation, market_system
- Added new schemas: claim_status, evidence_level, empirical_proxy
- Updated README.md for new structure

---

## [0.2.0] — 2026-04-25 (previous session)

### Hardening and V2 expansion

- Renamed primary term: A (appearance-from-within) → G (givenness / primitive residue)
- Added THEORY_UNDER_TEST.md
- Added new schemas: consciousness_result, false_positive_case, rival_theory_result
- Added individual YAML files for consciousness_edge_cases (waking_human, dreaming,
  minimal_awareness, psychedelic_ego_dissolution, propofol_unconsciousness,
  ketamine_unresponsive_dreaming, locked_in_syndrome)
- Added G-independence requirement: G must not be inferred from intelligence, language,
  self-report, field structure, or symbolic continuity
- Added self-continuity extension: R term, S_suspended formula, 12 YAML fixtures

---

## [0.1.0] — 2026-04-25 (initial build)

### Initial implementation

- Created labs/inhabited_interiority/ directory structure
- Implemented C = A·U·D·T·F formula (A later renamed G)
- Implemented S = C·P·O·B·K·N formula
- Created 5 schemas: field_case, continuity_case, false_positive, transfer_case, stress_result
- Created JSON fixtures for all initial domains
- Created 7 Python scripts (classify_field_type, score_consciousness_candidate, etc.)
- Created README.md, THEORY_UNDER_TEST.md
