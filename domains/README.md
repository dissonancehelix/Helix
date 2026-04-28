# domains/

Active domain capsules. Each capsule owns its model, tools, data, labs, and
reports.

## Active Domains

- `self/`
- `music/`
- `games/`
- `trails/`
- `wiki/`
- `software/`
- `language/`

## Capsule Contract

```text
domains/<domain>/
├── README.md
├── manifest.yaml
├── model/
├── data/
│   └── output/
├── tools/
└── reports/
```

Cleaned domain records live directly in `data/`. Generated products, indexes,
profiles, and other tool outputs live under `data/output/`.

Domain-local `labs/` is optional and only for true local experiments.

Domains elaborate the master map. They do not redefine `DISSONANCE.md` or
`core/map/`.
