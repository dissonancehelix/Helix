# Inhabited Interiority / Perturbable Phenomenal Field

**Lab status:** active candidate / local-lab only  
**Research program:** Inhabited Interiority Theory (IIT-adjacent falsification harness)  
**Location:** `labs/inhabited_interiority/`  
**Governed by:** `AGENT_RULES.md`, `WORKSPACE.md`

---

## Purpose

This lab does not prove the theory. It stress-tests it.

The goal is a falsification and classification harness that applies pressure to the candidate theory of consciousness, selfhood, and identity defined in `theory.md`. Every claim remains at candidate status until broken by a test or replaced by a better formulation. If a test breaks the theory, the break is preserved — not patched.

---

## Core Theory (Candidate)

**One sentence:** Consciousness is inhabited interiority — fielded appearance from within. Self is inhabited interiority preserving ownership through time.

**Formulas (stress-test scaffolds, not proofs):**

```
C = A · U · D · T · F

A = appearance-from-within
U = local unity / co-presence
D = differentiation / internal contrast
T = temporal thickness
F = field inclusion

If any term = 0, C = 0.
If any term = null, C is unresolvable.
```

```
S = C · P · O · B · K · N

P = perspective / from-here
O = ownership / mineness
B = self-boundary
K = carried constraint through time
N = non-branching continuity

If N = 0, singular self-continuity is impossible.
If C = 0, no self is possible.
```

```
Transfer(X_t → Y_t+1) preserves S iff it preserves C, P, O, B, K, and N.

Copy(pattern) ≠ Preserve(Self)
```

---

## Structure

```
labs/inhabited_interiority/
├── README.md                        ← this file
├── schemas/                         ← JSON Schema definitions
│   ├── field_case.schema.json       ← field classification fixture
│   ├── continuity_case.schema.json  ← self-continuity fixture
│   ├── false_positive.schema.json   ← false-positive control fixture
│   ├── transfer_case.schema.json    ← transfer scenario fixture
│   └── stress_result.schema.json    ← stress test output
├── fixtures/                        ← test cases
│   ├── consciousness_edge_cases/    ← waking, dreaming, anesthesia, split-brain, etc.
│   ├── simulation_and_transfer/     ← upload, copy, teleportation, sleep, reincarnation
│   ├── ai_and_agi/                  ← LLM, robot, RL agent, WBE, AGI candidate
│   ├── games_action_fields/         ← Dota, Rocket League, Trails, EFT, SOMA
│   ├── sports_action_fields/        ← NFL drive, soccer, basketball, combat sports
│   ├── board_card_fields/           ← chess, Magic, Go, poker, Dominion
│   ├── symbolic_fields/             ← religion, ideology, fiction, corporation, music
│   └── operational_fields/          ← Helix, Wikipedia, science, law, internet
├── scripts/                         ← analysis tools
│   ├── classify_field_type.py       ← classify fixtures by field type
│   ├── score_consciousness_candidate.py ← score C = A·U·D·T·F
│   ├── score_self_continuity.py     ← score S = C·P·O·B·K·N
│   ├── transfer_test.py             ← evaluate transfer scenarios
│   ├── branching_detector.py        ← find N=0 / branching failures
│   ├── false_positive_scan.py       ← verify false positives are rejected
│   ├── run_six_tests.py             ← run all 6 falsification tests
│   ├── run_domain_matrix.py         ← full fixture matrix with scores
│   └── generate_report.py           ← compile stress report to reports/
└── reports/
    └── .gitkeep                     ← reports generated here by generate_report.py
```

---

## Field Types

These are the eleven field types used in classification. None of them automatically constitute phenomenal consciousness.

| Field type | What it is | Phenomenal? |
|---|---|---|
| `constraint_field` | Lawful possibility-space | No |
| `closure_field` | Self-maintaining pattern | No by itself |
| `viability_field` | Living regulation | Not automatically |
| `phenomenal_field` | Lived co-presence | Yes if A > 0 |
| `action_field` | Agents coordinated by constraints | Field no; agents may be |
| `symbolic_field` | Meanings persist across agents | No unified subject |
| `operational_field` | Claims tested and preserved | No |
| `governance_field` | Rules update rules | No by itself |
| `aesthetic_field` | Structures experience | No — listener yes |
| `export_field` | Symbolic output | No by itself |
| `hybrid_agent_field` | Mixed/contested | Case-by-case |

