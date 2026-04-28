"""
promote_stubs.py -- Promote artist stubs from Phase 6 materialization into codex atlas.
"""
import json
import re
from pathlib import Path

MATERIALIZATION_JSON = Path(r"C:\Users\dissonance\Desktop\Helix\applications\labs\datasets\music\phase6\artist_entity_materialization.json")
CODEX_ARTIST_DIR = Path(r"C:\Users\dissonance\Desktop\Helix\codex\library\music\artist")

def slugify(text: str) -> str:
    slug = re.sub(r"[^\w]+", "_", text.strip()).strip("_")
    return slug

def promote_stubs():
    if not MATERIALIZATION_JSON.exists():
        print(f"File not found: {MATERIALIZATION_JSON}")
        return

    with open(MATERIALIZATION_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        records = data.get("records", [])

    promoted_count = 0
    
    # We want to promote stubs that are "high-confidence" or have sufficient signal
    for rec in records:
        if rec.get("status") != "stub_candidate":
            continue
            
        # Promotion criteria
        confidence = rec.get("confidence", 0.0)
        loved_count = rec.get("loved_track_count", 0)
        plays = rec.get("total_evidence_plays", 0)
        if confidence < 0.6 and loved_count == 0 and plays < 20:
            continue
            
        # Construct slug
        name = rec.get("credited_form", rec.get("normalized_key", ""))
        slug = slugify(rec.get("normalized_key", name))
        if not slug:
            continue
            
        entity_id = f"music.artist.{slug}"
        out_path = CODEX_ARTIST_DIR / f"{slug}.json"
        
        # Determine relationships if any from the record (not natively in Phase 6 materialization, but we can structure the record)
        entity = {
          "id": entity_id,
          "type": "Artist",
          "name": name.title() if name else "",
          "metadata": {
            "canonical_name": name.title() if name else "",
            "track_count": rec.get("track_count", 0),
            "loved_track_count": loved_count,
            "origin_confidence": confidence
          },
          "analysis": {},
          "relationships": []
        }
        
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump(entity, out, indent=2)
            
        promoted_count += 1

    print(f"Successfully promoted {promoted_count} artist stubs to {CODEX_ARTIST_DIR}")

if __name__ == "__main__":
    promote_stubs()
