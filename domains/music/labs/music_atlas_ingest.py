import json
import os
import re
from pathlib import Path

ATLAS_ENTITIES = Path(r"c:\Users\dissonance\Desktop\Helix\atlas\entities\music")
COMPOSER_REGISTRY = Path(r"c:\Users\dissonance\Desktop\Helix\atlas\entities\composers.json")
CHIP_REPORT = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")

def read_ape_tag(path):
    tag_path = Path(str(path) + ".tag")
    if not tag_path.exists(): return None
    try:
        with open(tag_path, "rb") as f:
            data = f.read()
            # Find Title, Artist, Album strings
            import re
            strings = re.findall(b"[\x20-\x7E]{4,}", data)
            decoded = [s.decode('ascii', errors='ignore') for s in strings]
            meta = {}
            for i, s in enumerate(decoded):
                if s == "Title": meta["title"] = decoded[i+1]
                if s == "Artist": meta["artist"] = decoded[i+1]
                if s == "Album": meta["album"] = decoded[i+1]
                if s == "Year": meta["year"] = decoded[i+1]
                if s == "Track": meta["track_num"] = decoded[i+1]
            return meta
    except: return None

def ingest():
    print("Ingesting Music Atlas (Stream Mode)...")
    
    # 1. Seeding Composers
    composers = {
        "Tatsuyuki Maeda": {"type": "Composer", "aliases": ["Johnny Maeda", "Ryunosuke"]},
        "Masayuki Nagao": {"type": "Composer", "aliases": ["N.GEE"]},
        "Morihiko Akiyama": {"type": "Composer"},
        "Hirofumi Murasaki": {"type": "Composer"}
    }

    # 2. Open and stream the report data
    with open(CHIP_REPORT, "r") as f:
        data = json.load(f)

    # Process Maeda first (High Priority)
    for group in ["maeda", "sst_other"]:
        print(f"  Ingesting {group}...")
        for t in data[group]:
            vgm_path = Path(t["path"])
            canon_meta = read_ape_tag(vgm_path) or {}
            
            # Default
            final_artist = canon_meta.get("artist", "Sega Sound Team")
            
            # Shinobi III Overrides
            if "Shinobi III" in str(vgm_path):
                if "01 - Shinobi" in t["name"]:
                    final_artist = "Masayuki Nagao"
                else:
                    final_artist = "Morihiko Akiyama / Hirofumi Murasaki"

            track_id = t["name"].lower().replace(" ", "_")
            track_id = re.sub(r'[^a-z0-9_]', '', track_id)
            entity_path = ATLAS_ENTITIES / f"{track_id}.json"
            
            entity = {
                "entity_id": track_id,
                "track_name": t.get("name", "Unknown"),
                "album": canon_meta.get("album", "Unknown"),
                "composer": final_artist,
                "year": canon_meta.get("year", "Unknown"),
                "track_order": canon_meta.get("track_num", "0"),
                "chip_data": {
                    "complexity": sum(t["algo_dist"][4:7]) if "algo_dist" in t else 0
                },
                "_type": "music:track"
            }
            
            # We only write if it's high value or specific override
            # To avoid writing 26k individual files unless requested.
            # We'll write the ones with a clear composer attribution.
            if final_artist != "Sega Sound Team":
                with open(entity_path, "w") as f_out:
                    json.dump(entity, f_out, indent=4)

    # Save Composer Registry
    with open(COMPOSER_REGISTRY, "w") as f_reg:
        json.dump(composers, f_reg, indent=4)

    print("Knowledge Ingestion Complete.")

if __name__ == "__main__":
    ingest()
