import gzip
import struct
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

class VGMParser:
    """
    Instruction-level parser for VGM/VGZ (YM2612 focus).
    """
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = self._read_file()
        self.header = self._parse_header()
        
    def _read_file(self) -> bytes:
        if self.file_path.suffix == '.vgz':
            with gzip.open(self.file_path, 'rb') as f:
                return f.read()
        else:
            with open(self.file_path, 'rb') as f:
                return f.read()

    def _parse_header(self) -> Dict[str, Any]:
        h = {}
        # Basic VGM header fields
        h['version'] = struct.unpack('<I', self.data[0x08:0x0C])[0]
        h['vgm_offset'] = struct.unpack('<I', self.data[0x34:0x38])[0] + 0x34
        h['ym2612_clock'] = struct.unpack('<I', self.data[0x2C:0x30])[0]
        h['psg_clock'] = struct.unpack('<I', self.data[0x0C:0x10])[0]
        return h

    def extract_event_stream(self) -> List[Dict[str, Any]]:
        offset = self.header['vgm_offset']
        events = []
        current_sample = 0
        
        while offset < len(self.data):
            cmd = self.data[offset]
            
            if cmd == 0x50: # PSG write
                val = self.data[offset+1]
                events.append({"ts": current_sample, "type": "PSG", "reg": None, "val": val})
                offset += 2
            elif cmd == 0x52: # YM2612 Part 1
                reg = self.data[offset+1]
                val = self.data[offset+2]
                events.append({"ts": current_sample, "type": "YM2612_P1", "reg": reg, "val": val})
                offset += 3
            elif cmd == 0x53: # YM2612 Part 2
                reg = self.data[offset+1]
                val = self.data[offset+2]
                events.append({"ts": current_sample, "type": "YM2612_P2", "reg": reg, "val": val})
                offset += 3
            elif cmd == 0x61: # Wait n samples
                n = struct.unpack('<H', self.data[offset+1:offset+3])[0]
                current_sample += n
                offset += 3
            elif cmd == 0x62: # Wait 735 samples (60Hz)
                current_sample += 735
                offset += 1
            elif cmd == 0x63: # Wait 882 samples (50Hz)
                current_sample += 882
                offset += 1
            elif 0x70 <= cmd <= 0x7F: # Wait n+1 samples
                current_sample += (cmd & 0x0F) + 1
                offset += 1
            elif cmd == 0x67: # Data block
                # Skip 0x66 byte
                size = struct.unpack('<I', self.data[offset+3:offset+7])[0]
                offset += 7 + size
            elif 0x80 <= cmd <= 0x8F: # YM2612 port 0 address 2A write from data bank
                # Logic to wait n samples then write PCM
                current_sample += (cmd & 0x0F)
                offset += 1
            elif cmd == 0x66: # End of data
                break
            elif 0x30 <= cmd <= 0x3F or 0x40 <= cmd <= 0x4E: # Single byte commands
                offset += 2
            elif 0x4F == cmd: # Game Gear PSG stereo
                offset += 2
            elif 0x51 == cmd or 0x54 <= cmd <= 0x5F: # Double byte commands
                offset += 3
            elif 0xA0 <= cmd <= 0xBF: # Double byte commands
                offset += 3
            elif 0xC0 <= cmd <= 0xDF: # Triple byte commands
                offset += 4
            elif 0xE0 <= cmd <= 0xFF: # Quad byte commands
                offset += 5
            else:
                offset += 1
                
        return events

def run_vgm_extraction(track_path: str, output_path: str):
    parser = VGMParser(track_path)
    events = parser.extract_event_stream()
    df = pd.DataFrame(events)
    df.to_parquet(output_path, compression='snappy')
    return len(events)

if __name__ == "__main__":
    # Test on one Sonic 3 track
    test_file = "/mnt/c/Users/dissonance/Music/VGM/S/Sonic 3 & Knuckles/02 - Angel Island Zone Act 1.vgz"
    out = "artifacts/music_lab/event_streams/sonic3_angel_island.parquet"
    if os.path.exists(test_file):
        count = run_vgm_extraction(test_file, out)
        print(f"Extracted {count} events to {out}")
