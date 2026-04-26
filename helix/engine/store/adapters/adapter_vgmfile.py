"""
adapter_vgmfile.py — Helix adapter for VGM file format (VGMFile.h)
===================================================================
Tier A: Pure Python — no compilation required.
Source reference: domains/music/toolkits/vgmtools/VGMFile.h

Purpose:
    Parse VGM/VGZ binary headers and GD3 embedded tags.
    Read external foobar2000-dialect .tag files.
    Merge metadata with strict priority:

        PRIORITY 1 (canon): external .tag file  (.vgz.tag, .vgm.tag)
        PRIORITY 2 (fallback): GD3 tag embedded in VGM binary

    External .tag fields always overwrite GD3 fields.
    Missing external .tag fields fall back to GD3 values.
    Both sources are preserved separately in output provenance.

Input (payload dict):
    file_path (str | Path)  — path to .vgm or .vgz file

Output (dict):
    {
        "header": {
            "version":        str,     # e.g. "1.70"
            "total_samples":  int,
            "loop_samples":   int,
            "loop_offset":    int,     # byte offset, 0 if no loop
            "rate":           int,     # Hz (50 or 60), 0 if not set
            "chip_clocks":    dict,    # chip_name -> Hz (nonzero only)
            "data_offset":    int,     # absolute byte offset to VGM data
            "gd3_offset":     int,     # absolute byte offset to GD3 block, 0 if absent
        },
        "metadata": {
            "recorded":       dict,    # merged canonical metadata (external > GD3)
            "normalized":     dict,    # slug forms, resolved fields
        },
        "provenance": {
            "external_tag":   dict | None,   # raw fields from .tag file
            "gd3":            dict | None,   # raw fields from GD3 block
            "field_sources":  dict,          # field -> "external_tag" | "gd3" | None
        },
        "adapter": "vgmfile",
    }

Adapter rules:
    • No Helix logic.
    • No audio rendering.
    • Raises AdapterError on unrecoverable parse failures.
"""
from __future__ import annotations

import gzip
import struct
from configparser import RawConfigParser
from io import StringIO
from pathlib import Path
from typing import Any

from core.engine.adapters.adapter_chip_library import ChipLibrary


class AdapterError(Exception):
    """Raised when the adapter cannot process its input."""


# ── VGM header byte offsets (from VGMFile.h / VGM spec 1.71) ─────────────────

# Each entry: (name, offset, format)
# format: 'I' = uint32, 'H' = uint16, 'B' = uint8, 'b' = int8
_HEADER_FIELDS: list[tuple[str, int, str]] = [
    ("fcc_vgm",          0x00, "I"),
    ("eof_offset",       0x04, "I"),
    ("version",          0x08, "I"),
    ("hz_psg",           0x0C, "I"),
    ("hz_ym2413",        0x10, "I"),
    ("gd3_offset",       0x14, "I"),
    ("total_samples",    0x18, "I"),
    ("loop_offset",      0x1C, "I"),
    ("loop_samples",     0x20, "I"),
    ("rate",             0x24, "I"),
    ("psg_feedback",     0x28, "H"),
    ("psg_sr_width",     0x2A, "B"),
    ("psg_flags",        0x2B, "B"),
    ("hz_ym2612",        0x2C, "I"),
    ("hz_ym2151",        0x30, "I"),
    ("data_offset",      0x34, "I"),
    ("hz_segapcm",       0x38, "I"),
    ("hz_rf5c68",        0x40, "I"),
    ("hz_ym2203",        0x44, "I"),
    ("hz_ym2608",        0x48, "I"),
    ("hz_ym2610",        0x4C, "I"),
    ("hz_ym3812",        0x50, "I"),
    ("hz_ym3526",        0x54, "I"),
    ("hz_y8950",         0x58, "I"),
    ("hz_ymf262",        0x5C, "I"),
    ("hz_ymf278b",       0x60, "I"),
    ("hz_ymf271",        0x64, "I"),
    ("hz_ymz280b",       0x68, "I"),
    ("hz_rf5c164",       0x6C, "I"),
    ("hz_pwm",           0x70, "I"),
    ("hz_ay8910",        0x74, "I"),
    ("ay_type",          0x78, "B"),
    ("ay_flag",          0x79, "B"),
    ("volume_modifier",  0x7C, "B"),
    ("loop_base",        0x7E, "b"),
    ("loop_modifier",    0x7F, "B"),
    ("hz_gb_dmg",        0x80, "I"),
    ("hz_nes_apu",       0x84, "I"),
    ("hz_multipcm",      0x88, "I"),
    ("hz_upd7759",       0x8C, "I"),
    ("hz_okim6258",      0x90, "I"),
    ("oki6258_flags",    0x94, "B"),
    ("k054539_flags",    0x95, "B"),
    ("c140_type",        0x96, "B"),
    ("hz_okim6295",      0x98, "I"),
    ("hz_k051649",       0x9C, "I"),
    ("hz_k054539",       0xA0, "I"),
    ("hz_huc6280",       0xA4, "I"),
    ("hz_c140",          0xA8, "I"),
    ("hz_k053260",       0xAC, "I"),
    ("hz_pokey",         0xB0, "I"),
    ("hz_qsound",        0xB4, "I"),
    ("hz_scsp",          0xB8, "I"),
    ("hz_wswan",         0xC0, "I"),
    ("hz_vsu",           0xC4, "I"),
    ("hz_saa1099",       0xC8, "I"),
    ("hz_es5503",        0xCC, "I"),
    ("hz_es5506",        0xD0, "I"),
    ("hz_x1_010",        0xD8, "I"),
    ("hz_c352",          0xDC, "I"),
    ("hz_ga20",          0xE0, "I"),
    ("hz_mikey",         0xE4, "I"),
    ("hz_k007232",       0xE8, "I"),
    ("hz_k005289",       0xEC, "I"),
    ("hz_okim5205",      0xF0, "I"),
]

