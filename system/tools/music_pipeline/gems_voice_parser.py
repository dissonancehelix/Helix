import json
import re
from pathlib import Path

def parse_gems_patch_bank(bank_path: Path) -> dict:
    """
    Parses a GEMS PATCH.BNK file and extracts the 80-byte chunk instruments.
    Returns a dictionary mapping the Patch Name to its raw hex payload.
    """
    data = bank_path.read_bytes()
    
    # Locate all 80-byte blocks starting with `<` (e.g., `<Untitled>`)
    # The first patch typically starts at header offset, we just use regex to find all < strings padded by 0!
    
    patches = {}
    
    # We locate all string boundaries that look like GEMS names: <Name> padded with \x00
    # Actually, we know patches are 80 bytes. If we find the first <, we can just stride by 80.
    first_idx = data.find(b'<')
    if first_idx == -1:
        return patches
        
    idx = first_idx
    patch_id = 0
    while idx + 80 <= len(data):
        chunk = data[idx:idx+80]
        
        # Extract name (null terminated or out to 16 bytes)
        null_pos = chunk.find(b'\x00')
        if null_pos != -1:
            name_bytes = chunk[:null_pos]
        else:
            name_bytes = chunk[:16]
            
        try:
            name = name_bytes.decode('ascii', errors='ignore').strip()
        except:
            name = f"Patch_{patch_id}"
            
        if not name:
            name = f"Unknown_{patch_id}"
            
        # We store the raw 80-byte chunk so we can extract the FM / PSG parameters later!
        patches[f"{patch_id:03d}_{name}"] = chunk.hex()
        
        idx += 80
        patch_id += 1
        
    return patches


def build_gems_library(gems_dir: Path, output_json: Path):
    """
    Finds all PATCH.BNK files in the GEMS directory, parses them,
    and consolidates them into a single Helix derived-data JSON.
    """
    all_patches = {}
    
    for bnk_path in gems_dir.rglob("PATCH.BNK"):
        print(f"Parsing {bnk_path}...")
        bank_patches = parse_gems_patch_bank(bnk_path)
        
        # Store under the relative path name to avoid collisions
        bank_name = bnk_path.parent.name
        for name, hex_data in bank_patches.items():
            key = f"{bank_name}::{name}"
            all_patches[key] = {
                "name": name,
                "driver": "GEMS",
                "source_bank": bank_name,
                "hex_data": hex_data,
                "chunk_length_bytes": len(hex_data) // 2
            }
            
    # Write to derived data.
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open('w') as f:
        json.dump(all_patches, f, indent=2)
        
    print(f"Extracted {len(all_patches)} GEMS patches -> {output_json}")
    return all_patches


if __name__ == "__main__":
    gems_root = Path("C:/Users/dissonance/Downloads/GEMS")
    output = Path(__file__).resolve().parents[3] / "data" / "derived" / "music_pipeline" / "gems_voice_library.json"
    build_gems_library(gems_root, output)
