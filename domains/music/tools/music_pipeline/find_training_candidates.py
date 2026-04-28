import os
import sqlite3
from pathlib import Path
from domains.music.tools.music_pipeline.metadata_processor import MetadataProcessor
from domains.music.tools.music_pipeline.config import VGM_ROOT, LIBRARY_ROOT

TARGET_COMPOSERS = {
    "Jun Senoue", "Tatsuyuki Maeda", "Sachio Ogawa", 
    "Masayuki Nagao", "Tomonori Sawada"
}

def find_candidates():
    scan_paths = [VGM_ROOT]
    meta = MetadataProcessor(LIBRARY_ROOT)
    
    found = {c: [] for c in TARGET_COMPOSERS}
    count = 0
    
    print(f"Scanning {VGM_ROOT} for target composers...")
    for root in scan_paths:
        for p in root.rglob("*"):
            if not p.is_file(): continue
            if p.suffix.lower() not in ['.vgm', '.vgz', '.spc', '.nsf', '.sid']: continue
            
            # Fast check filename/path first
            path_str = str(p)
            for composer in TARGET_COMPOSERS:
                if composer.lower() in path_str.lower():
                    found[composer].append(p)
                    break
            
            count += 1
            if count % 1000 == 0:
                print(f"  Processed {count} files...")
            
            if all(len(v) >= 100 for v in found.values()):
                break
                
    for c, files in found.items():
        print(f"{c}: {len(files)} candidates found")
    
    return found

if __name__ == "__main__":
    find_candidates()

