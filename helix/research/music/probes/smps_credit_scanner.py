"""
SMPS ROM Credit Scanner — tools/smps_credit_scanner.py
=======================================================
Searches a Mega Drive ROM binary for embedded SMPS-style composer credits.

The Sonic 3D Blast (Genesis) ROM contains credits in the SMPS sound bank in
the format:
    "Song by J.Seno. ? Arrange by J.Seno."

This script scans any MD ROM for the same pattern. If Sonic 3 or Sonic &
Knuckles has equivalent credits stored in their SMPS tables, this will find them.

Usage:
    python tools/smps_credit_scanner.py "path/to/sonic3.bin"
    python tools/smps_credit_scanner.py "path/to/sonic_and_knuckles.bin"
    python tools/smps_credit_scanner.py "path/to/sonicandknuckles.bin" --dump-hex

The script will print any found credit strings with their ROM offset.
"""

import argparse
import sys
from pathlib import Path


# Known abbreviations from Sonic 3D Blast
_KNOWN_COMPOSERS = {
    "J.Seno.":    "Jun Senoue",
    "T.Maeda":    "Tatsuyuki Maeda",
    "M.Sets.":    "Masaru Setsumaru",
    "H.Drossin.": "Howard Drossin",
    "Y.Makino":   "Yukifumi Makino",
    "S.Okamoto":  "S. Okamoto",
    # Potential S3K-specific credits (unknown until found)
    "M.Nagao":    "Masayuki Nagao",
    "M.Hikichi":  "Masanori Hikichi",
    "M.Takaoka":  "Miyoko Takaoka",
    "B.Buxer":    "Brad Buxer",
    "J.Kashima":  "Yoshiaki Kashima",
}

_SEARCH_PATTERNS = [
    b"Song by",
    b"song by",
    b"SONG BY",
    b"Arrange by",
    b"arrange by",
    b"Composed by",
    b"composed by",
]


def scan_rom(rom_path: Path, dump_hex: bool = False) -> list[dict]:
    """
    Scan a ROM binary for embedded SMPS composer credit strings.
    Returns list of found entries with offset, raw string, and parsed info.
    """
    data = rom_path.read_bytes()
    results = []
    seen_offsets = set()

    for pattern in _SEARCH_PATTERNS:
        offset = 0
        while True:
            idx = data.find(pattern, offset)
            if idx == -1:
                break

            # Grab up to 120 bytes from this offset for context
            window_start = max(0, idx - 8)
            window_end   = min(len(data), idx + 120)
            window = data[window_start:window_end]

            # Extract printable ASCII run
            credit_str = ""
            for i, b in enumerate(data[idx:idx + 100]):
                if 0x20 <= b < 0x7F or b in (0x09, 0x00):
                    credit_str += chr(b) if b != 0x00 else " "
                elif b == 0x0A or b == 0x0D:
                    credit_str += "\n"
                else:
                    if len(credit_str) > 6:
                        break
                    credit_str = ""  # reset if garbage early

            credit_str = credit_str.strip()
            if not credit_str or idx in seen_offsets:
                offset = idx + 1
                continue

            seen_offsets.add(idx)

            # Identify composers mentioned
            identified = []
            for abbrev, full_name in _KNOWN_COMPOSERS.items():
                if abbrev in credit_str:
                    identified.append(full_name)

            entry = {
                "offset_hex": f"0x{idx:06X}",
                "offset_dec": idx,
                "raw":        credit_str[:100].replace("\n", " "),
                "identified": identified,
            }
            results.append(entry)
            print(f"  [{entry['offset_hex']}] {entry['raw']}")
            if identified:
                print(f"            → {', '.join(identified)}")
            if dump_hex:
                hex_str = " ".join(f"{b:02X}" for b in data[window_start:window_end])
                print(f"            HEX: {hex_str}")

            offset = idx + 1

    return results


def main():
    ap = argparse.ArgumentParser(
        description="Scan a Mega Drive ROM for embedded SMPS composer credits."
    )
    ap.add_argument("rom", help="Path to ROM (.bin, .md, .smd, .gen)")
    ap.add_argument("--dump-hex", action="store_true",
                    help="Also print hex dump around each match")
    ap.add_argument("--out", default=None,
                    help="Output file for results (JSON)")
    args = ap.parse_args()

    rom_path = Path(args.rom)
    if not rom_path.exists():
        print(f"ERROR: ROM not found: {rom_path}")
        sys.exit(1)

    print(f"\nScanning: {rom_path.name}  ({rom_path.stat().st_size / 1024:.0f} KB)")
    print("-" * 60)

    results = scan_rom(rom_path, dump_hex=args.dump_hex)

    print(f"\nFound {len(results)} credit string(s).")

    if args.out and results:
        import json
        out = Path(args.out)
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Saved to: {out}")

    if not results:
        print("\nNo embedded credit strings found.")
        print("This may mean:")
        print("  - The ROM uses a different SMPS variant without embedded credits")
        print("  - Credits are stored in a compressed format")
        print("  - The credit block is at an unexpected location")
        print("\nTry: python tools/smps_credit_scanner.py <rom> --dump-hex")
        print("     to see raw bytes around any partial matches.")


if __name__ == "__main__":
    main()
