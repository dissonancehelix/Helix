import os
import json
import sys
from pathlib import Path

# Add repo root to sys.path so we can import apps
repo_root = Path(r"C:\Users\dissonance\Desktop\dissonance")
sys.path.insert(0, str(repo_root))

from apps.games_pipeline.platforms.steam import SteamClient

def main():
    vanity_name = "dissident93"
    print(f"Extracting Steam data for '{vanity_name}'...")
    
    # Helix env uses .env at helix/.env or root. Let's load it if it exists.
    env_path = repo_root / "helix" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("STEAM_API_KEY="):
                os.environ["STEAM_API_KEY"] = line.split("=", 1)[1].strip()

    client = SteamClient()
    if not client.is_authenticated():
        print("Error: STEAM_API_KEY not found in environment.")
        return

    steam_id = client.resolve_vanity(vanity_name)
    if not steam_id:
        print(f"Error: Could not resolve vanity URL '{vanity_name}'.")
        return
        
    print(f"Resolved to SteamID64: {steam_id}")
    
    summary = client.get_summary(steam_id)
    if summary:
        print(f"Found account: {summary.persona_name} (Visibility: {summary.visibility_state})")
    
    games = client.get_owned_games(steam_id)
    print(f"Found {len(games)} owned/played games.")
    
    output = []
    for g in games:
        output.append(g.to_dict())
        
    # Sort by playtime descending
    output.sort(key=lambda x: x["playtime_hours"], reverse=True)
    
    out_dir = repo_root / "data" / "raw" / "games"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"steam_{vanity_name}.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "vanity_name": vanity_name,
            "steam_id": steam_id,
            "account_summary": summary.raw_data if summary else None,
            "games_count": len(output),
            "games": output
        }, f, indent=2)
        
    print(f"Successfully saved to {out_path.relative_to(repo_root)}")

if __name__ == "__main__":
    main()
