from bs4 import BeautifulSoup
from pathlib import Path
import re

html_path = Path(r"C:\Users\dissonance\Desktop\temp\Sonic the Hedgehog 3_Development_Music - Sonic Retro.htm")
hil_output = Path(r"C:\Users\dissonance\Desktop\Helix\artifacts\ingest_s3k_metadata.hil")

def parse():
    if not html_path.exists():
        print("S3K Retro file not found.")
        return

    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    commands = []

    # 1. Base entities
    composers = {
        "Michael Jackson": "michael_jackson",
        "Brad Buxer": "brad_buxer",
        "Bobby Brooks": "bobby_brooks",
        "Darryl Ross": "darryl_ross",
        "Geoff Grace": "geoff_grace",
        "Doug Grigsby": "doug_grigsby",
        "Jun Senoue": "jun_senoue",
        "Tatsuyuki Maeda": "tatsuyuki_maeda",
        "Tomonori Sawada": "toni_sawada", # Toni is common alias
        "Masayuki Nagao": "masayuki_nagao",
        "Teruhiko Nakagawa": "teruhiko_nakagawa",
        "Howard Drossin": "howard_drossin"
    }
    
    for name, slug in composers.items():
        commands.append(f"ENTITY add music.composer:{slug} name:\"{name}\" type:Composer")

    commands.append("ENTITY add music.game:sonic_3_and_knuckles name:\"Sonic 3 & Knuckles\" type:Game")

    # 2. Find the per-track tables (there are multiple)
    # They usually have columns: Track / Title / Composer / etc.
    track_count = 0
    for table in soup.find_all("table"):
        headers = [h.get_text(strip=True).lower() for h in table.find_all(["th", "td"])[:10]]
        if any(h in ["title", "track"] for h in headers) and "composer" in str(table).lower():
            rows = table.find_all("tr")
            for row in rows[1:]:
                cols = row.find_all(["td", "th"])
                if len(cols) >= 3:
                    # Heuristic for title
                    title = ""
                    composer_text = ""
                    
                    # Try to find which col is title and which is composer
                    row_text = [c.get_text(strip=True) for c in cols]
                    
                    # Usually Title is the one with text names
                    # Composer is the one with MJ or Buxer
                    for cell in row_text:
                        if any(c in cell for c in composers.keys()):
                            composer_text = cell
                        elif not title and len(cell) > 3 and not cell.isdigit():
                            title = cell
                    
                    if title and title.lower() not in ["title", "track", "credit(s)"]:
                        tid = f"music.track:s3k_{re.sub(r'[^a-z0-9]', '_', title.lower())}"
                        commands.append(f"ENTITY add {tid} name:\"{title}\" type:Track")
                        track_count += 1
                        commands.append(f"ENTITY link {tid} relation:APPEARS_IN target:music.game:sonic_3_and_knuckles")
                        
                        for name, slug in composers.items():
                            if name.lower() in composer_text.lower():
                                commands.append(f"ENTITY link {tid} relation:COMPOSED target:music.composer:{slug}")

    with open(hil_output, "w", encoding="utf-8") as f:
        f.write("\n".join(commands))
    print(f"Generated {len(commands)} HIL commands (found {track_count} tracks) in {hil_output}")

if __name__ == "__main__":
    parse()
