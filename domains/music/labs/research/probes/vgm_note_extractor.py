import struct
import math
import os
import gzip
from pathlib import Path

# Clock for PC Engine (standard NTSC)
VGM_CLOCK_PCE = 3579545

def parse_vgm_pce(file_path):
    """
    Pure Python VGM parser for HuC6280 (PC Engine) note extraction.
    Follows the VGM v1.6x spec for command 0x5B (HuC6280 register write).
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found"}

    # Handle .vgz (gzip compressed)
    try:
        if path.suffix.lower() == ".vgz":
            with gzip.open(path, 'rb') as f:
                data = f.read()
        else:
            with open(path, 'rb') as f:
                data = f.read()
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    # Header check
    if data[0:4] != b'Vgm ':
        return {"error": "Invalid VGM magic"}

    # Data offset (at 0x34)
    data_offset = struct.unpack_from("<I", data, 0x34)[0]
    data_pos = 0x34 + data_offset if data_offset else 0x40
    
    # Track current state of the 6 HuC6280 channels
    channels = [{"freq": 0, "vol": 0, "enable": False, "history": []} for _ in range(6)]
    current_ch = 0
    total_samples = 0
    
    ptr = data_pos
    events = []
    cmd_count = 0
    
    while ptr < len(data):
        cmd = data[ptr]
        if cmd_count < 20: 
            print(f"DEBUG: ptr=0x{ptr:04X} cmd=0x{cmd:02X}")
        cmd_count += 1
        
        if cmd == 0x66: # End of data
            break
        elif cmd == 0x61: # Wait n samples
            count = struct.unpack_from("<H", data, ptr + 1)[0]
            total_samples += count
            ptr += 3
        elif cmd == 0x62: # Wait 735 (1/60s)
            total_samples += 735
            ptr += 1
        elif cmd == 0x63: # Wait 882 (1/50s)
            total_samples += 882
            ptr += 1
        elif 0x70 <= cmd <= 0x7F: # Wait n+1 samples
            total_samples += (cmd & 0x0F) + 1
            ptr += 1
        elif cmd == 0x5B or cmd == 0xB9: # HuC6280 Write (aa dd)
            reg = data[ptr + 1]
            val = data[ptr + 2]
            ptr += 3
            
            # Register logic for HuC6280
            if reg == 0x00: # Select Channel
                current_ch = val & 0x07
            elif reg == 0x02: # Freq Low
                channels[current_ch % 6]["freq"] = (channels[current_ch % 6]["freq"] & 0xF00) | val
            elif reg == 0x03: # Freq High
                old_f = channels[current_ch % 6]["freq"]
                new_f = (old_f & 0x0FF) | ((val & 0x0F) << 8)
                channels[current_ch % 6]["freq"] = new_f
                
                # Note trigger event on frequency change (heuristic)
                if new_f > 0 and new_f != old_f:
                    hz = VGM_CLOCK_PCE / (32 * new_f)
                    midi = 69 + 12 * math.log2(hz / 440.0) if hz > 0 else 0
                    if 12 < midi < 127:
                        events.append({
                            "time_s": total_samples / 44100.0,
                            "ch": current_ch % 6,
                            "hz": hz,
                            "midi": round(midi, 2)
                        })
            elif reg == 0x04: # Control
                channels[current_ch % 6]["enable"] = bool(val & 0x80)
            elif reg == 0x05: # Vol
                channels[current_ch % 6]["vol"] = val & 0x1F
        else:
            # Skip unknown commands based on size
            if 0x30 <= cmd <= 0x3F: ptr += 2
            elif 0x40 <= cmd <= 0x4F: ptr += 2
            elif 0x50 <= cmd <= 0x5F: ptr += 3
            elif 0xA0 <= cmd <= 0xBF: ptr += 3
            elif 0xC0 <= cmd <= 0xDF: ptr += 4
            elif 0xE0 <= cmd <= 0xFF: ptr += 5
            else: ptr += 1

    return events

if __name__ == "__main__":
    vgm_path = r"C:\Users\dissonance\Music\VGM\A\Air Zonk\07 - Mid-Boss.vgz"
    events = parse_vgm_pce(vgm_path)
    
    if "error" in events:
        print(json.dumps(events))
    else:
        # Generate Pitch Histogram for Fingerprinting
        pitches = [e["midi"] for e in events if 24 < e["midi"] < 108]
        histo = {}
        for p in pitches:
            note_name = round(p) % 12
            histo[note_name] = histo.get(note_name, 0) + 1
            
        print(f"Analysis of: {vgm_path}")
        print(f"Events captured: {len(events)}")
        print(f"Key Signature Heuristic (Pitch Distribution): {histo}")
