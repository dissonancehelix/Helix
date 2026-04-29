# domains/

Active domain capsules. Each capsule owns its model, data, and reports.
Operational capsules may also own tools and local labs when real workflows or
experiments exist.

## Active Domains

- `self/`
- `music/`
- `games/`
- `trails/`
- `wiki/`
- `software/`
- `language/`
- `attraction/`
- `food/`
- `aesthetics/`
- `body_sensory/`
- `sports/`

## Capsule Contract

```text
domains/<domain>/
├── README.md
├── manifest.yaml
├── model/
├── data/
└── reports/
```

Cleaned domain records, generated products, indexes, profiles, and compact
tool outputs live directly under `data/`, grouped by meaningful local role.

`tools/` exists only when the domain owns a runnable workflow.

Domain-local `labs/` is optional and only for true local experiments.

Domains elaborate the master map. They do not redefine `DISSONANCE.md` or
`core/map/`.
