"""
DCP Collapse Morphology — system/engine/compute/invariants/dcp/morphology.py
===========================================================
Provisional classification of collapse event outcomes.

A collapse morphology describes what happens to a system's trajectory
AFTER a DCP compression event. The categories below are working
classifications — operational, useful for structuring probes and
cross-domain comparison, not settled laws of nature.

These are data definitions only. Detection logic lives in domain hooks.
Classification logic does not exist yet — this module is the schema.

Usage:
    from core.invariants.dcp.morphology import CollapseMorphology, MORPHOLOGY_PROFILES

    label = CollapseMorphology.TRANSFORMATIVE
    profile = MORPHOLOGY_PROFILES[label]
    print(profile.post_collapse_tendency)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CollapseMorphology(str, Enum):
    """
    Provisional collapse morphology categories.

    Each value describes a class of post-collapse trajectory behavior.
    Values are stable identifiers — safe to store in DCPEvent artifacts.
    """

    TRANSFORMATIVE    = "TRANSFORMATIVE"
    """
    Narrowing into stronger / more coherent / more powered structure.
    The post-collapse trajectory is structurally distinct from pre-collapse
    and exhibits greater internal coherence or capability.
    """

    DISSOLUTIVE       = "DISSOLUTIVE"
    """
    Narrowing via thinning, dispersal, breakdown, or coherence loss.
    The post-collapse trajectory lacks the structural stability of the
    pre-collapse state. The system weakens or disperses after commitment.
    """

    CIRCULAR          = "CIRCULAR"
    """
    Narrowing back into a prior stable basin, loop, or origin state.
    The commitment is partial or temporary — the trajectory returns toward
    a pre-existing attractor rather than establishing a new one.
    """

    DEFERRED_SUSPENDED = "DEFERRED_SUSPENDED"
    """
    Approach to narrowing with closure withheld or incompletely realized.
    The system remains in sustained high-tension state near the collapse
    threshold without crossing it. Commitment is delayed or avoided.
    """


@dataclass(frozen=True)
class CollapseProfile:
    """
    Operational description of a collapse morphology category.

    Provides interpretive structure for probe design and post-event
    classification. All fields are provisional operational descriptions,
    not validated laws.
    """

    name:                    str
    description:             str
    pre_collapse_tendency:   str
    """Characteristic pattern in the pre-collapse window."""

    post_collapse_tendency:  str
    """Characteristic trajectory shape in the post-collapse window."""

    coherence_effect:        str
    """What happens to structural coherence / legibility across the event."""

    example_domains:         tuple[str, ...]
    """Domains where this morphology has been observed or hypothesized."""

    notes:                   Optional[str] = None


MORPHOLOGY_PROFILES: dict[CollapseMorphology, CollapseProfile] = {

    CollapseMorphology.TRANSFORMATIVE: CollapseProfile(
        name="Transformative Collapse",
        description=(
            "The system commits to a qualitatively new mode. "
            "Post-collapse trajectory is structurally distinct from pre-collapse "
            "and exhibits greater internal coherence or operational capability."
        ),
        pre_collapse_tendency=(
            "High tension; competing continuation modes; sustained entropy plateau "
            "before sharp narrowing. Possibility-space breadth may oscillate before collapse."
        ),
        post_collapse_tendency=(
            "New stable attractor with lower trajectory diversity than pre-collapse. "
            "Coherence rises; post-collapse variance drops and remains suppressed."
        ),
        coherence_effect=(
            "Coherence increases across the event. The post-collapse state is more "
            "internally consistent than the pre-collapse state."
        ),
        example_domains=("math", "games", "cognition"),
        notes=(
            "Kuramoto K→K_c transition is the canonical math example: "
            "disordered → synchronized, with sharp order-parameter rise and sustained lock."
        ),
    ),

    CollapseMorphology.DISSOLUTIVE: CollapseProfile(
        name="Dissolutive Collapse",
        description=(
            "The system narrows via thinning, dispersal, breakdown, or coherence loss. "
            "Post-collapse trajectory lacks the structural stability of the pre-collapse state."
        ),
        pre_collapse_tendency=(
            "Constraint tightens without tension resolution. "
            "Possibility-space breadth drops without a stable new attractor forming."
        ),
        post_collapse_tendency=(
            "Trajectory destabilizes or disperses. No new coherent structure emerges. "
            "Post-collapse state entropy may increase rather than decrease."
        ),
        coherence_effect=(
            "Coherence decreases across the event. The system is less legible "
            "after commitment than before."
        ),
        example_domains=("games", "cognition"),
        notes=(
            "Hypothesized in games where resource depletion forces commitment "
            "to a losing position. Not yet formally probed."
        ),
    ),

    CollapseMorphology.CIRCULAR: CollapseProfile(
        name="Circular Collapse",
        description=(
            "The system narrows back into a prior stable basin, loop, or origin state. "
            "Commitment is partial or temporary; the trajectory returns toward a "
            "pre-existing attractor."
        ),
        pre_collapse_tendency=(
            "Tension accumulates but does not exceed the threshold required for "
            "a new attractor to form. The system builds toward collapse, then redirects."
        ),
        post_collapse_tendency=(
            "Return to prior state or near-prior state. "
            "Post-collapse trajectory resembles pre-collapse trajectory rather than a new mode."
        ),
        coherence_effect=(
            "Coherence is temporarily disrupted but restored to the prior level. "
            "No net structural change across the event cycle."
        ),
        example_domains=("math", "cognition"),
        notes=(
            "Hypothesized in oscillator systems below K_c: partial synchronization "
            "followed by return to disordered state."
        ),
    ),

    CollapseMorphology.DEFERRED_SUSPENDED: CollapseProfile(
        name="Deferred / Suspended Collapse",
        description=(
            "The system remains in sustained high-tension state near the collapse threshold "
            "without crossing it. Commitment is delayed or avoided indefinitely."
        ),
        pre_collapse_tendency=(
            "Tension rises and is sustained without either resolving into a new trajectory "
            "or dissipating. The system hovers near the collapse boundary."
        ),
        post_collapse_tendency=(
            "No sharp post-collapse state — the 'event' is the sustained suspension itself. "
            "The system may eventually transition to another morphology or return to lower tension."
        ),
        coherence_effect=(
            "Coherence is held at an unstable intermediate level. "
            "Neither the open pre-collapse state nor a new collapsed state is realized."
        ),
        example_domains=("cognition", "games"),
        notes=(
            "Relevant to cognition domain for studying agents in sustained irresolution. "
            "Not yet probed in math or music domains."
        ),
    ),
}


def morphology_from_str(s: str) -> Optional[CollapseMorphology]:
    """
    Convert a string label to a CollapseMorphology value, or None if unrecognized.
    Case-insensitive. Safe for use when loading stored artifact labels.
    """
    try:
        return CollapseMorphology(s.upper())
    except ValueError:
        return None

