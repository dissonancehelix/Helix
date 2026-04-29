#!/usr/bin/env python3
"""
Trails Database — Cargo vertical slice setup
Wires up the first four Cargo tables and all supporting MediaWiki pages.

Tables created:
  MediaEntry   — games, anime, manga, drama CDs
  Character    — named characters
  Appearance   — character ↔ media junction
  SourceRecord — ingestion provenance

Run from WSL or Windows with wiki running at http://localhost:8080.
Idempotent: re-running overwrites pages safely.
"""

import requests
import subprocess
import sys

API = "http://localhost:8080/api.php"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "TrailsDBSetup/1.0"})


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login():
    r = SESSION.get(API, params={
        "action": "query", "meta": "tokens",
        "type": "login", "format": "json"
    })
    token = r.json()["query"]["tokens"]["logintoken"]
    resp = SESSION.post(API, data={
        "action": "login", "format": "json",
        "lgname": "WikiAdmin", "lgpassword": "WikiAdmin2026!",
        "lgtoken": token
    })
    result = resp.json()
    if result.get("login", {}).get("result") != "Success":
        print(f"Login failed: {result}")
        sys.exit(1)
    print("Logged in as WikiAdmin")


def csrf():
    r = SESSION.get(API, params={
        "action": "query", "meta": "tokens", "format": "json"
    })
    return r.json()["query"]["tokens"]["csrftoken"]


def write_page(title, content, summary="cargo-setup"):
    token = csrf()
    r = SESSION.post(API, data={
        "action": "edit",
        "title": title,
        "text": content,
        "summary": summary,
        "format": "json",
        "token": token,
    })
    result = r.json()
    status = result.get("edit", {}).get("result", "UNKNOWN")
    marker = "OK" if status == "Success" else "FAIL"
    print(f"  [{marker}] {title}")
    if status != "Success":
        print(f"         {result}")


# ---------------------------------------------------------------------------
# Page content definitions
# ---------------------------------------------------------------------------

PAGES = {}

# ---- MediaEntry table -------------------------------------------------------

PAGES["Template:MediaEntryData"] = """\
<noinclude>
Cargo table declaration for '''MediaEntry'''.

Call this template on each media entity page to populate the Cargo table.

=== Fields ===
{| class="wikitable"
! Field !! Type !! Notes
|-
| media_id || String || Canonical ID. Mirrors trails.db media_registry. e.g. <code>media:trails_sky_fc</code>
|-
| title_en || String || Official English release title
|-
| title_ja || String || Original Japanese title
|-
| media_type || String || <code>game</code> · <code>anime</code> · <code>manga</code> · <code>drama_cd</code> · <code>side_story</code>
|-
| arc || String || <code>Sky</code> · <code>Crossbell</code> · <code>Erebonia</code> · <code>Reverie</code> · <code>Calvard</code> · <code>Kai</code>
|-
| release_year || Integer || Year of original JP release
|-
| platform || String || Pipe-separated if multi-platform: <code>PC|PS4|Switch</code>
|-
| developer || String || Default: Nihon Falcom
|-
| publisher || String || Regional publisher (EN release)
|-
| spoiler_band || Integer || 0–100. Mirrors trails.db spoiler_band convention.
|}

{{#cargo_declare:_table=MediaEntry
|media_id=String
|title_en=String
|title_ja=String
|media_type=String
|arc=String
|release_year=Integer
|platform=String
|developer=String
|publisher=String
|spoiler_band=Integer
}}
[[Category:Cargo table templates]]
</noinclude><includeonly>{{#cargo_store:_table=MediaEntry
|media_id={{{media_id|}}}
|title_en={{{title_en|}}}
|title_ja={{{title_ja|}}}
|media_type={{{media_type|game}}}
|arc={{{arc|}}}
|release_year={{{release_year|}}}
|platform={{{platform|}}}
|developer={{{developer|Nihon Falcom}}}
|publisher={{{publisher|}}}
|spoiler_band={{{spoiler_band|0}}}
}}</includeonly>
"""

