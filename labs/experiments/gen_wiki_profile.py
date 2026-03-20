import json
from pathlib import Path
from datetime import datetime

ATLAS_DIR = Path(r"c:\Users\dissonance\Desktop\Helix\atlas\entities")
ENTITIES_DIR = ATLAS_DIR / "music"
TEMPLATE_PATH = Path(r"c:\Users\dissonance\Desktop\Helix\governance\templates\entity\ENTITY_TEMPLATE.md")

def generate_wiki():
    # 1. Load Composer Meta
    composer_file = ATLAS_DIR / "composers.json"
    if not composer_file.exists(): return
    with open(composer_file, "r") as f:
        composers = json.load(f)

    maeda = composers.get("Tatsuyuki Maeda")
    
    # 2. Find all tracks attributed to him in the Atlas
    confirmed_tracks = []
    attributed_tracks = []
    
    for p in ENTITIES_DIR.glob("*.json"):
        with open(p, "r") as f:
            data = json.load(f)
            if data.get("composer") == "Tatsuyuki Maeda":
                confirmed_tracks.append(data.get("track_name"))
            elif data.get("attributed_to") == "Tatsuyuki Maeda":
                attributed_tracks.append((data.get("track_name"), data.get("attribution_confidence")))

    # 3. Format Wiki Page (Markdown)
    wiki_content = f"""# COMPOSER PROFILE: Tatsuyuki Maeda
Status: Atlas Verified
Last Updated: {datetime.now().strftime('%Y-%m-%d')}

## 1. IDENTITY & ALIASES
* **Core ID**: Tatsuyuki Maeda
* **Aliases**: {", ".join(maeda['aliases'])}
* **Associations**: Sega Sound Team, Wave Master

## 2. SONIC SIGNATURE (INVARIANTS)
* **Signature Type**: Chip Complexity
* **Characteristic**: {maeda['style_signature']}
* **Confidence**: High (Based on J-League 2 and Sonic 3D Baseline)

## 3. CONFIRMED WORKS (ENTITY LIST)
{chr(10).join([f"* {t}" for t in sorted(list(set(confirmed_tracks)))])}

## 4. STYLE ATTRIBUTIONS (PROBABILISTIC)
*These tracks are credited to 'Sega Sound Team' but match the Maeda Complexity Signature:*
{chr(10).join([f"* {t} (Confidence: {c*100:.0f}%)" for t, c in sorted(attributed_tracks, key=lambda x: x[1], reverse=True)])}

## 5. REPOSITORY LINKS
* [Atlas Graph Entry](file:///c:/Users/dissonance/Desktop/Helix/codex/atlas/entities/composers.json)
* [Analysis Report](file:///c:/Users/dissonance/Desktop/Helix/artifacts/reports/maeda_vs_sst_chip.json)
"""

    out_path = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_wiki_profile.md")
    with open(out_path, "w") as f:
        f.write(wiki_content)

    print(f"Wiki profile generated at {out_path}")

if __name__ == "__main__":
    generate_wiki()
