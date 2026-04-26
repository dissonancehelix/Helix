"""
APEv2 Tag Reader — Helix Music Lab
=====================================
Parses APEv2 tags from .tag sidecar files (or embedded in VGZ/VGM).
Returns a dict of lowercase key -> string value.

APEv2 format:
  - Header/footer: "APETAGEX" magic + version + size + item count + flags
  - Items: uint32 length + uint32 flags + null-terminated key + value bytes
"""

from __future__ import annotations

import struct
from pathlib import Path


MAGIC = b"APETAGEX"


def _parse_apev2(data: bytes) -> dict[str, str]:
    """Parse APEv2 tag block from raw bytes. Returns {key: value} dict."""
    tags: dict[str, str] = {}

    # Find the APETAGEX header or footer
    pos = data.rfind(MAGIC)
    if pos == -1:
        # Try from start
        pos = data.find(MAGIC)
    if pos == -1:
        return tags

    # Skip magic (8) + version (4) + size (4) + item_count (4) + flags (4) + reserved (8)
    header_start = pos
    if pos + 32 > len(data):
        return tags

    version    = struct.unpack_from("<I", data, pos + 8)[0]
    tag_size   = struct.unpack_from("<I", data, pos + 12)[0]
    item_count = struct.unpack_from("<I", data, pos + 16)[0]
    flags      = struct.unpack_from("<I", data, pos + 20)[0]

    # Determine item block start
    is_header = bool(flags & (1 << 29))
    if is_header:
        item_start = pos + 32
    else:
        # Footer: items are before the footer
        item_start = pos - tag_size + 32
        if item_start < 0:
            item_start = 0

    cur = item_start
    for _ in range(item_count):
        if cur + 8 > len(data):
            break
        val_len  = struct.unpack_from("<I", data, cur)[0]
        item_flags = struct.unpack_from("<I", data, cur + 4)[0]
        cur += 8

        # Read key (null-terminated)
        key_end = data.find(b"\x00", cur)
        if key_end == -1:
            break
        key = data[cur:key_end].decode("utf-8", errors="replace").lower()
        cur = key_end + 1

        # Read value
        val_bytes = data[cur: cur + val_len]
        cur += val_len

        # Type 0 = UTF-8 string
        val_type = (item_flags >> 1) & 0x03
        if val_type == 0:
            tags[key] = val_bytes.decode("utf-8", errors="replace")

    return tags


def read_tag_file(path: Path) -> dict[str, str]:
    """Read a .tag sidecar file or a VGM/VGZ file and return APEv2 tags."""
    try:
        data = path.read_bytes()
        return _parse_apev2(data)
    except Exception:
        return {}


def read_vgz_tags(vgz_path: Path) -> dict[str, str]:
    """Read tags from a .vgz.tag sidecar file if it exists."""
    tag_path = Path(str(vgz_path) + ".tag")
    if tag_path.exists():
        return read_tag_file(tag_path)
    return read_tag_file(vgz_path)
