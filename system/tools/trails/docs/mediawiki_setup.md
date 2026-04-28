# Trails Database: MediaWiki Backend — Operator Reference

> This is an operational reference for LLMs working in this project. It describes how to read, write, and query the MediaWiki backend programmatically. Installation details are minimal — focus is on day-to-day operation.

---

## What the Backend Is

MediaWiki runs at `http://localhost:8080` inside WSL Ubuntu. It is not a human-facing interface. All interaction is programmatic via the MediaWiki API at:

```
http://localhost:8080/api.php
```

It provides two things:
1. **Cargo** — structured field enforcement and queryable storage (Wikidata-like). Each Atlas page class has a Cargo table that validates and stores Metadata fields.
2. **Wiki pages** — structured storage for Atlas prose, organized by namespace.

The SQLite database (`retrieval/index/trails.db`) remains the primary Metadata store. MediaWiki/Cargo is the enforcement and authoring layer on top.

---

## Starting the Backend

WSL does not persist services across restarts. Check and start if needed:

```bash
wsl bash -c "echo 'Helix' | sudo -S service mariadb start && echo 'Helix' | sudo -S service apache2 start"
wsl bash -c "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080"
# Expected: 200
```

---

## Credentials

| Item | Value |
| :--- | :--- |
| Wiki URL | `http://localhost:8080` |
| API endpoint | `http://localhost:8080/api.php` |
| Admin user | `WikiAdmin` |
| Admin password | `WikiAdmin2026!` |
| DB name | `trails_wiki` |
| DB user / pass | `wiki_user` / `trailsdb2026` |
| DB host | `127.0.0.1` |

---

## API Authentication

All write operations require authentication. Use `action=login` + `action=clientlogin` or a bot password.

### Login flow (Python)

```python
import requests

SESSION = requests.Session()
API = "http://localhost:8080/api.php"

def login():
    # Step 1: get login token
    r = SESSION.get(API, params={
        "action": "query", "meta": "tokens",
        "type": "login", "format": "json"
    })
    token = r.json()["query"]["tokens"]["logintoken"]

    # Step 2: log in
    SESSION.post(API, data={
        "action": "login", "format": "json",
        "lgname": "WikiAdmin", "lgpassword": "WikiAdmin2026!",
        "lgtoken": token
    })

def get_csrf_token():
    r = SESSION.get(API, params={
        "action": "query", "meta": "tokens", "format": "json"
    })
    return r.json()["query"]["tokens"]["csrftoken"]
```

---

## Reading a Page

```python
def read_page(title):
    r = SESSION.get(API, params={
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvslots": "main",
        "format": "json"
    })
    pages = r.json()["query"]["pages"]
    page = next(iter(pages.values()))
    if "missing" in page:
        return None
    return page["revisions"][0]["slots"]["main"]["*"]
```

---

## Writing a Page

```python
def write_page(title, content, summary=""):
    token = get_csrf_token()
    SESSION.post(API, data={
        "action": "edit",
        "title": title,
        "text": content,
        "summary": summary,
        "format": "json",
        "token": token
    })
```

### Namespace routing

| Content type | Title prefix |
| :--- | :--- |
| Atlas entry | `Estelle Bright` (no prefix — Main namespace) |
| Metadata/Cargo record | `Metadata:Estelle Bright` |
| Draft entry | `Draft:Estelle Bright` |
| Infobox template | `Template:CharacterInfobox` |
| Lua module | `Module:Character` |
| Schema definition | `Schema:Character` |

---

## Querying Cargo (once Cargo extension is active)

Cargo tables are defined by `{{#cargo_declare:}}` in template pages. Once declared and populated, they are queryable via API:

```python
def cargo_query(table, fields, where="", limit=50):
    r = SESSION.get(API, params={
        "action": "cargoquery",
        "tables": table,
        "fields": fields,
        "where": where,
        "limit": limit,
        "format": "json"
    })
    return r.json().get("cargoquery", [])
```

Example — fetch all characters in the Sky arc:
```python
results = cargo_query(
    table="Character",
    fields="name_en,arc_first_appearance,spoiler_band",
    where="arc_first_appearance='Sky'"
)
```

---

## Cargo Table Definitions (per Atlas page class)

These match the Metadata fields in `docs/schema.md`. Each table is declared in its Template page.

