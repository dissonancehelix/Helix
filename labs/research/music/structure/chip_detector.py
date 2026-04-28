import struct
from pathlib import Path
from typing import Dict, Any, List

class VGMChipDetector:
    """
    Detects sound chips and basic metadata from VGM headers.
    Following VGM Specification 1.72.
    """
    
    CHIP_MAP = {
        0x0C: "SN76489",
        0x10: "YM2413",
        0x2C: "YM2612",
        0x30: "YM2151",
        0x44: "YM2203",
        0x48: "YM2608",
        0x4C: "YM2610",
        0x50: "YM3812",
        0x54: "YM3526",
        0x58: "Y8950",
        0x5C: "YMF262",
        0x60: "YMF278B",
        0x64: "YMF271",
        0x68: "YMZ280B",
        0x6C: "RF5C64",
        0x70: "PWM",
        0x74: "AY8910",
        0x80: "GameBoy DMG",
        0x84: "NES APU",
        0x88: "MultiPCM",
        0x8C: "uPD7759",
        0x90: "OKIM6295",
        0x94: "K051649",
        0x98: "K054539",
        0x9C: "HuC6280",
        0xA0: "C140",
        0xA4: "K053260",
        0xA8: "Pokey",
        0xAC: "QSound",
        0xB0: "SCSP",
        0xB4: "WSwan",
        0xB8: "VSU",
        0xBC: "SAA1099",
        0xC0: "ES5503",
        0xC4: "ES5505",
        0xC8: "X1-010",
        0xCC: "C352",
        0xD0: "GA20",
    }

    def __init__(self, data: bytes):
        self.data = data

    def detect_chips(self) -> List[Dict[str, Any]]:
        chips = []
        if len(self.data) < 0x40:
            return chips

        for offset, name in self.CHIP_MAP.items():
            if offset + 4 > len(self.data):
                continue
            
            clock = struct.unpack('<I', self.data[offset:offset+4])[0]
            if clock > 0:
                # Bit 31 indicates dual chip if set (except for some specific chips)
                dual = bool(clock & 0x40000000)
                actual_clock = clock & 0x3FFFFFFF
                
                chips.append({
                    "chip": name,
                    "clock": actual_clock,
                    "dual": dual
                })
        
        return chips

    def get_duration_samples(self) -> int:
        if len(self.data) < 0x20:
            return 0
        return struct.unpack('<I', self.data[0x18:0x1C])[0]

    def get_vgm_version(self) -> str:
        if len(self.data) < 0x0C:
            return "0.00"
        v = struct.unpack('<I', self.data[0x08:0x0C])[0]
        return f"{(v >> 8) & 0xFF}.{(v & 0xFF):02x}"
