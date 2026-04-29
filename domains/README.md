# Domain Capsules

`domains/` holds the first-class bounded contexts that decompress
`DISSONANCE.md` into browsable rooms.

Domains elaborate the master map; they do not redefine it. Each domain owns the
durable interpretation, compact data, and review artifacts for one recurring
field of cognition, taste, action, or evidence.

Best compression:

> **The main map names the doors; domain files hold the rooms.**

## Shape

Active domain capsules use named domain files:

```text
domains/<domain>/
├── <DOMAIN>.md
├── manifest.yaml
├── model/
├── data/
└── reports/
```

Operational domains also have `tools/` when they own runnable workflows.
Domain-local `labs/` exists only for true local experiments.

Do not create domain-root `README.md` files. The active room file is named
after the domain.

## Active Domains

| Domain | Domain file | Role |
|---|---|---|
| `self` | `domains/self/SELF.md` | cognitive style, neurotype constraints, sensory/social gates, response debt, attention chambers, and operational terrain |
| `music` | `domains/music/MUSIC.md` | foobar, VGM, DSP, metadata, world-listening, bass/air/return, library evidence |
| `games` | `domains/games/GAMES.md` | field mechanics, authored worlds, roles, transition systems, completion/playtime evidence |
| `trails` | `domains/trails/TRAILS.md` | Trails/Kiseki continuity, atlas work, wiki/database work, world-memory, source ingestion |
| `wiki` | `domains/wiki/WIKI.md` | Wikipedia editing, article architecture, citations, templates, infoboxes, Commons/Wikidata |
| `software` | `domains/software/SOFTWARE.md` | Helix, schemas, inspectable agency, LLM collaboration, tooling, executable personal ontology |
| `language` | `domains/language/LANGUAGE.md` | linguistics, English, Spanish, Japanese/source access, grammar, register, translation alignment |
| `attraction` | `domains/attraction/ATTRACTION.md` | sexual/visual attraction, face-primary beauty gate, channel convergence, body-signal hierarchy |
| `food` | `domains/food/FOOD.md` | bounded abundance, soft base/sharp event, seasonal ritual, texture, comfort, convenience |
| `aesthetics` | `domains/aesthetics/AESTHETICS.md` | color, warmth, darkness, enclosure, texture, ruins, inhabited environments |
| `body_sensory` | `domains/body_sensory/BODY_SENSORY.md` | DOMS, massage, stretch, localizable body maps, controlled intensity, signal ownership |
| `sports` | `domains/sports/SPORTS.md` | Commanders fandom, Jayden Daniels, live team state, future leverage, public-knowledge maintenance |
| `worldview` | `domains/worldview/WORLDVIEW.md` | politics, morals, institutions, religion/spirituality, metaphysical leaning, other-mind/personality views, shared standards |

## Domain Responsibilities

Each domain should answer:

1. What this domain is to the operator.
2. What it is not.
3. Core reward mechanics.
4. Core rejection mechanics.
5. Evidence anchors.
6. False positives / negative controls.
7. Local anomalies.
8. How the domain feeds the global cognitive map.
9. Best compression.

## Data And Evidence

`data/` holds compact domain-owned records and extracted evidence. Raw,
substantial source piles stay local-only in `archive/`; tiny source slips should
be deleted after extraction.

`model/` holds durable interpretation. `reports/` holds review artifacts only.
Reports do not become canon until reviewed and promoted.

## Tool Ownership

Use `tools/` only when a domain owns a runnable workflow.

Current workflow-owning domains:

- `self`
- `music`
- `games`
- `trails`
- `wiki`
- `software`
- `language`

Domains without workflow-owned tools yet:

- `attraction`
- `food`
- `aesthetics`
- `body_sensory`
- `sports`
- `worldview`

Best compression:

> **A domain gets tools when it acts, not merely because it exists.**
