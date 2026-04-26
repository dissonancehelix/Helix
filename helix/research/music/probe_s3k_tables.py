from bs4 import BeautifulSoup
from pathlib import Path

html_path = Path(r"C:\Users\dissonance\Desktop\temp\Sonic the Hedgehog 3_Development_Music - Sonic Retro.htm")

def probe():
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    for i, table in enumerate(soup.find_all("table")):
        text = table.get_text().lower()
        if "michael jackson" in text:
            print(f"MATCH FOUND: Table {i}")
            rows = table.find_all("tr")
            for r in rows[:5]:
                cells = r.find_all(["th", "td"])
                print(f"  {[c.get_text(strip=True) for c in cells]}")
            # return # Don't return, find all matching tables

if __name__ == "__main__":
    probe()
