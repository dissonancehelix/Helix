"""
ROM deep scan — finds ALL printable ASCII strings + SMPS structural markers.
Usage: python tools/rom_deep_scan.py <rom.md>
"""
import sys
import re
from pathlib import Path

def extract_strings(data: bytes, min_len: int = 4) -> list[tuple[int, str]]:
    """Extract all printable ASCII runs >= min_len bytes."""
    results = []
    pattern = re.compile(rb'[ -~]{' + str(min_len).encode() + rb',}')
    for m in pattern.finditer(data):
        results.append((m.start(), m.group().decode('ascii', errors='replace')))
    return results

def find_smps_pointers(data: bytes) -> list[tuple[int, int]]:
    """
    SMPS song tables store big-endian 16-bit or 32-bit pointers.
    Look for runs of valid ROM-range addresses (0x000000 - 0x3FFFFF for 4MB ROM).
    Returns offset, value pairs.
    """
    rom_size = len(data)
    results = []
    # Look for repeated pairs of bytes that look like word-aligned addresses
    for i in range(0, rom_size - 4, 2):
        # Big-endian 16-bit (SMPS Z80 uses 16-bit offsets into sound bank)
        val = (data[i] << 8) | data[i+1]
        if 0x0100 < val < 0x7FFF:
            # Check the 4 bytes around it for similar values (pointer table pattern)
            prev = (data[i-2] << 8) | data[i-1] if i >= 2 else 0
            nxt  = (data[i+2] << 8) | data[i+3] if i+4 < rom_size else 0
            if prev and abs(val - prev) < 0x0200 and abs(nxt - val) < 0x0200:
                results.append((i, val))
    return results

def scan_rom(rom_path: Path):
    data = rom_path.read_bytes()
    size_kb = len(data) // 1024
    print(f"\n{'='*60}")
    print(f"ROM: {rom_path.name}  ({size_kb} KB)")
    print(f"{'='*60}")

    # 1. All ASCII strings
    strings = extract_strings(data, min_len=5)
    print(f"\n[ASCII STRINGS - {len(strings)} found]\n")
    
    # Filter to interesting ones (sound/music/author/copyright related)
    sound_kw = re.compile(r'sound|music|song|bgm|sfx|seq|track|comp|arrang|author|ver|'
                          r'sega|sonic|nakam|senou|nagao|hikic|takao|setsum|dross|maeda|buxer|'
                          r'copyright|\(c\)|smps|gems|driver|z80|fm|psg|ym|adsr|voice|patch|'
                          r'level|zone|stage|act|demo|data|bank|tbl|table|hdr|header|init|'
                          r'sub|call|jump|loop|end|start|main|game', re.IGNORECASE)
    
    interesting = [(off, s) for off, s in strings if sound_kw.search(s)]
    generic     = [(off, s) for off, s in strings if not sound_kw.search(s) and len(s) >= 8]

    if interesting:
        print("  == SOUND/MUSIC/AUTHOR RELATED ==")
        for off, s in interesting[:100]:
            print(f"  0x{off:06X}: {s[:80]}")

    if generic:
        print(f"\n  == OTHER STRINGS (>= 8 chars) ==")
        for off, s in generic[:80]:
            print(f"  0x{off:06X}: {s[:80]}")

    # 2. Look for Sonic 3D Blast-style "Song by" pattern as raw bytes  
    # The 3D Blast pattern used DC.B directives with 0x3F ('?') as separator
    print(f"\n[SMPS CREDIT BYTE PATTERN SEARCH]")
    # Search for 0x3F (?) surrounded by printable chars
    for i in range(1, len(data)-10):
        if data[i] == 0x3F and 0x20 <= data[i-1] < 0x7F and 0x20 <= data[i+1] < 0x7F:
            ctx = data[max(0,i-20):i+20]
            txt = ''.join(chr(b) if 0x20 <= b < 0x7F else '.' for b in ctx)
            if any(c.isalpha() for c in txt[10:]):
                print(f"  0x{i:06X} [?-pattern]: {txt}")

    # 3. ROM header info (Mega Drive standard header at 0x100-0x200)
    print(f"\n[MEGA DRIVE ROM HEADER]")
    header_fields = [
        (0x100, 16, "System type"),
        (0x110, 16, "Copyright"),
        (0x120, 48, "Domestic title"),
        (0x150, 48, "International title"),
        (0x198, 8,  "Serial number"),
        (0x1A0, 3,  "ROM version"),
    ]
    for off, length, label in header_fields:
        raw = data[off:off+length]
        txt = ''.join(chr(b) if 0x20 <= b < 0x7F else '.' for b in raw).strip()
        print(f"  {label}: {txt}")

    # 4. Count how many unique byte sequences appear near sound-ID positions
    # In SMPS, the Z80 sound driver is loaded from a known area; look for Z80 init pattern
    print(f"\n[Z80 SOUND CPU MARKER SEARCH]")
    # Z80 reset vector pattern often starts with 0xF3 (DI), 0xED, 0x56 or 0xC3 (JP)
    z80_markers = [bytes([0xF3, 0xED, 0x56]), bytes([0xF3, 0xC3]), bytes([0xF3, 0x31])]
    for marker in z80_markers:
        idx = data.find(marker)
        if idx >= 0:
            ctx = data[idx:idx+32].hex(' ')
            print(f"  0x{idx:06X} Z80 pattern {marker.hex()}: {ctx}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/rom_deep_scan.py <rom1.md> [rom2.md ...]")
        sys.exit(1)
    for path in sys.argv[1:]:
        scan_rom(Path(path))