### Character
```
{{#cargo_declare:_table=Character
|entity_id=String
|name_en=String
|name_ja=String
|aliases=List (,) of String
|arc_first_appearance=String
|spoiler_band=Integer
|affiliation=String
|voice_jp=String
|voice_en=String
}}
```

### Place
```
{{#cargo_declare:_table=Place
|entity_id=String
|name_en=String
|name_ja=String
|region=String
|nation=String
|place_type=String
|first_appearance=String
|spoiler_band=Integer
}}
```

### Organization
```
{{#cargo_declare:_table=Organization
|entity_id=String
|name_en=String
|name_ja=String
|org_type=String
|headquarters=String
|founding_arc=String
|spoiler_band=Integer
}}
```

### Event
```
{{#cargo_declare:_table=Event
|entity_id=String
|name_en=String
|arc=String
|chronology_position=String
|involved_entities=List (,) of String
|spoiler_band=Integer
}}
```

### Concept
```
{{#cargo_declare:_table=Concept
|entity_id=String
|name_en=String
|name_ja=String
|concept_type=String
|domain=String
|spoiler_band=Integer
}}
```

### Media
```
{{#cargo_declare:_table=Media
|media_id=String
|title_en=String
|title_ja=String
|media_type=String
|arc=String
|release_year=Integer
|platform=String
|spoiler_band=Integer
}}
```

---

## Atlas Entry Structure (wikitext)

A standard Atlas entry page in the Main namespace follows this structure:

```wikitext
{{CharacterInfobox
|entity_id=char:estelle_bright
|name_en=Estelle Bright
|name_ja=エステル・ブライト
|arc_first_appearance=Sky
|spoiler_band=14
|affiliation=Bracer Guild (Liberl)
|voice_jp=Kanae Itō
}}

== Identity & Role ==
Estelle Bright is the protagonist of the ''Sky'' arc. She operates as a junior Bracer
in the Liberl Kingdom, initially under the supervision of her father Cassius Bright.

== Chronological History ==
=== Sky Arc ===
[prose]

== Affiliations & Relationships ==
* [[Bracer Guild]] — Member
* [[Joshua Bright]] — Arc partner

== Appearances ==
* ''[[Trails in the Sky FC]]'' (Sky arc)
* ''[[Trails in the Sky SC]]'' (Sky arc)

== Sources ==
* <code>wiki:kiseki_fandom</code> (trust tier 2)

[[Category:Character]][[Category:Sky Arc]]
```

---

## Lifecycle States in MediaWiki

Mirrors `lifecycle_registry` in `trails.db`:

| State | MediaWiki location | Condition |
| :--- | :--- | :--- |
| `raw` | Not in wiki | Entity exists in trails.db only |
| `normalized` | `Draft:PageName` | Metadata clean, not yet curated |
| `curated` | `Main/PageName` (unapproved revision) | Prose slots filled, pending approval |
| `export_ready` | `Main/PageName` (approved revision) | Approved Revs approved |

Advancement is done programmatically: move a page from `Draft:` to Main, then call the Approved Revs API to mark a revision as approved.

---

## Approved Revs API (once extension is active)

```python
def approve_revision(page_title, rev_id):
    token = get_csrf_token()
    SESSION.post(API, data={
        "action": "approvepage",
        "title": page_title,
        "revid": rev_id,
        "token": token,
        "format": "json"
    })
```

---

## Spoiler Suppression

The master Atlas page always contains the full entry. Spoiler suppression is a query-time filter applied when generating exports or search results — not a wiki operation.

When generating exports from Cargo:
```python
# Safe export (band < 100)
cargo_query("Character", "name_en,spoiler_band", where="spoiler_band < 100")

# Curator mode (all content)
cargo_query("Character", "name_en,spoiler_band", where="spoiler_band <= 100")
```

---

## Key Files

| File | Purpose |
| :--- | :--- |
| `scripts/setup_mediawiki.sh` | Full reinstall script |
| `scripts/LocalSettings_additions.php` | Custom namespaces and extension config |
| `/var/www/html/wiki/LocalSettings.php` | Live wiki config (WSL) |
| `pipelines/ingest/mediawiki_sync.py` | Existing API client (Kiseki Fandom + JA Wikipedia sync) — patterns reusable for local wiki |