# ---- Character table --------------------------------------------------------

PAGES["Template:CharacterData"] = """\
<noinclude>
Cargo table declaration for '''Character'''.

Call this template on each character page to populate the Cargo table.

=== Fields ===
{| class="wikitable"
! Field !! Type !! Notes
|-
| entity_id || String || Canonical ID. Mirrors trails.db entity_registry. e.g. <code>char:estelle_bright</code>
|-
| name_en || String || English display name
|-
| name_ja || String || Japanese name
|-
| aliases || List (,) of String || Comma-separated alternate names/titles
|-
| arc_first_appearance || String || Arc name of first appearance. e.g. <code>Sky</code>
|-
| spoiler_band || Integer || 0–100
|-
| voice_jp || String || Japanese voice actor
|-
| voice_en || String || English voice actor (if dubbed)
|}

{{#cargo_declare:_table=Character
|entity_id=String
|name_en=String
|name_ja=String
|aliases=String
|arc_first_appearance=String
|spoiler_band=Integer
|voice_jp=String
|voice_en=String
}}
[[Category:Cargo table templates]]
</noinclude><includeonly>{{#cargo_store:_table=Character
|entity_id={{{entity_id|}}}
|name_en={{{name_en|}}}
|name_ja={{{name_ja|}}}
|aliases={{{aliases|}}}
|arc_first_appearance={{{arc_first_appearance|}}}
|spoiler_band={{{spoiler_band|0}}}
|voice_jp={{{voice_jp|}}}
|voice_en={{{voice_en|}}}
}}</includeonly>
"""

# ---- Appearance table -------------------------------------------------------

PAGES["Template:AppearanceData"] = """\
<noinclude>
Cargo table declaration for '''Appearance'''.

Junction table linking Character entities to MediaEntry entities.
One row per (entity_id, media_id) pair.

=== Fields ===
{| class="wikitable"
! Field !! Type !! Notes
|-
| entity_id || String || FK → Character.entity_id
|-
| media_id || String || FK → MediaEntry.media_id
|-
| role || String || <code>protagonist</code> · <code>supporting</code> · <code>mentioned</code> · <code>playable</code> · <code>antagonist</code>
|-
| spoiler_band || Integer || Band at which this appearance can be revealed (may differ from character base band)
|}

{{#cargo_declare:_table=Appearance
|entity_id=String
|media_id=String
|role=String
|spoiler_band=Integer
}}
[[Category:Cargo table templates]]
</noinclude><includeonly>{{#cargo_store:_table=Appearance
|entity_id={{{entity_id|}}}
|media_id={{{media_id|}}}
|role={{{role|supporting}}}
|spoiler_band={{{spoiler_band|0}}}
}}</includeonly>
"""

# ---- SourceRecord table -----------------------------------------------------

PAGES["Template:SourceRecordData"] = """\
<noinclude>
Cargo table declaration for '''SourceRecord'''.

Mirrors source provenance from trails.db source_registry.
One row per registered ingestion source.

=== Fields ===
{| class="wikitable"
! Field !! Type !! Notes
|-
| source_id || String || Canonical ID. e.g. <code>wiki:kiseki_fandom</code>
|-
| source_url || String || Base URL of source
|-
| trust_tier || Integer || 0 (official) · 1 (JA Wikipedia) · 2 (fan wiki) · 3 (secondary)
|-
| language || String || <code>en</code> or <code>ja</code>
|-
| source_type || String || <code>wiki</code> · <code>official</code> · <code>local</code> · <code>review</code>
|-
| last_fetched_at || String || ISO 8601 timestamp of last sync
|}

{{#cargo_declare:_table=SourceRecord
|source_id=String
|source_url=String
|trust_tier=Integer
|language=String
|source_type=String
|last_fetched_at=String
}}
[[Category:Cargo table templates]]
</noinclude><includeonly>{{#cargo_store:_table=SourceRecord
|source_id={{{source_id|}}}
|source_url={{{source_url|}}}
|trust_tier={{{trust_tier|2}}}
|language={{{language|en}}}
|source_type={{{source_type|wiki}}}
|last_fetched_at={{{last_fetched_at|}}}
}}</includeonly>
"""

