"""
adapter_nuked_opl3.py — Helix adapter for Nuked-OPL3 (YMF262 reference)
=========================================================================
Wraps the Nuked-OPL3 constants from:
    codex/library/music/source/code/Nuked-OPL3/opl3.c

Purpose:
    Provide OPL3 (YMF262) FM synthesis topology constants for brightness
    and timbre analysis of PC and arcade music using OPL chips (AdLib,
    Sound Blaster, arcade FM boards).

    OPL3 differs structurally from OPN2/OPM:
    - 2-operator channels (OP1, OP2) — the base mode
    - Optional 4-operator pairing of adjacent channels

    The CON register bit determines the routing:
        CON=0: FM mode — OP1 modulates OP2 → OP2 is the sole carrier
        CON=1: AM mode — OP1 and OP2 both output additively (both carriers)

    In 4-op paired mode two CON bits (one per channel pair) combine to form
    four distinct algorithms:
        4op_alg 0 (CON_a=0, CON_b=0): serial FM chain     → carrier = {OP4}
        4op_alg 1 (CON_a=0, CON_b=1): OP3→OP4 + OP1→OP2  → carrier = {OP2, OP4}
        4op_alg 2 (CON_a=1, CON_b=0): OP1→OP2→OP3 + OP4  → carrier = {OP3, OP4}
        4op_alg 3 (CON_a=1, CON_b=1): additive pairs       → carrier = {OP2, OP3, OP4}

OPL3 operator naming:
    2-op: Slot 0 = OP1 (modulator/carrier), Slot 1 = OP2 (carrier)
    4-op: Slot 0 = OP1, Slot 1 = OP2, Slot 2 = OP3, Slot 3 = OP4

Input:
    mode        (str)  — "2op" or "4op"
    con         (int)  — CON bit value (2-op: 0 or 1)
    con_a       (int)  — first channel CON (4-op only)
    con_b       (int)  — second channel CON (4-op only)
    operator_total_levels (dict[int, int])  — slot → TL (0–63)

Output (dict):
    {
        "mode":             "2op" | "4op",
        "carrier_slots":    list[int],
        "modulator_slots":  list[int],
        "carrier_count":    int,
        "brightness_proxy": float | None,
        "chip":             "YMF262",
        "adapter":          "nuked_opl3",
    }

Adapter rules:
    • No Helix logic.
    • No audio rendering.
    • Exposes topology constants only. Always available (Tier A).
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# 2-op carrier slots keyed by CON bit (0 or 1)
_CARRIER_SLOTS_2OP: dict[int, frozenset[int]] = {
    0: frozenset({1}),      # FM: OP2 is carrier only
    1: frozenset({0, 1}),   # AM: both OP1 and OP2 are additive carriers
}

# 4-op carrier slots keyed by (CON_a, CON_b)
# CON_a = CON bit of the first channel pair (OP1-OP2 relationship)
# CON_b = CON bit of the second channel pair (OP3-OP4 relationship)
_CARRIER_SLOTS_4OP: dict[tuple[int, int], frozenset[int]] = {
    (0, 0): frozenset({3}),       # serial chain OP1→OP2→OP3→OP4
    (0, 1): frozenset({1, 3}),    # OP1→OP2 and OP3→OP4 additive
    (1, 0): frozenset({2, 3}),    # OP1→OP2→OP3 and +OP4
    (1, 1): frozenset({1, 2, 3}), # OP1→OP2 additive, OP3, OP4
}

_ALL_SLOTS_2OP: frozenset[int] = frozenset({0, 1})
_ALL_SLOTS_4OP: frozenset[int] = frozenset({0, 1, 2, 3})


class Adapter:
    """
    Adapter exposing Nuked-OPL3 YMF262 topology constants.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → constant tables
    """
    toolkit = "nuked_opl3"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode = payload.get("mode", "2op")
        operator_total_levels = payload.get("operator_total_levels", {})
        if mode == "4op":
            con_a = int(payload.get("con_a", 0))
            con_b = int(payload.get("con_b", 0))
            return self.analyze_patch_4op(con_a, con_b, operator_total_levels)
        else:
            con = int(payload.get("con", 0))
            return self.analyze_patch_2op(con, operator_total_levels)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def get_carrier_slots_2op(self, con: int) -> dict[str, Any]:
        """Return carrier topology for a 2-op OPL3 channel."""
        if con not in _CARRIER_SLOTS_2OP:
            raise AdapterError(f"Invalid OPL3 CON bit {con!r}. Valid: 0 or 1.")
        carriers = _CARRIER_SLOTS_2OP[con]
        modulators = _ALL_SLOTS_2OP - carriers
        return {
            "mode":            "2op",
            "con":             con,
            "carrier_slots":   sorted(carriers),
            "modulator_slots": sorted(modulators),
            "carrier_count":   len(carriers),
            "brightness_proxy": None,
            "chip":            "YMF262",
            "adapter":         "nuked_opl3",
        }

    def get_carrier_slots_4op(self, con_a: int, con_b: int) -> dict[str, Any]:
        """Return carrier topology for a 4-op OPL3 channel pair."""
        key = (int(con_a), int(con_b))
        if key not in _CARRIER_SLOTS_4OP:
            raise AdapterError(
                f"Invalid OPL3 4-op CON pair {key!r}. "
                "Each CON bit must be 0 or 1."
            )
        carriers = _CARRIER_SLOTS_4OP[key]
        modulators = _ALL_SLOTS_4OP - carriers
        return {
            "mode":            "4op",
            "con_a":           con_a,
            "con_b":           con_b,
            "carrier_slots":   sorted(carriers),
            "modulator_slots": sorted(modulators),
            "carrier_count":   len(carriers),
            "brightness_proxy": None,
            "chip":            "YMF262",
            "adapter":         "nuked_opl3",
        }

    def analyze_patch_2op(
        self,
        con: int,
        operator_total_levels: dict[int, int],
    ) -> dict[str, Any]:
        """Compute brightness proxy for a 2-op OPL3 patch. TL range: 0–63."""
        topo = self.get_carrier_slots_2op(con)
        carrier_tls = [
            float(operator_total_levels[s])
            for s in topo["carrier_slots"]
            if s in operator_total_levels
        ]
        topo["brightness_proxy"] = (
            sum(carrier_tls) / len(carrier_tls) if carrier_tls else None
        )
        topo["operator_total_levels"] = operator_total_levels
        return topo

    def analyze_patch_4op(
        self,
        con_a: int,
        con_b: int,
        operator_total_levels: dict[int, int],
    ) -> dict[str, Any]:
        """Compute brightness proxy for a 4-op OPL3 patch. TL range: 0–63."""
        topo = self.get_carrier_slots_4op(con_a, con_b)
        carrier_tls = [
            float(operator_total_levels[s])
            for s in topo["carrier_slots"]
            if s in operator_total_levels
        ]
        topo["brightness_proxy"] = (
            sum(carrier_tls) / len(carrier_tls) if carrier_tls else None
        )
        topo["operator_total_levels"] = operator_total_levels
        return topo

    def all_2op_modes(self) -> list[dict[str, Any]]:
        """Return topology for all 2-op CON modes."""
        return [self.get_carrier_slots_2op(con) for con in (0, 1)]

    def all_4op_modes(self) -> list[dict[str, Any]]:
        """Return topology for all 4-op CON combinations."""
        return [
            self.get_carrier_slots_4op(con_a, con_b)
            for con_a in (0, 1)
            for con_b in (0, 1)
        ]

    def is_available(self) -> bool:
        """Nuked-OPL3 adapter is always available — uses static constants."""
        return True
