# Residue Science Lab

Residue Science is a bounded lab for testing what remains after transformation, what disappears, and how future agents can reconstruct a crossing without inventing a fake past.

Best compression:

> **Residue Science studies what remains after transformation, what disappears, and how future agents can reconstruct the crossing without inventing a fake past.**

Second compression:

> **Preserve enough residue that future reconstruction remains possible.**

Third compression:

> **A missing trace is not automatically a hidden cause. It is an uncertainty boundary.**

## Purpose

This lab exists to discriminate between three different states that can look similar after time has passed:

```text
preserved transformation
missing evidence
invented continuity
```

It is not a new domain and not active canon. It is a pressure chamber for evidence lineage, archive hygiene, claim provenance, reconstruction limits, and false-history prevention.

Residue Science is useful when a system has changed and a later reader, agent, or future operator needs to answer:

- what changed?
- what trace did it leave?
- what can be reconstructed?
- what cannot be reconstructed?
- what evidence decayed, moved, or was never captured?
- what story would be tempting but unsupported?

## Claim under pressure

Primary claim:

> A Helix claim, domain state, file transformation, or theory update is more trustworthy when its residue chain is reconstructible from current statement back through intermediate report, source, artifact, or observed operator correction.

Falsifiable form:

> If important Helix claims repeatedly cannot be traced to evidence, source lineage, operator correction, or reviewable transformation records, then the map is overcompressing and the relevant claims should be demoted, marked uncertain, or moved into anomaly review.

This lab does not prove a claim true by finding residue. It only improves reconstruction confidence.

## Scope

Residue Science may inspect:

- Git history and file diffs
- report lineages
- domain-file claim paths
- source manifests
- archived exports and compact data products
- session harvests
- theory reports
- wiki/public-knowledge provenance
- game/music/body/aesthetic examples where residue is part of the mechanism

Residue Science does not own:

- `DISSONANCE.md` canon
- domain identity
- raw archives
- theory truth
- provenance policy by itself
- every old file simply because it exists

## Fixtures / data

Initial fixture classes:

| Fixture class | Example source | Question |
|---|---|---|
| Claim trace | `DISSONANCE.md` sentence or domain compression | Can it be traced backward? |
| Transform trace | Git diff / renamed file / deleted file | What changed and why? |
| Report trace | `domains/*/reports/` or `labs/*/reports/` | Was the finding promoted, rejected, or left provisional? |
| Archive trace | compact exports / local evidence summaries | Is raw provenance recoverable enough? |
| Negative trace | missing file, missing source, silent gap | Is absence being overinterpreted? |

Do not import heavy private archives into GitHub just to satisfy this lab. GitHub carries compact extracted data and reports; local-only archive material remains local unless explicitly promoted elsewhere.

## Scripts

No scripts are required in v0.1.

Future scripts should be small and audit-oriented, such as:

- claim-to-source trace checker
- file lineage summary generator
- missing-manifest detector
- report-promotion scanner
- hash/fixity verifier for compact artifacts

Scripts must not silently rewrite source-of-truth files. They should produce reports first.

## Outputs / reports location

Reports live under:

```text
labs/residue_science/reports/
```

Templates live under:

```text
labs/residue_science/templates/
```

Claim ledgers live under:

```text
labs/residue_science/claims/
```

## Method

Every residue pass should separate observation, interpretation, and transformation.

### 1. Observation

Record the visible traces:

```text
file paths
commit / timestamp if available
source document
claim text
supporting examples
missing expected evidence
```

### 2. Interpretation

Classify what the traces support:

```text
strong lineage
partial lineage
weak lineage
missing lineage
conflicting lineage
```

### 3. Transformation

Only after review, propose one of:

```text
promote confidence
keep provisional
demote claim
create anomaly
request source recovery
leave unresolved
```

## Residue classes

| Class | Meaning |
|---|---|
| Direct residue | raw evidence, operator correction, source export, commit diff |
| Intermediate residue | report, normalized data, session harvest, compact profile |
| Compressed residue | domain section, claim card, best compression, map node |
| Negative residue | expected trace missing or unavailable |
| False residue | artifact that looks evidential but does not support the claim |
| Decayed residue | once-useful evidence now stale, incomplete, inaccessible, or ambiguous |
| Reconstructive residue | enough trace remains to rebuild a plausible lineage with uncertainty noted |

## False-positive controls

Residue Science must guard against these shallow conclusions:

| False positive | Correction |
|---|---|
| Missing evidence means suppression or deletion | Missing evidence may mean never recorded, private, stale, local-only, or outside the checked layer. |
| A clean story means true lineage | Smooth reconstruction can be invented after the fact. Require traceable support. |
| More archive is always better | Archive bloat can reduce active legibility. Preserve load-bearing residue, not all sediment. |
| Git history is full truth | Commits show file transformations, not every reason or context. |
| A report is canon | Reports are evidence pressure until promoted. |
| A source proves interpretation | Sources support claims; interpretation still needs scope and confidence. |
| A beautiful cross-domain fit is proof | Beauty is not causality; residue improves traceability, not metaphysical certainty. |

## Demotion criteria

A claim, compression, or domain update should be weakened when:

- no traceable evidence can be found after a reasonable search,
- the only support is an agent inference with no operator correction or source anchor,
- the claim depends on an archive that is unavailable, private, or unverified,
- multiple traces conflict and no anomaly entry exists,
- compressed wording makes the original evidence unrecoverable,
- the claim overreads absence as proof,
- the claim survived because it sounded structurally elegant rather than because it had lineage.

Possible outcomes:

```text
CLAIM_STABLE
CLAIM_PARTIAL
CLAIM_UNTRACED
CLAIM_CONFLICTED
CLAIM_OVERCOMPRESSED
CLAIM_DEMOTE_TO_ANOMALY
```

## Promotion criteria

Residue Science can strengthen confidence when:

- a claim traces to direct operator correction, durable source, or compact evidence product,
- intermediate reports preserve uncertainty and scope,
- domain files preserve examples as evidence doors,
- source lineage remains reconstructible without private guessing,
- absence is marked as absence rather than filled with story,
- the compression remains reversible enough for future agents to reopen the room.

## Relation to existing labs

Residue Science is adjacent to, but separate from, the Appearance–Ownership–Continuity lab.

Working bridge:

```text
LIP = before the crossing, when local evidence is insufficient
DCP = the crossing / commitment that compresses possibility into actuality
EIP = the residue after the crossing, where the prior epistemic state cannot be fully restored
Residue Science = audit method for what can be reconstructed after the crossing
```

This bridge is a methodological analogy unless supported by specific reports.

## Non-domain rule

Residue Science should remain a lab unless it develops a distinct operational interior with reusable tools, claim ledgers, audit reports, and cross-domain procedures that would otherwise flatten the main map.

Do not promote it to a first-class domain merely because the metaphor is strong.

Best compression:

> **This is a forensic flashlight, not a new room.**
