#!/usr/bin/env python3
"""Update Module:Character with pcall-wrapped Cargo queries to prevent transaction rollback."""

import requests

API = "http://localhost:8080/api.php"
SESSION = requests.Session()

def login():
    r = SESSION.get(API, params={"action": "query", "meta": "tokens", "type": "login", "format": "json"})
    token = r.json()["query"]["tokens"]["logintoken"]
    SESSION.post(API, data={"action": "login", "format": "json",
        "lgname": "WikiAdmin", "lgpassword": "WikiAdmin2026!", "lgtoken": token})

def csrf():
    r = SESSION.get(API, params={"action": "query", "meta": "tokens", "format": "json"})
    return r.json()["query"]["tokens"]["csrftoken"]

def write(title, content, summary=""):
    token = csrf()
    r = SESSION.post(API, data={"action": "edit", "title": title,
        "text": content, "summary": summary, "format": "json", "token": token})
    print(title, "->", r.json().get("edit", {}).get("result", "FAIL"))

login()

MODULE_CHARACTER = r"""-- Module:Character
-- Renders character infobox and lead from Cargo data.
-- All Cargo queries wrapped in pcall to prevent transaction rollback on error.

local p = {}

local function safe_cargo(tbl, fields, opts)
    local ok, result = pcall(mw.ext.cargo.query, tbl, fields, opts or {})
    if ok and result then return result end
    return {}
end

local function fetch_char(entity_id)
    local rows = safe_cargo('Character',
        'name_en,name_ja,aliases,arc_first_appearance,spoiler_band,voice_jp,voice_en',
        { where = 'entity_id="' .. entity_id .. '"', limit = 1 })
    return rows[1] or nil
end

function p.infobox(frame)
    local entity_id = (frame:getParent().args.entity_id or ''):gsub('^%s*(.-)%s*$', '%1')
    if entity_id == '' then
        return '<div class="error">CharacterInfobox: entity_id required.</div>'
    end
    local row = fetch_char(entity_id)
    if not row then
        return '<!-- no Cargo record for ' .. entity_id .. ' -->'
    end

    local out = '{| class="wikitable infobox" style="float:right;margin:0 0 1em 1em"\n'
    out = out .. '! colspan="2" | ' .. (row.name_en or entity_id) .. '\n'
    local function add(label, val)
        if val and val ~= '' then
            out = out .. '|-\n| ' .. label .. ' || ' .. val .. '\n'
        end
    end
    add('Japanese', row.name_ja)
    add('Also known as', row.aliases)
    add('First arc', row.arc_first_appearance)
    add('Voice (JP)', row.voice_jp)
    add('Voice (EN)', row.voice_en)
    out = out .. '|}\n'
    return out
end

function p.lead(frame)
    local entity_id = (frame:getParent().args.entity_id or ''):gsub('^%s*(.-)%s*$', '%1')
    if entity_id == '' then return '' end
    local row = fetch_char(entity_id)
    if not row then return '' end
    local name = row.name_en or ''
    local arc  = row.arc_first_appearance or ''
    local lead = "'''" .. name .. "'''"
    if arc ~= '' then
        lead = lead .. " is a character in the " .. arc .. " arc of the ''Trails'' series"
    else
        lead = lead .. " is a character in the ''Trails'' series"
    end
    return lead .. '.'
end

function p.appearances(frame)
    local entity_id = (frame:getParent().args.entity_id or ''):gsub('^%s*(.-)%s*$', '%1')
    if entity_id == '' then return '' end
    local results = safe_cargo('Appearance,MediaEntry',
        'MediaEntry.title_en,MediaEntry.arc,Appearance.role,Appearance.spoiler_band',
        {
            join = 'Appearance.media_id=MediaEntry.media_id',
            where = 'Appearance.entity_id="' .. entity_id .. '"',
            orderBy = 'MediaEntry.release_year'
        })
    if #results == 0 then
        return 'No appearances registered.'
    end
    local out = ''
    for _, row in ipairs(results) do
        local title = row['MediaEntry.title_en'] or '?'
        local arc   = row['MediaEntry.arc'] or ''
        local role  = row['Appearance.role'] or ''
        out = out .. "* '[[" .. title .. "]]' (" .. arc .. ' arc'
        if role ~= '' and role ~= 'supporting' then
            out = out .. ', ' .. role
        end
        out = out .. ')\n'
    end
    return out
end

return p
"""

write("Module:Character", MODULE_CHARACTER, "pcall-wrap all cargo queries to prevent tx rollback")