# ---- Scribunto module: Character --------------------------------------------

PAGES["Module:Character"] = """\
-- Module:Character
-- Renders character infobox and lead sentence from Cargo data.
-- Called by Template:CharacterInfobox.

local p = {}

local function cargo_fetch(entity_id)
    local results = mw.ext.cargo.query(
        'Character',
        'name_en,name_ja,aliases,arc_first_appearance,spoiler_band,voice_jp,voice_en',
        { where = 'entity_id="' .. entity_id .. '"', limit = 1 }
    )
    if results and #results > 0 then
        return results[1]
    end
    return nil
end

-- Render the infobox table from Cargo data.
function p.infobox(frame)
    local entity_id = frame:getParent().args.entity_id or ''
    if entity_id == '' then
        return '<div class="error">CharacterInfobox: entity_id is required.</div>'
    end

    local row = cargo_fetch(entity_id)
    if not row then
        return '<div class="error">No Cargo record for entity_id: ' .. entity_id .. '</div>'
    end

    local lines = {}
    local function add(label, value)
        if value and value ~= '' then
            lines[#lines+1] = '|-\\n| ' .. label .. ' || ' .. value
        end
    end

    local out = '{| class="wikitable infobox character-infobox" style="float:right;margin:0 0 1em 1em"\\n'
    out = out .. '! colspan="2" style="text-align:center" | ' .. (row.name_en or entity_id) .. '\\n'
    add('Japanese', row.name_ja)
    add('Also known as', row.aliases)
    add('First arc', row.arc_first_appearance)
    add('Voice (JP)', row.voice_jp)
    add('Voice (EN)', row.voice_en)

    for _, line in ipairs(lines) do
        out = out .. line .. '\\n'
    end
    out = out .. '|}\\n'
    return out
end

-- Render the lead sentence from Cargo data.
-- Returns a formatted lead paragraph to open the Atlas entry.
function p.lead(frame)
    local entity_id = frame:getParent().args.entity_id or ''
    if entity_id == '' then return '' end

    local row = cargo_fetch(entity_id)
    if not row then return '' end

    local name = row.name_en or ''
    local arc  = row.arc_first_appearance or ''

    -- Fetch appearance count for this character
    local appearances = mw.ext.cargo.query(
        'Appearance',
        'media_id',
        { where = 'entity_id="' .. entity_id .. '"' }
    )
    local app_count = appearances and #appearances or 0

    local lead = "'''" .. name .. "'''"
    if arc ~= '' then
        lead = lead .. ' is a character in the ' .. arc .. ' arc of the \\'\\'\\'Trails\\'\\'\\'  series'
    else
        lead = lead .. ' is a character in the \\'\\'\\'Trails\\'\\'\\'  series'
    end
    if app_count > 0 then
        lead = lead .. ', appearing across ' .. app_count .. ' registered media entr' .. (app_count == 1 and 'y' or 'ies')
    end
    lead = lead .. '.'
    return lead
end

-- Query and render the appearances list for a character.
function p.appearances(frame)
    local entity_id = frame:getParent().args.entity_id or ''
    if entity_id == '' then return '' end

    local results = mw.ext.cargo.query(
        'Appearance,MediaEntry',
        'MediaEntry.title_en,MediaEntry.arc,Appearance.role,Appearance.spoiler_band',
        {
            join = 'Appearance.media_id=MediaEntry.media_id',
            where = 'Appearance.entity_id="' .. entity_id .. '"',
            orderBy = 'MediaEntry.release_year'
        }
    )

    if not results or #results == 0 then
        return 'No appearances registered.'
    end

    local out = ''
    for _, row in ipairs(results) do
        local title = row['MediaEntry.title_en'] or '?'
        local arc   = row['MediaEntry.arc'] or ''
        local role  = row['Appearance.role'] or ''
        out = out .. '* \\'\\'\\'[[' .. title .. ']]\\'\\'\\'  (' .. arc .. ' arc'
        if role ~= '' and role ~= 'supporting' then
            out = out .. ', ' .. role
        end
        out = out .. ')\\n'
    end
    return out
end

return p
"""

