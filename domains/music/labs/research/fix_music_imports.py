import os
from pathlib import Path

ROOT = Path(r"C:\Users\dissonance\Desktop\Helix\domains\music")

def fix_imports():
    for root, dirs, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".py"):
                path = Path(root) / f
                content = path.read_text(encoding="utf-8", errors="replace")
                new_content = content.replace("substrates.music.knowledge", "domains.music.atlas_integration")
                new_content = new_content.replace("substrates.music.config", "domains.music.ingestion.config")
                new_content = new_content.replace("substrates.music.db", "domains.music.atlas_integration")
                if new_content != content:
                    print(f"Fixing {path.relative_to(ROOT)}")
                    path.write_text(new_content, encoding="utf-8")

if __name__ == "__main__":
    fix_imports()
