# labs/

Pressure chambers. Each lab tests a claim made elsewhere in the system: in `DISSONANCE.md`, in `core/map/patterns.yaml`, or in a domain file. Labs are not theory shrines: a lab without a falsifiable claim and a demotion criterion is overdue for either sharpening or deletion.

## Structure

Each lab is a subfolder with at minimum:

```text
labs/<name>/
├── README.md          # purpose, claim, fixtures, scripts, outputs path, false-positive controls, demotion criteria
├── (theory docs)
├── (test registry / claim ledger)
└── (fixtures / scripts)
```

## Lab README contract

Each lab README must cover:

- **Purpose** — what this lab exists to discriminate.
- **Claim under pressure** — the specific assertion being tested, in falsifiable form.
- **Fixtures / data** — what evidence the lab consumes (link to data/ paths).
- **Scripts** — how the test runs.
- **Outputs / reports location** — where produced artifacts land (typically `labs/reports/tests/`).
- **False-positive controls** — what a shallow model would wrongly conclude, and how this lab guards against it.
- **Demotion criteria** — under what observed result the lab declares the claim weakened, and what happens to the linked map IDs.

## Current labs

- `temporal_ownership/` — Temporal Ownership Model work: ICT, DCP, LIP, EIP, ownership, continuity, commitment, residue, and appearance-from-within pressure tests.
- `cognitive_mapping/` — claims about the operator ontology and the map structure itself.
- `invariants/` — cross-domain invariant discovery and pressure work.

## Rules

- A lab does not own truth. It applies pressure.
- A lab that cannot fail is not a lab. Mark it speculative or remove it.
- When a lab demotes a pattern, update `core/map/patterns.yaml` status and add a `core/map/anomalies.yaml` entry recording the disagreement.
