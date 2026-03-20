import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from domains.music.db.track_db import TrackDB
from domains.music.config import DB_PATH

def run(subcommand: str = "tracks", **params):
    db = TrackDB(DB_PATH)
    print(f"--- LIST {subcommand} ---")
    
    if subcommand == "tracks":
        composer = params.get("composer")
        if composer:
            # Simple LIKE query for listing
            with db._conn() as conn:
                rows = conn.execute("SELECT artist, title, album FROM tracks WHERE artist LIKE ?", (f"%{composer}%",)).fetchall()
            tracks = [dict(r) for r in rows]
        else:
            tracks = db.get_tracks_by_tier(max_tier=1)
        
        for t in tracks[:50]:
            print(f"  {t.get('artist')} - {t.get('title')} ({t.get('album')})")
        
        if len(tracks) > 50:
            print(f"  ... and {len(tracks) - 50} more")
            
        return {"status": "ok", "count": len(tracks)}
        
    elif subcommand == "composers":
        with db._conn() as conn:
            rows = conn.execute("SELECT DISTINCT artist FROM tracks WHERE artist IS NOT NULL ORDER BY artist").fetchall()
        composers = [r[0] for r in rows if r[0]]
        for c in composers:
            print(f"  {c}")
        return {"status": "ok", "count": len(composers)}
        
    elif subcommand == "franchises":
         with db._conn() as conn:
            rows = conn.execute("SELECT DISTINCT franchise FROM tracks WHERE franchise IS NOT NULL ORDER BY franchise").fetchall()
         franchises = [r[0] for r in rows if r[0]]
         for f in franchises:
            print(f"  {f}")
         return {"status": "ok", "count": len(franchises)}

    return {"status": "error", "message": f"Unknown LIST subcommand: {subcommand}"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("subcommand", nargs="?", default="tracks")
    args, unknown = parser.parse_known_args()
    
    # Simple k:v param parser for CLI testing
    params = {}
    for arg in unknown:
        if ":" in arg:
            k, v = arg.split(":", 1)
            params[k] = v
            
    run(args.subcommand, **params)
