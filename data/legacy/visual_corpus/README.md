# Visual Corpus Evidence

Status: local raw evidence preserved under `data/raw/visual_corpus/`.

This corpus is not a first-class domain. It is a visual evidence surface that currently decompresses into the active `games`, `music`, `self`, and `software` domains when needed.

Raw screenshots and downloaded images are intentionally not tracked in Git. The repo should keep the analysis, pattern names, and compact evidence handles, not a permanent dump of copyrighted/reference images.

Generated local analysis/contact sheets may live under `reports/analyses/visual_corpus/`.

## Inventory

- `danganronpa`: 41 images
- `decap_attack`: 6 images
- `disco_elysium_portraits`: 116 images
- `dota_dark_seer`: 10 images
- `kentucky_route_zero`: 15 images
- `norco`: 15 images
- `osamu_sato`: 10 images
- `overwatch_moira`: 9 images
- `paradise_killer`: 10 images
- `persona_5_ui`: 14 images
- `yume_nikki`: 23 images

## Re-analysis

The corpus is not mostly "aesthetic taste" in the loose sense. It is evidence for how visual systems become readable, inhabitable, and returnable.

### Shaped Absence

Black or empty space becomes content when its boundary is sharp enough to carry structure.

Evidence:
- `yume_nikki`: void fields, tiny player sprite, repeated symbols, dark rooms as topology
- `kentucky_route_zero`: opaque black silhouettes, cutaway buildings, isolated lit rooms
- `osamu_sato`: figure-in-deep-space, letterbox, clashing low-poly isolation
- `persona_5_ui`: black as graphic material rather than empty background

Best compression:

> Absence works when it has architecture.

### Bounded Abundance

Variation becomes attractive when it happens inside a stable visual grammar.

Evidence:
- `disco_elysium_portraits`: 116 portraits, one brush grammar, scuffed faces, limited pigments
- `yume_nikki`: many worlds, one tiny-sprite/room grammar
- `paradise_killer`: extreme color and fashion bounded by tropical/editorial framing
- `danganronpa`: character excess bounded by red/black/white, cutout UI, and trial-room grammar

Best compression:

> Many variants, one law.

### Compatible Mindprint

The strongest sets are instantly attributable to a specific hand or constraint system.

Evidence:
- KIKIYAMA / `yume_nikki`
- Osamu Sato / `osamu_sato`
- `disco_elysium_portraits`
- `kentucky_route_zero`
- `persona_5_ui`
- `norco`

Best compression:

> A visual world should remember who made it.

### Surrealism as Place

Surrealism works when it becomes a navigable place, not a novelty layer.

Evidence:
- `yume_nikki`
- `osamu_sato`
- `kentucky_route_zero`
- `norco`

Borderline/useful contrast:
- `paradise_killer` is more decorative/editorial surrealism: coherent and pleasurable, but less haunted.

Best compression:

> Weirdness must be inhabitable.

### State Inspectability

Some visual systems are attractive because they expose state clearly.

Evidence:
- `dota_dark_seer`: dense HUD, minimap, cooldowns, items, status, spell fields
- `overwatch_moira`: silhouette discipline and ability-color readability
- `persona_5_ui`: graphic violence remains legible because the palette and shapes are strict

Best compression:

> Complexity is acceptable when the state is readable.

### Object-Worlds That Slept Longer Than the Player

Some worlds feel already old: they do not exist for the player, but permit entry.

Evidence:
- `yume_nikki`
- `osamu_sato`
- `kentucky_route_zero`
- `norco`

Best compression:

> The world was there before you arrived.

## Preservation Decision

Keep:
- This analysis.
- Pattern IDs and examples in `model/map/`.
- Domain references in `model/domains/games/README.md`.
- Local generated reports/contact sheets when useful.

Do not commit by default:
- raw screenshots/images
- downloaded image dumps
- zip archives

Promote raw images only if a future visual-corpus application needs reproducible fixtures.

