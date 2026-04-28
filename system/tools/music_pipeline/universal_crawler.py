import json
import time
from pathlib import Path
import sys

HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
sys.path.append(str(HELIX_ROOT / "model/domains/music/ingestion"))

from ign_artwork_downloader import resolve_artwork, download_artwork, is_ign_placeholder

LIBRARY_CATEGORY_ROOT = Path("C:/Users/dissonance/Music/VGM/A")
CODEX_ALBUMS = HELIX_ROOT / "codex/library/music/album"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def rename_folder_images(folder: Path):
    """Rename folder.webp -> cover.webp and folder.jpg -> cover.jpg if no cover exists."""
    webp_src = folder / "folder.webp"
    if webp_src.exists():
        webp_src.rename(folder / "cover.webp")
        print(f"  [RENAME] folder.webp -> cover.webp")

    jpg_src = folder / "folder.jpg"
    cover = folder / "cover.jpg"
    if jpg_src.exists() and not cover.exists():
        jpg_src.rename(cover)
        print(f"  [RENAME] folder.jpg -> cover.jpg")


def purge_non_canonical(folder: Path):
    """Removes all image files except cover.jpg and cover.webp."""
    for f in folder.iterdir():
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
            if f.name not in ("cover.jpg", "cover.webp"):
                try:
                    f.unlink()
                    print(f"  [CLEAN] Purged: {f.name}")
                except Exception as e:
                    print(f"  [ERROR] Could not purge {f.name}: {e}")


def update_codex_visual(folder_name: str, source: str, resolution: list):
    album_id = folder_name.lower().replace(" ", "_").replace(".", "_")
    codex_path = CODEX_ALBUMS / album_id
    if not (codex_path / "album.json").exists():
        return False
    try:
        with open(codex_path / "album.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        data["visual"] = {
            "canonical_path": "cover.jpg",
            "current_status": "repaired_digital_autonomous",
            "resolution": resolution,
            "is_square": True,
            "branding_clean": source == "ign",
            "source_type": source,
            "is_digital_native": source in ("ign", "vgmdb", "musicbrainz_caa"),
            "note": f"Autonomous crawler acquisition from {source}.",
        }
        with open(codex_path / "album.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def run_universal_crawler(category_path: Path):
    print(f"--- Universal Crawler Launch: {category_path} ---")
    folders = [f for f in category_path.iterdir() if f.is_dir()]
    print(f"Found {len(folders)} candidate folders.")

    success_count = 0
    for folder in folders:
        game_name = folder.name
        print(f"Crawling: {game_name}...")

        # Always rename folder.webp first (independent of download outcome)
        rename_folder_images(folder)

        art_url, source = resolve_artwork(game_name)
        if not art_url:
            print(f"  [FAIL] No source found.")
            continue

        dest_path = folder / "cover.jpg"
        if download_artwork(art_url, dest_path):
            # Reject IGN placeholders and retry without IGN
            if source == "ign" and is_ign_placeholder(dest_path):
                print(f"  [PLACEHOLDER] IGN served placeholder, falling back...")
                dest_path.unlink(missing_ok=True)
                from ign_artwork_downloader import resolve_vgmdb_artwork, resolve_sega_retro_artwork, download_artwork as dl
                fallback_url = resolve_vgmdb_artwork(game_name) or resolve_sega_retro_artwork(game_name)
                if fallback_url and dl(fallback_url, dest_path):
                    source = "vgmdb_or_sega_retro_fallback"
                    print(f"  [OK] Fallback art acquired.")
                else:
                    print(f"  [FAIL] Fallback also failed.")
                    continue

            print(f"  [OK] Art acquired from {source}.")
            purge_non_canonical(folder)
            update_codex_visual(game_name, source, [1000, 1000])
            success_count += 1
            time.sleep(0.5)
        else:
            print(f"  [FAIL] Download failed.")

    print(f"\nCrawl Batch Complete. Success: {success_count}/{len(folders)}")


if __name__ == "__main__":
    run_universal_crawler(LIBRARY_CATEGORY_ROOT)

