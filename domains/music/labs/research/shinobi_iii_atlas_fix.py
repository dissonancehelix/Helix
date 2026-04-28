from pathlib import Path
import json
import re

REGISTRY_PATH = Path(r"C:\Users\dissonance\Desktop\Helix\atlas\entities\registry.json")

def fix_shinobi_iii():
    if not REGISTRY_PATH.exists():
        print("Registry not found.")
        return

    print("Loading registry...")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data["entities"]
    modified = 0
    
    # 1. Ensure composers exist
    composers = {
        "music.composer:morihiko_akiyama": "Morihiko Akiyama",
        "music.composer:hirofumi_murasaki": "Hirofumi Murasaki",
        "music.composer:masayuki_nagao": "Masayuki Nagao"
    }
    
    comp_map = {e["id"]: e for e in entities if e["type"] == "Composer"}
    for cid, name in composers.items():
        if cid not in comp_map:
            new_comp = {
                "id": cid,
                "type": "Composer",
                "name": name,
                "metadata": {"source": "manual_fix", "reason": "shinobi_iii_attribution"},
                "external_ids": {},
                "relationships": []
            }
            entities.append(new_comp)
            comp_map[cid] = new_comp
            print(f"Added composer: {name}")

    # 2. Fix tracks
    for e in entities:
        if e["type"] == "Track":
            source_artifact = e.get("metadata", {}).get("source_artifact", "")
            if "Shinobi III" in source_artifact:
                # Clear existing COMPOSED links to Sega Sound Team or others
                e["relationships"] = [r for r in e["relationships"] if r["relation"] != "COMPOSED"]
                
                if "01 - Shinobi.vgz" in source_artifact:
                    target_comp = "music.composer:masayuki_nagao"
                    e["name"] = "Shinobi (Intro)"
                else:
                    # Attribution to both
                    target_comp = "music.composer:morihiko_akiyama"
                    # We can link to both by adding another relationship later
                
                e["relationships"].append({
                    "relation": "COMPOSED",
                    "target_id": target_comp,
                    "confidence": 1.0
                })
                
                if "01 - Shinobi.vgz" not in source_artifact:
                    e["relationships"].append({
                        "relation": "COMPOSED",
                        "target_id": "music.composer:hirofumi_murasaki",
                        "confidence": 1.0
                    })
                
                modified += 1

    if modified > 0:
        print(f"Modified {modified} Shinobi III tracks.")
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Saved registry.")
    else:
        print("No Shinobi III tracks found to modify.")

if __name__ == "__main__":
    fix_shinobi_iii()
