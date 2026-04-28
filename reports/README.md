# reports/

Generated review artifacts. Outputs from labs, regenerations, imports, and analyses land here for review, promotion, or deletion. **Reports are never source of truth.**

## Layout

```text
reports/
├── tests/          # lab test outputs (verdicts, refutations, coverage runs)
├── analyses/       # ad-hoc analytical outputs (e.g. cross-domain comparisons)
│   └── workstation/  # workstation_bridge snapshots — review artifacts only, never canon
├── regenerations/  # regenerated documents and refactor summaries
└── imports/        # import-pipeline outputs awaiting review
```

## Reports as epistemic airlocks

> Reports quarantine generated meaning before promotion.

Every artifact under `reports/` is a holding cell for meaning that has not yet earned canonical status:

- A report **may contain generated interpretation** — analyses, snapshots, proposals, regenerations.
- A report is **never source of truth by default**.
- A report **must be reviewed** before promotion into `model/map/`, a domain README, or `DISSONANCE.md`.
- A report **may be promoted, archived, or deleted** — but never silently absorbed into canon.
- **Phase reports** (under `reports/regenerations/`) are *implementation history*, not ontology, unless their findings are later promoted.

This quarantine is the anti-drift firewall: it prevents tools, agents, or generators from contaminating source-of-truth layers with unreviewed output.

## Rules

- Reports do not own facts. The fact lives in `data/` or in the lab fixture.
- Reports do not redefine patterns. If a report contradicts `model/map/patterns.yaml`, file an entry in `model/map/anomalies.yaml` and link the report.
- Reports rot. A report older than its source data should be regenerated or deleted.
- Promotion path: a report's *findings* can be promoted into a domain README, a lab claim, or a map entry — but the report itself stays as the produced artifact.

