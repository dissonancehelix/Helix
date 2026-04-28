# Template Intake Prep

## Purpose

Describes how operator-supplied templates will be ingested as first-class study targets.

Templates fed by the operator are treated differently from general template indexing:
they become **authoritative local study targets** with full dossier + sandbox + pattern treatment.

---

## Where template source lives

Cached at: `core/tools/wikimedia/template_index/<Template_name>.json`

Each file contains:
- `source_wikitext` — full template source from `action=query&prop=revisions`
- `doc_wikitext` — `/doc` page source (if exists)
- `templatedata` — TemplateData JSON (if exists)
- `params` — parsed parameter list with names, aliases, types, required/suggested
- `dependencies` — templates transcluded inside this one (heuristic)
- `description` — from TemplateData

---

## How to ingest a specific template

```python
from model.domains.language.wikipedia.operator import WikiOperator

op = WikiOperator()
op.index(["Infobox NFL player", "NFL player stats"])
```

Or via CLI:
```
python core/tools/wiki/wiki_tool.py index "Infobox NFL player" "NFL player stats"
```

---

## How template data connects to the rest of the subsystem

| Connection | How |
|-----------|-----|
| Rule engine | `dossiers/dossier.py` maps template names to policy families |
| Dossiers | `find_dossiers_for_template(name)` returns applicable family dossier |
| Sandbox | `op.expand(source)` tests template logic against live parser |
| Pattern library | `find_matching_patterns(source)` finds applicable rewrite patterns |
| Anti-patterns | `find_anti_patterns(source)` flags known breakage patterns in source |
| Patch critic | `op.critique(before, after, template_name=name)` uses dossier fragile zones |

---

## Priority templates to ingest next (operator's domain)

### NFL
- `Template:Infobox NFL player`
- `Template:NFL player stats`
- `Template:NFL draft`
- `Template:NFL link`

### Video game
- `Template:Infobox video game`
- `Template:Video game reviews`
- `Template:Video game release`

### Cross-domain
- `Template:Birth date and age`
- `Template:Death date and age`
- `Template:Infobox person`

---

## Extending the dossier system

When a new template family is identified, add a `TemplateFamilyDossier` entry to
`domains/language/model/wikipedia/dossiers/dossier.py` and add it to `DOSSIER_REGISTRY`.

Minimum required fields:
- `member_templates`
- `fragile_zones`
- `breakage_patterns`
- `relevant_policies`

