# model/domains/

Modeled interpretation chambers. Each domain has its own external/operational model first, then maps to the cognitive map. Storage lives in `data/`; interpretation lives here.

## Subdomain layout (target)

```text
model/domains/
├── games/
│   ├── overwatch/
│   ├── soulsborne/
│   ├── trails/           # currently at model/domains/trails/ — Phase 2 decides relocation
│   ├── eft/
│   ├── dota/
│   ├── stardew/
│   └── completed_games/
├── music/
├── internet/
├── sports/
├── food/
├── aesthetics/
├── language/
└── software/
```

Pre-existing folders not in the target above (`self/`, `wiki/`, `trails/` at top level) remain in place pending Phase 2 disposition.

## Canonical domain README template

Every domain README (and subdomain README, when subject-specific) must follow this shape. Phase 1 scaffolds empty stubs — content is authored by the operator in a later pass.

```markdown
# Domain: <Name>

## Domain Role
What this domain proves about the operator.

## External / Operational Model
What this domain is independent of Dissonance.

## Dissonance Mapping
Which master patterns this domain supports.

## Evidence Anchors
Specific examples (artists, games, items) with one-line explanations.

## Dataset Notes
Relevant exports, play counts, scrobbles, modlists, screenshots, saved posts.
Detailed enough to reopen later, not raw dumps.

## False Positives
What a shallow model would wrongly infer.

## Anomalies / Open Questions
Things that do not fit yet.

## Upward Links
Pattern IDs in `model/map/patterns.yaml` this domain supports.

## Downward Links
Subfolders, evidence files, reports, datasets supporting this README.
```

## Rules

1. Build the domain's operational model **first**, independent of Dissonance.
2. Preserve exact examples as evidence anchors. Do not flatten taste into traits.
3. Map examples to master patterns using the IDs in `model/map/patterns.yaml`.
4. Keep detailed local knowledge here. Do not bloat `DISSONANCE.md`.
5. Update `model/map/links.yaml` only when a relationship is stable.
6. Mark uncertain claims as open questions.
7. Do not duplicate raw data. Summarize and link to `data/` paths.
8. Each domain README must read independently.

