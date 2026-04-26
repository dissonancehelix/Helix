#!/usr/bin/env python3
"""
Fix CharacterData template: move cargo_declare inside noinclude to match
the structure used by working templates (MediaEntryData, SourceRecordData).
Then run setCargoPageData to populate all tables.
"""

import requests
import subprocess

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

def write(title, content, summary="fix"):
    token = csrf()
    r = SESSION.post(API, data={"action": "edit", "title": title,
        "text": content, "summary": summary, "format": "json", "token": token})
    print(title, "->", r.json().get("edit", {}).get("result", "FAIL"))

def purge(title):
    r = SESSION.post(API, data={"action": "purge", "titles": title, "format": "json"})
    print("purge", title, "->", "ok")

login()

# CharacterData: cargo_declare inside noinclude (matching MediaEntryData structure)
CHARACTER_DATA = (
    "<noinclude>\n"
    "Cargo table declaration for Character.\n"
    "Call on each character page to store structured metadata.\n\n"
    "{{#cargo_declare:_table=Character\n"
    "|entity_id=String\n"
    "|name_en=String\n"
    "|name_ja=String\n"
    "|aliases=String\n"
    "|arc_first_appearance=String\n"
    "|spoiler_band=Integer\n"
    "|voice_jp=String\n"
    "|voice_en=String\n"
    "}}\n"
    "[[Category:Cargo table templates]]\n"
    "</noinclude>"
    "<includeonly>{{#cargo_store:_table=Character\n"
    "|entity_id={{{entity_id|}}}\n"
    "|name_en={{{name_en|}}}\n"
    "|name_ja={{{name_ja|}}}\n"
    "|aliases={{{aliases|}}}\n"
    "|arc_first_appearance={{{arc_first_appearance|}}}\n"
    "|spoiler_band={{{spoiler_band|0}}}\n"
    "|voice_jp={{{voice_jp|}}}\n"
    "|voice_en={{{voice_en|}}}\n"
    "}}</includeonly>"
)

write("Template:CharacterData", CHARACTER_DATA, "fix: cargo_declare inside noinclude")

# Purge all data pages to force re-parse and trigger cargo_store
for page in ["Estelle Bright", "Trails in the Sky FC", "Trails Database:Sources"]:
    purge(page)

# Run setCargoPageData
print("\nRunning setCargoPageData...")
result = subprocess.run(
    ["sudo", "-u", "www-data", "php",
     "/var/www/html/wiki/extensions/Cargo/maintenance/setCargoPageData.php"],
    capture_output=True, text=True, timeout=60
)
print(result.stdout[-500:] if result.stdout else "(no output)")
if result.stderr:
    print("stderr:", result.stderr[-200:])