# Chip clock fields: internal name -> human-readable chip name
_CHIP_CLOCK_MAP: dict[str, str] = {
    "hz_psg":       "SN76489",
    "hz_ym2413":    "YM2413",
    "hz_ym2612":    "YM2612",
    "hz_ym2151":    "YM2151",
    "hz_segapcm":   "SegaPCM",
    "hz_rf5c68":    "RF5C68",
    "hz_ym2203":    "YM2203",
    "hz_ym2608":    "YM2608",
    "hz_ym2610":    "YM2610",
    "hz_ym3812":    "YM3812",
    "hz_ym3526":    "YM3526",
    "hz_y8950":     "Y8950",
    "hz_ymf262":    "YMF262",
    "hz_ymf278b":   "YMF278B",
    "hz_ymf271":    "YMF271",
    "hz_ymz280b":   "YMZ280B",
    "hz_rf5c164":   "RF5C164",
    "hz_pwm":       "PWM",
    "hz_ay8910":    "AY8910",
    "hz_gb_dmg":    "GB_DMG",
    "hz_nes_apu":   "NES_APU",
    "hz_multipcm":  "MultiPCM",
    "hz_upd7759":   "UPD7759",
    "hz_okim6258":  "OKIM6258",
    "hz_okim6295":  "OKIM6295",
    "hz_k051649":   "K051649",
    "hz_k054539":   "K054539",
    "hz_huc6280":   "HuC6280",
    "hz_c140":      "C140",
    "hz_k053260":   "K053260",
    "hz_pokey":     "Pokey",
    "hz_qsound":    "QSound",
    "hz_scsp":      "SCSP",
    "hz_wswan":     "WonderSwan",
    "hz_vsu":       "VSU",
    "hz_saa1099":   "SAA1099",
    "hz_es5503":    "ES5503",
    "hz_es5506":    "ES5506",
    "hz_x1_010":    "X1-010",
    "hz_c352":      "C352",
    "hz_ga20":      "GA20",
    "hz_mikey":     "Mikey",
    "hz_k007232":   "K007232",
    "hz_k005289":   "K005289",
    "hz_okim5205":  "OKIM5205",
}

# GD3 field order (11 null-terminated UTF-16LE strings)
_GD3_FIELDS: list[str] = [
    "track_name_en",
    "track_name_jp",
    "game_name_en",
    "game_name_jp",
    "system_name_en",
    "system_name_jp",
    "author_name_en",
    "author_name_jp",
    "release_date",
    "vgm_creator",
    "notes",
]

# Mapping from GD3 field names to UMO metadata.recorded field names
_GD3_TO_RECORDED: dict[str, str] = {
    "track_name_en": "title",
    "game_name_en":  "album",
    "system_name_en": "platform",
    "author_name_en": "artist",
    "release_date":  "date",
    "notes":         "comment",
}

# Mapping from .tag key (case-insensitive) to UMO metadata.recorded field names
_TAG_KEY_MAP: dict[str, str] = {
    "title":        "title",
    "artist":       "artist",
    "album":        "album",
    "date":         "date",
    "genre":        "genre",
    "featuring":    "featuring",
    "album artist": "album_artist",
    "sound team":   "sound_team",
    "franchise":    "franchise",
    "track number": "track_number",
    "total tracks": "total_tracks",
    "disc number":  "disc_number",
    "total discs":  "total_discs",
    "comment":      "comment",
    "platform":     "platform",
    "sound chip":   "sound_chip",
}

