"""
adapter_nuked_opm.py — Helix adapter for Nuked-OPM (YM2151 reference)
======================================================================
Wraps the Nuked-OPM constants from:
    domains/music/data/library/source/code/Nuked-OPM/opm.c

Purpose:
    Provide YM2151 FM synthesis topology constants (carrier slot tables,
    algorithm → carrier operator mappings) for brightness and timbre
    analysis of arcade and FM Towns music.

    Nuked-OPM is used as a reference only — no audio rendering.
    It provides the carrier slot mapping derived from the fm_algorithm[4][6][8]
    table in opm.c. The "Out" row (index 5) determines which operator time-slots
    route to the DAC per algorithm.

YM2151 operator naming:
    Slot 0 = M1 (Modulator 1, first in chain)
    Slot 1 = M2 (Modulator 2)
    Slot 2 = C1 (Carrier 1)
    Slot 3 = C2 (Carrier 2, final output in most algorithms)

Source derivation (opm.c fm_algorithm[time_slot][5][alg]):
    time_slot 0 out: {0, 0, 0, 0, 0, 0, 0, 1}  → alg 7 only
    time_slot 1 out: {0, 0, 0, 0, 0, 1, 1, 1}  → alg 5, 6, 7
    time_slot 2 out: {0, 0, 0, 0, 1, 1, 1, 1}  → alg 4, 5, 6, 7
    time_slot 3 out: {1, 1, 1, 1, 1, 1, 1, 1}  → all algorithms

Input:
    algorithm (int)  — YM2151 algorithm number (0–7)

Output (dict):
    {
        "algorithm":        int,
        "carrier_slots":    list[int],   # operator slots that output to DAC
        "modulator_slots":  list[int],   # operator slots that modulate only
        "carrier_count":    int,
        "carrier_names":    list[str],   # human-readable slot names (M1/M2/C1/C2)
        "brightness_proxy": float | None,
        "chip":             "YM2151",
        "adapter":          "nuked_opm",
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


# YM2151 carrier slot tables derived from Nuked-OPM opm.c fm_algorithm[4][6][8]
# "Out" row (dim1=5) — which time-slots route to DAC per algorithm
_CARRIER_SLOTS: dict[int, frozenset[int]] = {
    0: frozenset({3}),          # C2 only
    1: frozenset({3}),          # C2 only
    2: frozenset({3}),          # C2 only
    3: frozenset({3}),          # C2 only
    4: frozenset({2, 3}),       # C1 + C2
    5: frozenset({1, 2, 3}),    # M2 + C1 + C2
    6: frozenset({1, 2, 3}),    # M2 + C1 + C2
    7: frozenset({0, 1, 2, 3}), # M1 + M2 + C1 + C2 (fully additive)
}

_ALL_SLOTS: frozenset[int] = frozenset({0, 1, 2, 3})

_SLOT_NAMES: dict[int, str] = {0: "M1", 1: "M2", 2: "C1", 3: "C2"}


class Adapter:
    """
    Adapter exposing Nuked-OPM YM2151 topology constants.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → constant tables
    """
    toolkit = "nuked_opm"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        algorithm = payload.get("algorithm")
        operator_total_levels = payload.get("operator_total_levels", {})
        if algorithm is None:
            raise AdapterError("Payload must contain 'algorithm'")
        return self.analyze_patch(algorithm, operator_total_levels)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def get_carrier_slots(self, algorithm: int) -> dict[str, Any]:
        """
        Return carrier and modulator slot info for a YM2151 algorithm.

        Args:
            algorithm: FM algorithm number (0–7).

        Returns:
            Topology dict with carrier_slots, modulator_slots, carrier_names.
        """
        if algorithm not in _CARRIER_SLOTS:
            raise AdapterError(
                f"Invalid YM2151 algorithm {algorithm!r}. Valid range: 0–7."
            )
        carriers = _CARRIER_SLOTS[algorithm]
        modulators = _ALL_SLOTS - carriers
        return {
            "algorithm":       algorithm,
            "carrier_slots":   sorted(carriers),
            "modulator_slots": sorted(modulators),
            "carrier_count":   len(carriers),
            "carrier_names":   [_SLOT_NAMES[s] for s in sorted(carriers)],
            "brightness_proxy": None,
            "chip":            "YM2151",
            "adapter":         "nuked_opm",
        }

    def analyze_patch(
        self,
        algorithm: int,
        operator_total_levels: dict[int, int],
    ) -> dict[str, Any]:
        """
        Compute a brightness proxy from a YM2151 FM patch.

        Args:
            algorithm:              FM algorithm number (0–7).
            operator_total_levels:  dict mapping slot index (0–3) → TL value (0–127).
                                    Lower TL = louder / brighter.

        Returns:
            Topology dict with brightness_proxy as mean TL of carrier slots.
            brightness_proxy is in [0, 127]; lower = brighter.
        """
        topo = self.get_carrier_slots(algorithm)
        carrier_tls: list[float] = [
            float(operator_total_levels[s])
            for s in topo["carrier_slots"]
            if s in operator_total_levels
        ]
        topo["brightness_proxy"] = (
            sum(carrier_tls) / len(carrier_tls) if carrier_tls else None
        )
        topo["operator_total_levels"] = operator_total_levels
        return topo

    def all_algorithms(self) -> list[dict[str, Any]]:
        """Return topology info for all 8 YM2151 algorithms."""
        return [self.get_carrier_slots(alg) for alg in range(8)]

    def is_available(self) -> bool:
        """Nuked-OPM adapter is always available — uses static constants."""
        return True
