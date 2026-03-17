"""
adapter_nuked_opn2.py — Helix adapter for Nuked-OPN2 (YM2612 reference)
=========================================================================
Wraps the Nuked-OPN2 constants used in:
    substrates/music/domain_analysis/tool_bridge.py

Purpose:
    Provide YM2612 FM synthesis topology constants (carrier slot tables,
    algorithm → carrier operator mappings) for brightness and timbre
    analysis of Genesis/Mega Drive music.

    Nuked-OPN2 is used as a reference only — no audio rendering.
    It provides the CARRIER_SLOTS table that maps FM algorithm number
    to the set of operator slots that act as audio carriers.

Input:
    algorithm (int)  — YM2612 FM algorithm number (0–7)

Output (dict — chip topology info):
    {
        "algorithm":        int,
        "carrier_slots":    list[int],   # operator slot indices that are carriers
        "modulator_slots":  list[int],   # operator slot indices that are modulators
        "carrier_count":    int,
        "brightness_proxy": float | None,  # mean TL of carrier ops if patch provided
        "adapter":          "nuked_opn2",
    }

Additional call:
    analyze_patch(patch: dict) -> dict   — full patch brightness analysis

Adapter rules:
    • No Helix logic.
    • No audio rendering.
    • Exposes topology constants only.
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# YM2612 carrier slot tables (from Nuked-OPN2 / ym3438.h reference)
# Algorithm → frozenset of operator slot indices that are audio carriers
_CARRIER_SLOTS: dict[int, frozenset[int]] = {
    0: frozenset({3}),          # OP4 only
    1: frozenset({3}),          # OP4 only
    2: frozenset({3}),          # OP4 only
    3: frozenset({3}),          # OP4 only
    4: frozenset({1, 3}),       # OP2 + OP4
    5: frozenset({1, 2, 3}),    # OP2 + OP3 + OP4
    6: frozenset({1, 2, 3}),    # OP2 + OP3 + OP4
    7: frozenset({0, 1, 2, 3}), # all 4 operators
}

_ALL_SLOTS: frozenset[int] = frozenset({0, 1, 2, 3})


class Adapter:
    """
    Adapter exposing Nuked-OPN2 YM2612 topology constants.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → constant tables
    """
    toolkit = "nuked_opn2"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Execute adapter logic for YM2612 FM topologies.
        """
        algorithm = payload.get("algorithm")
        operator_total_levels = payload.get("operator_total_levels")
        
        if algorithm is None:
            raise AdapterError("Payload must contain 'algorithm'")
            
        result = self.analyze_patch(algorithm, operator_total_levels or {})
        return self.normalize(result)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def get_carrier_slots(self, algorithm: int) -> dict[str, Any]:
        """
        Return carrier and modulator slot info for a YM2612 FM algorithm.

        Args:
            algorithm: FM algorithm number (0–7).

        Returns:
            Topology dict with carrier_slots, modulator_slots, carrier_count.
        """
        if algorithm not in _CARRIER_SLOTS:
            raise AdapterError(
                f"Invalid YM2612 algorithm {algorithm!r}. Valid range: 0–7."
            )
        carriers   = _CARRIER_SLOTS[algorithm]
        modulators = _ALL_SLOTS - carriers
        return {
            "algorithm":       algorithm,
            "carrier_slots":   sorted(carriers),
            "modulator_slots": sorted(modulators),
            "carrier_count":   len(carriers),
            "brightness_proxy": None,
            "adapter":         "nuked_opn2",
        }

    def analyze_patch(
        self,
        algorithm: int,
        operator_total_levels: dict[int, int],
    ) -> dict[str, Any]:
        """
        Compute a brightness proxy from a YM2612 FM patch.

        Args:
            algorithm:              FM algorithm number (0–7).
            operator_total_levels:  dict mapping operator index (0–3) → TL value (0–127).
                                    Lower TL = louder / brighter.

        Returns:
            Topology dict with brightness_proxy computed as mean TL of carrier ops.
            brightness_proxy is in [0, 127]; lower = brighter.
        """
        topo = self.get_carrier_slots(algorithm)
        carrier_tls: list[float] = []
        for slot in topo["carrier_slots"]:
            tl = operator_total_levels.get(slot)
            if tl is not None:
                carrier_tls.append(float(tl))

        brightness = sum(carrier_tls) / len(carrier_tls) if carrier_tls else None
        topo["brightness_proxy"] = brightness
        topo["operator_total_levels"] = operator_total_levels
        return topo

    def all_algorithms(self) -> list[dict[str, Any]]:
        """Return topology info for all 8 YM2612 FM algorithms."""
        return [self.get_carrier_slots(alg) for alg in range(8)]

    def is_available(self) -> bool:
        """Nuked-OPN2 adapter is always available — uses static constants."""
        return True
