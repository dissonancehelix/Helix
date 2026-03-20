# Entity Schema

## Canonical identity

All entities use:

```text
domain.type:slug
```

Examples:

- `music.composer:jun_senoue`
- `music.track:rusty_ruin_act_1`
- `language.dataset:grammar_resolution`

## Canonical entity shape

```json
{
  "id": "domain.type:slug",
  "type": "TypeName",
  "name": "Human-readable name",
  "label": "Short display label",
  "description": "Optional sentence",
  "metadata": {},
  "external_ids": {},
  "relationships": [
    {
      "relation": "RELATION_NAME",
      "target_id": "domain.type:slug",
      "confidence": 1.0
    }
  ]
}
```

## File layout rule

- Filename = `slug.json`
- Full identity stays inside the JSON payload.
- Registry index lives at `codex/atlas/entities/registry.json`.
