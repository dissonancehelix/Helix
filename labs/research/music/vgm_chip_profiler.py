import os
import gzip
import struct
from pathlib import Path
import json
import re

def parse_vgm_tags(vgm_path):
    """Simple GD3 tag parser for VGM files to identify titles."""
    try:
        if str(vgm_path).endswith('.vgz'):
            with gzip.open(vgm_path, 'rb') as f:
                data = f.read()
        else:
            with open(vgm_path, 'rb') as f:
                data = f.read()
        
        gd3_offset = struct.unpack('<I', data[0x14:0x18])[0] + 0x14
        if data[gd3_offset:gd3_offset+4] != b'Gd3 ':
            return None
        
        # Strings are null-terminated UTF-16LE
        gd3_data = data[gd3_offset+12:]
        strings = []
        pos = 0
        for _ in range(10): # Usually 10-12 strings
            end = gd3_data.find(b'\x00\x00', pos)
            if end == -1: break
            s = gd3_data[pos:end+1].decode('utf-16le', errors='ignore')
            strings.append(s)
            pos = end + 2
        return {"track_name": strings[0] if strings else "Unknown"}
    except:
        return None

def profile_vgm_advanced(vgm_path):
    if str(vgm_path).endswith('.vgz'):
        try:
            with gzip.open(vgm_path, 'rb') as f:
                data = f.read()
        except: return None
    else:
        with open(vgm_path, 'rb') as f:
            data = f.read()

    if data[:4] != b'Vgm ': return None

    header_version = struct.unpack('<I', data[0x08:0x0C])[0]
    data_offset = 0x40
    if header_version >= 0x150:
        data_offset = struct.unpack('<I', data[0x34:0x38])[0] + 0x34

    stats = {
        "fm_writes": 0,
        "psg_writes": 0,
        "dac_writes": 0,
        "algos": [0]*8,
        "feedbacks": [0]*8,
        "total_samples": 0,
        "pcm_blocks": 0,
        "path": str(vgm_path),
        "name": vgm_path.stem
    }

    # Tracking current register states to find the "dominant" algo/fb per channel
    # YM2612 has 6 channels. Algos/FB are in B0-B2 (Port 0: Ch 1-3, Port 1: Ch 4-6)
    pos = data_offset
    while pos < len(data):
        cmd = data[pos]
        if cmd == 0x50: # PSG
            stats["psg_writes"] += 1; pos += 2
        elif cmd in [0x52, 0x53]: # FM
            addr = data[pos+1]
            val = data[pos+2]
            stats["fm_writes"] += 1
            if 0xB0 <= addr <= 0xB2:
                algo = val & 0x07
                fb = (val >> 3) & 0x07
                stats["algos"][algo] += 1
                stats["feedbacks"][fb] += 1
            if addr == 0x2A: stats["dac_writes"] += 1
            pos += 3
        elif cmd == 0x61:
            stats["total_samples"] += struct.unpack('<H', data[pos+1:pos+3])[0]; pos += 3
        elif cmd == 0x62: stats["total_samples"] += 735; pos += 1
        elif cmd == 0x63: stats["total_samples"] += 882; pos += 1
        elif 0x70 <= cmd <= 0x7F: stats["total_samples"] += (cmd & 0x0F) + 1; pos += 1
        elif cmd == 0x67: # Data block
            stats["pcm_blocks"] += 1
            size = struct.unpack('<I', data[pos+3:pos+7])[0]
            pos += 7 + size
        elif 0x80 <= cmd <= 0x8F: stats["dac_writes"] += 1; stats["total_samples"] += (cmd & 0x0F); pos += 1
        elif cmd == 0x66: break
        else: pos += 1
    
    # Normalize Algos
    total_algo_writes = sum(stats["algos"])
    if total_algo_writes > 0:
        stats["algo_dist"] = [round(x/total_algo_writes, 3) for x in stats["algos"]]
    else:
        stats["algo_dist"] = [0]*8
        
    return stats

def run_deep_comparison():
    # Maeda Confirmed Track Filter (Regex/Substrings)
    maeda_targets = {
        "Sonic 3D Blast": [
            "Rusty Ruin", "Diamond Dust", "Volcano Valley", 
            "Gene Gadget", "Panic Puppet Zone Act 2", "Boss 1"
        ],
        "Golden Axe III": [
            "Wilderness", "Thief", "Map", "Boss Even", "Dim Jungle", 
            "Bloody Street", "A Voyage to Castle", "In the Castle", "Last Boss", "Ending"
        ],
        "J League Pro Striker 2": ["*"], 
        "Sonic 3 & Knuckles": [
            "Azure Lake", "Balloon Park", "Desert Palace", 
            "Chrome Gadget", "Endless Mine"
        ]
    }

    results = {"maeda": [], "sst_other": []}
    base_vgm = Path(r"C:\Users\dissonance\Music\VGM")
    
    # Pre-scan for all VGMs to build a global baseline
    print("Building global SST baseline from all Sega consoles...")
    all_vgm = list(base_vgm.rglob("*.v*"))
    for vgm in all_vgm:
        if vgm.suffix not in ['.vgm', '.vgz']: continue
        
        is_maeda = False
        for game, filters in maeda_targets.items():
            if game.lower() in str(vgm).lower():
                if "*" in filters: is_maeda = True
                else:
                    for f in filters:
                        if f.lower() in vgm.name.lower():
                            is_maeda = True
                            break
            if is_maeda: break
            
        profile = profile_vgm_advanced(vgm)
        if profile:
            if is_maeda: results["maeda"].append(profile)
            else: results["sst_other"].append(profile)

    # Save Results
    out_path = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"Global analysis complete. Found {len(results['maeda'])} Maeda tracks and {len(results['sst_other'])} SST baseline tracks.")

    # Save Results
    out_path = Path(r"c:\Users\dissonance\Desktop\Helix\artifacts\reports\maeda_vs_sst_chip.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"Analysis complete. Found {len(results['maeda'])} Maeda tracks and {len(results['sst_other'])} SST tracks.")

if __name__ == "__main__":
    run_deep_comparison()