**Anti-bloat rule:** Field-like organization is not automatically phenomenal.

---

## Six Tests

1. **temporal_deletion_test** — Remove time. Does C collapse when T → 0?
2. **boundary_perturbation_test** — Disturb inside/outside. What collapses — C or S?
3. **network_partition_test** — Split the system. One self, two, or network partition?
4. **false_positive_field_test** — What looks conscious but isn't? Does the theory reject it?
5. **carried_constraint_test** — Does the past remain active as constraint on the future?
6. **geometry_topology_test** — What relations survive deformation? Is the self a topology?

---

## Running the Scripts

All scripts use standard Python 3. No dependencies beyond the standard library.

```bash
# From anywhere in the workspace:
cd labs/inhabited_interiority/scripts

# Classify all field types
python classify_field_type.py --verbose

# Score consciousness candidates
python score_consciousness_candidate.py --candidates-only

# Score self-continuity cases
python score_self_continuity.py --show-topology

# Run transfer tests
python transfer_test.py --show-carriers --show-breaks

# Detect branching failures
python branching_detector.py --severity high

# Scan for false positives
python false_positive_scan.py --show-what-it-has

# Run all six tests
python run_six_tests.py --show-breaks

# Full domain matrix
python run_domain_matrix.py

# Generate report
python generate_report.py
```

---

## False-Positive Controls

The following are explicitly classified as non-phenomenal. If the theory promotes any of them, the theory is broken.

| Control | Why rejected |
|---|---|
| LLM persona | A is unestablished. No non-behavioral proxy for appearance-from-within. |
| Fictional character | Inhabited by the reader's phenomenal engagement, not itself. |
| Religion | Symbolic field. No unified subject inhabits it. |
| Ideology | Constraint field for phenomenal agents. Not a phenomenal field. |
| Corporation / state | Governance field with legal personhood attribution, not phenomenal status. |
| Sports team | Symbolic/institutional. Complete roster replacement, no self-continuity. |
| Dota match | Action field. Players are conscious; the match is not. |
| Rocket League rotation | Action field. K is high; A = 0. |
| NFL drive | Action field. K is explicit (down/distance); A = 0. |
| Trails world continuity | Symbolic field. Inhabited by the player; does not inhabit itself. |
| Helix workspace | Operational field. Processes claims; does not experience them. |
| Wikipedia article | Operational field. Edited by conscious agents; not conscious. |
| Music track | Aesthetic field. Structures listener's phenomenal time; not itself phenomenal. |
| Architectural space | Aesthetic field. Shapes inhabitation without inhabiting. |

---

## Transfer Case Classifications

| Transfer type | Pattern? | Self? | Classification |
|---|---|---|---|
| Ordinary biological change | yes | yes | identity_preserving_transformation |
| Sleep / anesthesia | yes | yes-ish | field_suspension_resumable |
| Gradual neural replacement | yes | unknown | possible_self_carrying |
| Destructive teleportation | yes | doubtful | pattern_copy_field_break_risk |
| Non-destructive copy | yes | no (N=0) | branching_descendants_only |
| Mind upload | yes | unknown | unresolved |
| Reincarnation (psychological) | yes | no proven carrier | unresolved |
| Soul claim | unknown | unknown | unresolved |
| Genetic lineage | yes | no | symbolic_survival_only |
| Symbolic legacy / profile | K only | no | symbolic_survival_only |

---

## Tone

Use: **candidate / stress result / revision pressure / demotion / unresolved**  
Avoid: **proved / solved / universal / confirmed**

The most important rule: if a test breaks the theory, preserve the break. Do not patch it with prose.

---

## Source Anchors

- SEP: [Phenomenological Self-Consciousness](https://plato.stanford.edu/entries/self-consciousness-phenomenological/)
- SEP: [Temporal Consciousness](https://plato.stanford.edu/entries/consciousness-temporal/)
- SEP: [Personal Identity](https://plato.stanford.edu/entries/identity-personal/)
- Bostrom: [Simulation Argument](https://simulation-argument.com/)
- Josipovic & Miskovic 2020: Nondual Awareness and Minimal Phenomenal Experience
- Gamma & Metzinger 2021: MPE questionnaire
- Perich, Narain, Gallego 2025: Neural manifold view of the brain
- Clark and Chalmers 1998: The Extended Mind

---

*This lab is an example of Order 9 infrastructure. Helix is the implementation; the research program is the concept.*
