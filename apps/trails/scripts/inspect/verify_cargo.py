#!/usr/bin/env python3
import requests

API = 'http://localhost:8080/api.php'

tests = [
    ('Characters in Calvard arc', {
        'tables': 'Character',
        'fields': 'name_en,arc_first_appearance',
        'where': 'arc_first_appearance="Calvard arc"',
        'limit': '5',
    }),
    ('Van Arkride appearances', {
        'tables': 'Appearance',
        'fields': 'entity_id,media_id,role',
        'where': 'entity_id="char:van_arkride"',
    }),
    ('Main game media entries', {
        'tables': 'MediaEntry',
        'fields': 'media_id,title_en,arc,release_year',
        'where': 'media_type="main_game"',
        'limit': '5',
    }),
    ('Quest sample', {
        'tables': 'Entity',
        'fields': 'entity_id,name_en',
        'where': 'entity_type="quest"',
        'limit': '3',
    }),
    ('Factions sample', {
        'tables': 'Faction',
        'fields': 'entity_id,name_en',
        'limit': '3',
    }),
    ('Locations sample', {
        'tables': 'Location',
        'fields': 'entity_id,name_en',
        'limit': '3',
    }),
    ('Agnes Claudel (accented)', {
        'tables': 'Character',
        'fields': 'entity_id,name_en',
        'where': 'name_en LIKE "agn%"',
    }),
]

for label, params in tests:
    params['action'] = 'cargoquery'
    params['format'] = 'json'
    r = requests.get(API, params=params)
    data = r.json().get('cargoquery', [])
    print(f"\n[{label}]")
    for row in data:
        print(' ', row['title'])
    if not data:
        print('  (no results)')
