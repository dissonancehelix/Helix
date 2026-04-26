import os
import re
from pathlib import Path

def find_maeda():
    dir_path = Path(r"C:\Users\dissonance\Music\VGM\S\Shinobi III")
    for p in dir_path.glob("*.vgz.tag"):
        with open(p, "rb") as f:
            data = f.read()
            if b"Maeda" in data:
                print(f"FOUND MAEDA IN: {p.name}")
                strings = re.findall(b"[\x20-\x7E]{4,}", data)
                print([s.decode('ascii', errors='ignore') for s in strings])

if __name__ == "__main__":
    find_maeda()
