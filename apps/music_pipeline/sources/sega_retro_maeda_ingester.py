from __future__ import annotations
import logging
import re
from pathlib import Path
from bs4 import BeautifulSoup
from domains.music.atlas_integration.composer_schema import (
    ComposerNode, GameNode, Relationship, TrackNode
)
from domains.music.atlas_integration.composer_graph import (
    ComposerGraph, cid, gid, tid
)

log = logging.getLogger(__name__)

MAEDA_HTML = Path(r"C:\Users\dissonance\Desktop\temp\Tatsuyuki Maeda - Sega Retro.htm")

def ingest_maeda_retro(graph: ComposerGraph):
    if not MAEDA_HTML.exists():
        print(f"File not found: {MAEDA_HTML}")
        return

    html_text = MAEDA_HTML.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html_text, 'html.parser')

    # 1. Ensure Maeda exists
    maeda_id = "tatsuyuki_maeda"
    maeda_node = graph.get_composer(maeda_id)
    if not maeda_node:
        maeda_node = ComposerNode(
            composer_id=maeda_id,
            full_name="Tatsuyuki Maeda",
            aliases=["Johnny Maeda", "Ryunosuke"],
            studios=["Sega"],
            external_ids={"sega_retro": "Tatsuyuki_Maeda"}
        )
        graph.add_composer(maeda_node)

    # 2. Parse "Music (Game)" section
    print("Parsing game credits...")
    games_processed = 0
    
    # 2a. Check for tables (canonical format)
    for table in soup.find_all('table', class_='wikitable'):
        headers = [th.text.strip().lower() for th in table.find_all('th')]
        if 'game' in headers and 'role' in headers:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    game_title = cols[0].text.strip()
                    role = cols[1].text.strip()
                    _add_game_rel(graph, maeda_id, game_title, role)
                    games_processed += 1

    # 2b. Check for H3 headings followed by lists (career section format)
    for h3 in soup.find_all(['h3', 'h4']):
        game_link = h3.find('a')
        if game_link and 'title' in game_link.attrs:
            game_title = game_link.text.strip()
            # Look for roles in the text or next list
            role = "Composer" # Default if in career section
            _add_game_rel(graph, maeda_id, game_title, role)
            games_processed += 1
            
            # Optionally parse tracks in the following <ul>
            next_ul = h3.find_next_sibling('ul')
            if next_ul:
                for li in next_ul.find_all('li'):
                    track_text = li.text.strip()
                    if "—" in track_text:
                        track_name = track_text.split("—")[0].strip()
                        # Add track node if needed (TBD)

    print(f"Seeded {games_processed} games from Sega Retro.")
    return games_processed

def _add_game_rel(graph, composer_id, game_title, role):
    game_slug = game_title.lower().replace(" ", "_").replace("'", "").replace("&", "n")
    game_slug = re.sub(r'[^a-z0-9_]', '', game_slug)
    
    if not graph.get_game(game_slug):
        graph.add_game(GameNode(game_id=game_slug, title=game_title))
    
    graph.relate(cid(composer_id), "worked_on", gid(game_slug), 
                 confidence=1.0, source_name="sega_retro_html", notes=role)

if __name__ == "__main__":
    from domains.music.atlas_integration.composer_graph import get_graph
    g = get_graph()
    ingest_maeda_retro(g)
    g.save(Path(r"c:\Users\dissonance\Desktop\Helix\atlas\entities\music\composer_graph.json"))
