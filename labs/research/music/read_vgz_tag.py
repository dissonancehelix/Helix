import os
from pathlib import Path

def read_tag_raw(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
            # Simple heuristic: Look for text strings in the binary tag file
            # APEv2 tags often have field names and values as ASCII/UTF8
            import re
            strings = re.findall(b"[\x20-\x7E]{4,}", data)
            return [s.decode('ascii', errors='ignore') for s in strings]
    except Exception as e:
        return str(e)

path = r"C:\Users\dissonance\Music\VGM\S\Shinobi III\12 - Whirlwind.vgz.tag"
print(f"--- Raw strings in {path} ---")
print(read_tag_raw(path))