VGM_MAGIC = 0x206D6756   # 'Vgm '
GD3_MAGIC  = 0x20336447  # 'Gd3 '


class Adapter:
    """
    Adapter for VGM binary header parsing, GD3 tag reading, and
    external foobar2000 .tag file parsing with priority merging.

    Tier A — no build required.
    """
    toolkit  = "vgmfile"
    substrate = "music"

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".vgm", ".vgz"})

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        file_path = payload.get("file_path")
        if not file_path:
            raise AdapterError("Payload must contain 'file_path'")
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise AdapterError(f"Unsupported extension: {path.suffix!r}")

        raw = self._read_bytes(path)
        header = self._parse_header(raw)
        gd3    = self._parse_gd3(raw, header)
        ext    = self._read_external_tag(path)
        merged, provenance = self._merge_metadata(ext, gd3)

        return self.normalize(header, merged, provenance)

    def is_available(self) -> bool:
        return True

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _read_bytes(self, path: Path) -> bytes:
        if path.suffix.lower() == ".vgz":
            try:
                with gzip.open(path, "rb") as f:
                    return f.read()
            except Exception as exc:
                raise AdapterError(f"Failed to decompress {path}: {exc}") from exc
        with open(path, "rb") as f:
            return f.read()

    def _parse_header(self, raw: bytes) -> dict[str, Any]:
        if len(raw) < 4:
            raise AdapterError("File too short to be a VGM")
        magic = struct.unpack_from("<I", raw, 0)[0]
        if magic != VGM_MAGIC:
            raise AdapterError(
                f"Not a VGM file — magic 0x{magic:08X} != 0x{VGM_MAGIC:08X}"
            )

        fields: dict[str, Any] = {}
        for name, offset, fmt in _HEADER_FIELDS:
            size = struct.calcsize(f"<{fmt}")
            if offset + size > len(raw):
                break
            (val,) = struct.unpack_from(f"<{fmt}", raw, offset)
            fields[name] = val

        # Version: 0x00IIJJ → "I.JJ" string
        ver_raw = fields.get("version", 0)
        major = (ver_raw >> 8) & 0xFF
        minor = ver_raw & 0xFF
        version_str = f"{major}.{minor:02d}"

        # GD3 offset is relative to 0x14; 0 means absent
        gd3_rel = fields.get("gd3_offset", 0)
        gd3_abs = (0x14 + gd3_rel) if gd3_rel else 0

        # Data offset: relative to 0x34; default 0x0C for v1.00 files
        data_rel = fields.get("data_offset", 0)
        data_abs = (0x34 + data_rel) if data_rel else 0x40

        # Loop offset: relative to 0x1C; 0 means no loop
        loop_rel = fields.get("loop_offset", 0)
        loop_abs = (0x1C + loop_rel) if loop_rel else 0

        # Collect nonzero chip clocks
        chip_clocks: dict[str, int] = {}
        for field_name, chip_name in _CHIP_CLOCK_MAP.items():
            hz = fields.get(field_name, 0)
            # High bit set = second chip instance; mask it to get clock
            if hz:
                chip_clocks[chip_name] = hz & 0x3FFFFFFF

        return {
            "version":       version_str,
            "total_samples": fields.get("total_samples", 0),
            "loop_samples":  fields.get("loop_samples",  0),
            "loop_offset":   loop_abs,
            "rate":          fields.get("rate", 0),
            "chip_clocks":   chip_clocks,
            "data_offset":   data_abs,
            "gd3_offset":    gd3_abs,
            "psg_feedback":  fields.get("psg_feedback", 0),
            "psg_sr_width":  fields.get("psg_sr_width", 0),
            "volume_modifier": fields.get("volume_modifier", 0),
            "loop_modifier": fields.get("loop_modifier", 0),
        }

    def _parse_gd3(self, raw: bytes, header: dict[str, Any]) -> dict[str, str] | None:
        gd3_abs = header.get("gd3_offset", 0)
        if not gd3_abs or gd3_abs >= len(raw):
            return None

        try:
            magic = struct.unpack_from("<I", raw, gd3_abs)[0]
            if magic != GD3_MAGIC:
                return None
            # version at +4, tag_length at +8
            tag_length = struct.unpack_from("<I", raw, gd3_abs + 8)[0]
            data_start  = gd3_abs + 12
            data_end    = data_start + tag_length
            tag_bytes   = raw[data_start:data_end]
        except struct.error:
            return None

        # Decode: 11 null-terminated UTF-16LE strings
        strings: list[str] = []
        pos = 0
        while len(strings) < len(_GD3_FIELDS) and pos < len(tag_bytes):
            end = tag_bytes.find(b"\x00\x00", pos)
            # align to 2-byte boundary for UTF-16
            if end == -1:
                chunk = tag_bytes[pos:]
                pos = len(tag_bytes)
            else:
                # ensure null terminator is at even offset
                if (end - pos) % 2 != 0:
                    end += 1
                chunk = tag_bytes[pos:end]
                pos = end + 2
            try:
                strings.append(chunk.decode("utf-16-le", errors="replace").strip())
            except Exception:
                strings.append("")

        return {
            field: strings[i] if i < len(strings) else ""
            for i, field in enumerate(_GD3_FIELDS)
        }

    def _read_external_tag(self, vgm_path: Path) -> dict[str, str] | None:
        """
        Look for a foobar2000-dialect .tag sidecar file.
        Candidates: <file>.tag, <file.vgz>.tag, <stem>.tag
        Returns dict of {key: value} or None if no tag file found.
        """
        candidates = [
            vgm_path.parent / (vgm_path.name + ".tag"),
            vgm_path.with_suffix(".tag"),
        ]
        for tag_path in candidates:
            if tag_path.exists():
                return self._parse_tag_file(tag_path)
        return None

    def _parse_tag_file(self, tag_path: Path) -> dict[str, str]:
        """Parse foobar2000 INI-style .tag file. Returns {key: value}."""
        try:
            text = tag_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise AdapterError(f"Cannot read tag file {tag_path}: {exc}") from exc

        # foobar2000 .tag files are INI-like but have no section header
        # Inject a dummy section so RawConfigParser can handle them
        ini_text = "[tag]\n" + text
        cfg = RawConfigParser(strict=False)
        cfg.optionxform = str   # preserve key case
        try:
            cfg.read_file(StringIO(ini_text))
        except Exception:
            # Fallback: manual line parse
            result: dict[str, str] = {}
            for line in text.splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    result[k.strip()] = v.strip()
            return result

        return dict(cfg.items("tag"))

    # ── Metadata merging ──────────────────────────────────────────────────────

    def _merge_metadata(
        self,
        ext: dict[str, str] | None,
        gd3: dict[str, str] | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Merge external .tag and GD3 into UMO metadata.recorded dict.
        External .tag wins on all conflicts. GD3 fills gaps.
        Returns (recorded_dict, provenance_dict).
        """
        recorded: dict[str, Any] = {}
        field_sources: dict[str, str] = {}

        # --- Layer 1: GD3 (lower priority) ---
        if gd3:
            for gd3_field, rec_field in _GD3_TO_RECORDED.items():
                val = gd3.get(gd3_field, "").strip()
                if val:
                    recorded[rec_field] = val
                    field_sources[rec_field] = "gd3"

        # --- Layer 2: external .tag (overrides GD3) ---
        if ext:
            for raw_key, raw_val in ext.items():
                key_lower = raw_key.lower()
                rec_field = _TAG_KEY_MAP.get(key_lower)
                if rec_field is None:
                    continue
                val = raw_val.strip()
                if not val:
                    continue
                # Integer coercion for numeric fields
                if rec_field in ("track_number", "total_tracks", "disc_number", "total_discs"):
                    try:
                        val = int(val)
                    except ValueError:
                        continue
                recorded[rec_field] = val
                field_sources[rec_field] = "external_tag"

        provenance = {
            "external_tag":  ext,
            "gd3":           gd3,
            "field_sources": field_sources,
        }
        return recorded, provenance

    # ── Normalization ─────────────────────────────────────────────────────────

    def normalize(
        self,
        header: dict[str, Any],
        recorded: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        # Slug form of title if present
        title = recorded.get("title", "")
        if title:
            import re
            normalized["title_slug"] = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")

        # --- Automated Library Enrichment ---
        # For each chip in the header, look up its full library specs
        chip_details: dict[str, Any] = {}
        for chip_name, clock in header.get("chip_clocks", {}).items():
            # Standardize names for lookup
            lookup_key = chip_name.lower().replace(" ", "_").replace("-", "_")
            # Special case for SN76489 (it's often 'PSG' in VGM headers)
            if lookup_key == "sn76489": lookup_key = "sn76489"
            
            detail = ChipLibrary.get_chip(lookup_key)
            if detail:
                chip_details[chip_name] = {
                    "id": detail.get("id"),
                    "architecture": detail.get("properties", {}).get("architecture"),
                    "hardware": detail.get("properties", {}).get("hardware"),
                    "analysis_notes": detail.get("properties", {}).get("analysis_notes"),
                    "invariant_links": detail.get("properties", {}).get("invariant_links")
                }

        return {
            "header":   header,
            "chip_library_enrichment": chip_details,
            "metadata": {
                "recorded":   recorded,
                "normalized": normalized,
            },
            "provenance": provenance,
            "adapter":    "vgmfile",
        }
