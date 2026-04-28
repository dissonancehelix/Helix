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
│   ├── normalized/
│   └── derived/
├── tools/
├── labs/
└── reports/
```

Domains elaborate the master map. They do not redefine `DISSONANCE.md` or
`core/map/`.