# ---- CharacterInfobox template ----------------------------------------------

PAGES["Template:CharacterInfobox"] = """\
<noinclude>
Renders a character infobox from Cargo data via [[Module:Character]].

Usage:
<pre>{{CharacterInfobox|entity_id=char:estelle_bright}}</pre>

The infobox reads all fields from the Character Cargo table.
No fields need to be passed manually — they are fetched by entity_id.
[[Category:Infobox templates]]
</noinclude><includeonly>{{#invoke:Character|infobox}}</includeonly>
"""

# ---- Page Forms: Character --------------------------------------------------

PAGES["Form:Character"] = """\
<div id="wikiPreview" style="display: none; padding-bottom: 25px; margin-bottom: 25px; border-bottom: 1px solid #AAAAAA;"></div>
{{{for template|CharacterData}}}
{| class="formtable"
! Entity ID (trails.db):
| {{{field|entity_id|input type=text|mandatory}}}
|-
! English name:
| {{{field|name_en|input type=text|mandatory}}}
|-
! Japanese name:
| {{{field|name_ja|input type=text}}}
|-
! Aliases (comma-separated):
| {{{field|aliases|input type=text}}}
|-
! First arc:
| {{{field|arc_first_appearance|input type=dropdown|values=Sky,Crossbell,Erebonia,Reverie,Calvard,Kai}}}
|-
! Spoiler band (0–100):
| {{{field|spoiler_band|input type=text|default=0}}}
|-
! Voice JP:
| {{{field|voice_jp|input type=text}}}
|-
! Voice EN:
| {{{field|voice_en|input type=text}}}
|}
{{{end template}}}

{{{standard input|free text|rows=30|edittools}}}
{{{standard input|summary}}}
{{{standard input|save}}} {{{standard input|preview}}} {{{standard input|changes}}} {{{standard input|cancel}}}
"""

# ---- Example: Estelle Bright ------------------------------------------------

PAGES["Estelle Bright"] = """\
{{CharacterData
|entity_id=char:estelle_bright
|name_en=Estelle Bright
|name_ja=エステル・ブライト
|aliases=
|arc_first_appearance=Sky
|spoiler_band=14
|voice_jp=Kanae Itō
|voice_en=Brittney Karbowski
}}
{{AppearanceData|entity_id=char:estelle_bright|media_id=media:trails_sky_fc|role=protagonist|spoiler_band=10}}
{{AppearanceData|entity_id=char:estelle_bright|media_id=media:trails_sky_sc|role=protagonist|spoiler_band=12}}
{{AppearanceData|entity_id=char:estelle_bright|media_id=media:trails_sky_3rd|role=supporting|spoiler_band=14}}
{{AppearanceData|entity_id=char:estelle_bright|media_id=media:trails_from_zero|role=supporting|spoiler_band=20}}
{{AppearanceData|entity_id=char:estelle_bright|media_id=media:trails_to_azure|role=supporting|spoiler_band=22}}
{{AppearanceData|entity_id=char:estelle_bright|media_id=media:trails_into_reverie|role=supporting|spoiler_band=65}}
{{CharacterInfobox|entity_id=char:estelle_bright}}

{{#invoke:Character|lead|entity_id=char:estelle_bright}}

== Identity & Role ==

Estelle Bright is the protagonist of the ''Sky'' arc. She operates as a junior Bracer in the Liberl Kingdom, initially under the supervision of her father Cassius Bright, and later as a licensed Bracer in her own right. Her affiliation with the Bracer Guild is not incidental — it defines the jurisdictional and moral framework through which she engages every problem the arc presents.

She is a recurring operational contact in subsequent arcs, most significantly during the ''Crossbell'' arc and as a background presence in the ''Erebonia'' arc.

== Chronological History ==

=== Sky Arc ===

<!-- [PROSE SLOT — awaiting curator] -->

=== Crossbell Arc ===

<!-- [PROSE SLOT — awaiting curator] -->

== Affiliations & Relationships ==

* [[Bracer Guild]] — Member (Liberl branch)
* [[Joshua Bright]] — Arc partner; adopted sibling
* [[Cassius Bright]] — Father; mentor

== Appearances ==

{{#invoke:Character|appearances|entity_id=char:estelle_bright}}

== Sources ==

* <code>wiki:kiseki_fandom</code> (trust tier 2)
* <code>wiki:ja_wikipedia_characters</code> (trust tier 1)

[[Category:Character]][[Category:Sky Arc]][[Category:Protagonist]]
"""

