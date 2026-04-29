# Domain: Language

## Domain Role

Language is a first-class domain for linguistics, English, Spanish, grammar,
register, translation alignment, and public-language structure.

Spanish and English are nested surfaces inside this domain. They are not root
domains and not merely self-domain evidence.

## Operational Model

This capsule owns language datasets, construction maps, template and grammar
analysis tools, and language labs. It can support Wikipedia work, self-modeling,
and learning workflows, but it remains its own domain.

## Capsule Contents

- `model/` — domain model and future language-specific specs.
- `data/` — cleaned language records.
- `data/` — generated language datasets and caches.
- `tools/` — language and Spanish helper pipelines.
- `labs/` — language research probes.
- `reports/` — review artifacts from language workflows.

## Rules

- Domain-owned outputs stay inside this capsule.
- Raw external language dumps belong in `archive/raw/`.
- Reports are review artifacts, not truth.
