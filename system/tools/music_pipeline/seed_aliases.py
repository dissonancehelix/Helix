"""
seed_aliases.py -- Seed Japanese/Romaji/English aliases for codex artists via VGMDB.
"""
import json
import time
from pathlib import Path
from model.domains.music.atlas_integration.sources.vgmdb_ingester import fetch_artist, search_artist

CODEX_ARTIST_DIR = Path(r"C:\Users\dissonance\Desktop\Helix\codex\library\music\artist")

def seed_aliases():
    # Only seed for artists with high track counts or loved counts which were recently promoted
    for json_file in CODEX_ARTIST_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Skip if already enriched
        if data.get("metadata", {}).get("vgmdb_id"):
            continue
            
        name = data.get("name")
        if not name or name == "Unknown Artist":
            continue
            
        print(f"Searching VGMDB for {name}...")
        results = search_artist(name)
        if not results:
            continue
            
        # Take the first best match
        best_match = results[0]
        vgmdb_id = best_match["vgmdb_id"]
        
        print(f"Found match: {best_match['name']} ({vgmdb_id}). Fetching full profile...")
        profile = fetch_artist(vgmdb_id)
        
        if profile:
            # Update data
            data["metadata"]["vgmdb_id"] = vgmdb_id
            data["metadata"]["canonical_name"] = profile["full_name"]
            
            # Combine aliases
            existing_aliases = set(data.setdefault("aliases", []))
            new_aliases = set(profile.get("aliases", []))
            data["aliases"] = list(existing_aliases | new_aliases)
            
            # Add websites
            data["metadata"]["websites"] = profile.get("websites", {})
            
            with open(json_file, "w", encoding="utf-8") as out:
                json.dump(data, out, indent=2, ensure_ascii=False)
            
            print(f"Enriched {name} with {len(profile.get('aliases', []))} aliases.")
        
        # Polite delay
        time.sleep(1.0)

if __name__ == "__main__":
    # Note: This is an expensive operation if run on all 2225 artists.
    # Recommended to run on a subset or manually for high-priority artists.
    print("Seeding aliases for codex artists...")
    seed_aliases()

