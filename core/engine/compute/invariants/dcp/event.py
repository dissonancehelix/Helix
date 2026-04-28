"""
DCP Event Schema — core/invariants/dcp/event.py
================================================
Structural representation of a Decision Compression event.

A DCPEvent is the unit of evidence for a compression claim.
It captures the five required components of a DCP-like event
in a domain-agnostic format that can be produced by any domain hook.

This is a data structure, not a detection algorithm.
Detection logic lives in domain-specific hooks (see core/probes/math/analysis/dcp.py).
Metric computation lives in core/invariants/dcp/metrics.py.

Design rules:
- All fields that carry "proxy" values are domain-specific measurements
  that have been mapped to this canonical format by the domain hook.
- Fields marked Optional are permitted to be None; they reduce confidence
  but do not invalidate the event.
- confidence is set by the domain hook; it is a provisional estimate,
  not a validated score.
- schema_version must be bumped if fields are added/removed/renamed.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import json

SCHEMA_VERSION = "dcp_event_v2"
# v2: added collapse_morphology, constraint_class fields; added DCPProbeOutput


@dataclass
class DCPEvent:
    """
    A single Decision Compression event observation.

    Produced by a domain hook after analyzing a simulation, replay log,
    or other source artifact.
    """

    # --- Identity / Provenance ---
    source_domain: str
    """Domain that produced this event: 'math', 'games', 'music', 'language'"""

    source_artifact: str
    """Path or ID of the source artifact (replay log, simulation run, track ID, etc.)"""

    event_id: Optional[str] = None
    """Optional short identifier for this event (e.g. 'kuramoto-K2.0-n50-s42-lock')"""

    # --- Five DCP Components (all domain-specific proxies) ---

    possibility_space_proxy: Optional[float] = None
    """
    Breadth of reachable futures BEFORE the compression event.
    Higher = more open. Range: [0.0, 1.0] recommended (normalized).
    Example: normalized phase variance (math), policy entropy (games),
             interval entropy (music).
    """

    constraint_proxy: Optional[float] = None
    """
    Strength of the acting constraint relative to system capacity.
    Higher = stronger constraint. Range: [0.0, 1.0] recommended.
    Example: K/K_c ratio (math), resource utilization (games),
             register saturation (music).
    """

    tension_proxy: Optional[float] = None
    """
    Pre-collapse unresolved competition.
    Higher = more tension before event. Range: [0.0, 1.0] recommended.
    Example: order-parameter variance peak before lock (math),
             strategy entropy plateau duration (games).
    None is acceptable if tension is not observable in this domain/event.
    """

    collapse_proxy: Optional[float] = None
    """
    Sharpness of the compression event. Higher = sharper collapse.
    Range: [0.0, 1.0] recommended (normalized rate).
    Example: d(sync_index)/dt at lock (math), d(policy_entropy)/dt at commit (games).
    """

    post_collapse_narrowing: Optional[float] = None
    """
    Reduction in trajectory diversity after the collapse.
    Higher = more narrowing (more compression). Range: [0.0, 1.0].
    Example: 1 - post_lock_phase_variance (math),
             1 - viable_strategy_ratio_post_commit (games).
    """

    # --- Collapse Morphology ---
    collapse_morphology: Optional[str] = None
    """
    Post-collapse trajectory class. Use values from CollapseMorphology enum:
        'TRANSFORMATIVE' | 'DISSOLUTIVE' | 'CIRCULAR' | 'DEFERRED_SUSPENDED'
    None if morphology has not been classified.
    See: core/engine/compute/invariants/dcp/morphology.py
    """

    constraint_class: Optional[str] = None
    """
    Class of the acting constraint:
        'internal'  — structural / self-imposed (resource limits, rule sets)
        'external'  — applied from outside (adversarial action, coupling from other agents)
        'mixed'     — both internal and external constraints active simultaneously
    None if constraint class has not been identified.
    """

    # --- Confidence and Calibration ---
    confidence: float = 0.0
    """
    Provisional confidence score for this compression classification.
    Set by the domain hook. Not validated against null baseline until
    a calibration run is performed.
    Range: [0.0, 1.0].
    """

    calibration_status: str = "provisional"
    """'provisional' | 'calibrated' | 'null_baseline_run'"""

    # --- Metadata ---
    schema_version: str = SCHEMA_VERSION

    notes: Optional[str] = None
    """Free-text provenance note."""

    domain_metadata: dict[str, Any] = field(default_factory=dict)
    """
    Additional domain-specific fields from the producing hook.
    All domain-specific data that doesn't fit above goes here.
    Example: {'K': 2.0, 'n': 50, 'sync_index': 0.96}
    """

    # --- Qualification Status ---
    def qualification_status(self) -> str:
        """
        Returns a classification of this event based on which DCP components
        were observed. Does NOT validate correctness — only structural completeness.

        Returns:
            'FULL'             — all five components present
            'UNCONFIRMED'      — missing tension (tension_proxy is None)
            'INCOMPLETE'       — two or more components missing
            'INSUFFICIENT'     — fewer than three components present
        """
        components = [
            self.possibility_space_proxy,
            self.constraint_proxy,
            self.tension_proxy,
            self.collapse_proxy,
            self.post_collapse_narrowing,
        ]
        present = sum(c is not None for c in components)

        if present == 5:
            return "FULL"
        if present == 4 and self.tension_proxy is None:
            return "UNCONFIRMED"  # tension not observable
        if present >= 3:
            return "INCOMPLETE"
        return "INSUFFICIENT"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["qualification_status"] = self.qualification_status()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ---------------------------------------------------------------------------
# DCPProbeOutput — lightweight schema for structured probe results
# ---------------------------------------------------------------------------

DCP_PROBE_SCHEMA_VERSION = "dcp_probe_v1"


@dataclass
class DCPProbeOutput:
    """
    Structured output schema for a domain DCP probe run.

    Intended as the minimal portable record of what a probe observed
    about a single agent/system/session. Not a full DCPEvent — this is
    the probe-level summary that feeds into DCPEvent construction.

    Example use: cognition domain probe on a toy branching agent session,
    or a math domain probe summary at a specific K value.

    This is a data schema, not a detection algorithm.
    """

    agent_id: str
    """Identifier for the agent, simulation, or artifact being probed."""

    source_domain: str
    """Domain that produced this probe: 'math', 'games', 'music', 'cognition', etc."""

    constraint_profile: dict[str, Any]
    """
    Constraint description. Minimal expected structure:
        {
            'class':     'internal' | 'external' | 'mixed' | None,
            'intensity': float,   # [0.0, 1.0] normalized constraint strength
            'notes':     str      # optional domain-specific description
        }
    """

    possibility_breadth: Optional[float] = None
    """Estimated possibility-space breadth at time of probe. [0.0, 1.0]"""

    tension_estimate: Optional[float] = None
    """Estimated pre-collapse tension level. [0.0, 1.0]"""

    collapse_detected: bool = False
    """Whether a compression event was identified during this probe session."""

    collapse_morphology: Optional[str] = None
    """
    Morphology label if collapse was detected. Use CollapseMorphology values.
    None if no collapse or morphology not yet classified.
    """

    post_collapse_class: Optional[str] = None
    """
    Post-collapse trajectory class label if collapse was detected.
    Domain-specific; not yet standardized across domains.
    """

    confidence: float = 0.0
    """Provisional confidence for the collapse detection. [0.0, 1.0]"""

    notes: Optional[str] = None
    """Free-text provenance or context note."""

    schema_version: str = DCP_PROBE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id":            self.agent_id,
            "source_domain":       self.source_domain,
            "constraint_profile":  self.constraint_profile,
            "possibility_breadth": self.possibility_breadth,
            "tension_estimate":    self.tension_estimate,
            "collapse_detected":   self.collapse_detected,
            "collapse_morphology": self.collapse_morphology,
            "post_collapse_class": self.post_collapse_class,
            "confidence":          self.confidence,
            "notes":               self.notes,
            "schema_version":      self.schema_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