# ---- Example: Trails in the Sky FC ------------------------------------------

PAGES["Trails in the Sky FC"] = """\
{{MediaEntryData
|media_id=media:trails_sky_fc
|title_en=Trails in the Sky FC
|title_ja=英雄伝説 空の軌跡 FC
|media_type=game
|arc=Sky
|release_year=2004
|platform=PC|PSP|PS3|Vita
|developer=Nihon Falcom
|publisher=XSEED Games
|spoiler_band=10
}}

'''Trails in the Sky FC''' (''Eiyū Densetsu: Sora no Kiseki FC'') is the first entry in the ''Sky'' arc and the opening title of the ''Trails'' series.

[[Category:Media]][[Category:Sky Arc]][[Category:Game]]
"""

# ---- Source records ---------------------------------------------------------

PAGES["Trails Database:Sources"] = """\
{{SourceRecordData
|source_id=wiki:kiseki_fandom
|source_url=https://kiseki.fandom.com
|trust_tier=2
|language=en
|source_type=wiki
}}
{{SourceRecordData
|source_id=wiki:ja_wikipedia_series
|source_url=https://ja.wikipedia.org/wiki/英雄伝説_軌跡シリーズ
|trust_tier=1
|language=ja
|source_type=wiki
}}
{{SourceRecordData
|source_id=wiki:ja_wikipedia_characters
|source_url=https://ja.wikipedia.org/wiki/英雄伝説_軌跡シリーズの登場人物
|trust_tier=1
|language=ja
|source_type=wiki
}}

This page registers all active ingestion sources for the Trails Database.
Each source record is stored in the Cargo SourceRecord table and mirrors trails.db source_registry.

[[Category:Administration]]
"""


# ---------------------------------------------------------------------------
# Cargo table initialisation via maintenance script
# ---------------------------------------------------------------------------

def recreate_cargo_tables():
    tables = ["MediaEntry", "Character", "Appearance", "SourceRecord"]
    print("\nInitialising Cargo tables via API...")
    token = csrf()
    for table in tables:
        r = SESSION.post(API, data={
            "action": "cargorecreatetables",
            "template": f"{table}Data",
            "format": "json",
            "token": token,
        })
        result = r.json()
        if "error" in result:
            # Fallback: try the recreatecargodata action name variant
            r2 = SESSION.post(API, data={
                "action": "cargorecreatedata",
                "template": f"{table}Data",
                "format": "json",
                "token": token,
            })
            result = r2.json()
        success = "error" not in result
        print(f"  {table}: {'OK' if success else result.get('error', {}).get('info', '?')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Trails Database — Cargo vertical slice setup ===\n")
    login()

    print("\nWriting MediaWiki pages...")
    for title, content in PAGES.items():
        write_page(title, content)

    recreate_cargo_tables()

    print("\n=== Done ===")
    print("Verify at: http://localhost:8080/wiki/Special:CargoTables")
    print("Test page: http://localhost:8080/wiki/Estelle_Bright")


if __name__ == "__main__":
    main()
