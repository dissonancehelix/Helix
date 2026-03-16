"""
HIL Alias Registry
==================
Maps human-readable shorthand inputs to canonical HIL strings.

Rules:
- Patterns are explicit — no fuzzy matching.
- Ambiguous expansions raise HILAmbiguityError.
- Unknown inputs return None (fall through to parser).
- Pattern matching is case-insensitive on the token list.
"""
from __future__ import annotations

# (pattern_tokens_lower, canonical_hil_string)
_ALIAS_TABLE: list[tuple[tuple[str, ...], str]] = [
    # PROBE
    (("probe", "decision", "compression"),       "PROBE invariant:decision_compression"),
    (("probe", "oscillator", "locking"),         "PROBE invariant:oscillator_locking"),
    (("probe", "epistemic", "irreversibility"),  "PROBE invariant:epistemic_irreversibility"),
    (("probe", "local", "incompleteness"),       "PROBE invariant:local_incompleteness"),
    (("probe", "regime", "transition"),          "PROBE invariant:regime_transition"),
    (("probe", "commitment"),                    "PROBE operator:commitment_probe"),

    # RUN
    (("run", "decision", "compression", "probe"), "RUN experiment:decision_compression_probe"),
    (("run", "decision", "compression", "sweep"), "RUN experiment:decision_compression_sweep"),
    (("run", "commitment", "probe"),              "RUN operator:commitment_probe"),

    # COMPILE
    (("compile",),                               "COMPILE atlas"),
    (("compile", "the", "atlas"),                "COMPILE atlas"),
    (("compile", "atlas"),                       "COMPILE atlas"),
    (("compile", "graph"),                       "COMPILE graph"),
    (("compile", "entries"),                     "COMPILE entries"),
    (("build", "atlas"),                         "COMPILE atlas"),

    # INTEGRITY
    (("integrity",),                             "INTEGRITY check"),
    (("integrity", "check"),                     "INTEGRITY check"),
    (("integrity", "report"),                    "INTEGRITY report"),
    (("integrity", "gate"),                      "INTEGRITY gate"),
    (("check", "integrity"),                     "INTEGRITY check"),

    # GRAPH
    (("graph",),                                 "GRAPH build"),
    (("graph", "build"),                         "GRAPH build"),
    (("graph", "export"),                        "GRAPH export"),

    # VALIDATE
    (("validate",),                              "VALIDATE atlas"),
    (("validate", "atlas"),                      "VALIDATE atlas"),

    # TRACE
    (("trace", "decision", "compression"),       "TRACE experiment:decision_compression_sweep"),
]


def resolve_alias(tokens: list[str]) -> str | None:
    """
    Match lowercased token list against alias table.

    Rules:
    - Only matches when remaining tokens (after the pattern) are typed refs (contain ':')
      or there are no remaining tokens.  Bare-word remainders invalidate the match.
    - Longest match wins.
    - If multiple patterns of the same length yield the same canonical string,
      that string is returned (not ambiguous — same result).
    - Raises HILAmbiguityError only if longest matches yield different canonical strings.
    """
    from core.hil.errors import HILAmbiguityError
    lower = [t.lower() for t in tokens]
    # (pattern_length, canonical)
    candidates: list[tuple[int, str]] = []
    for pattern, canonical in _ALIAS_TABLE:
        plen = len(pattern)
        if lower[:plen] == list(pattern):
            remaining = lower[plen:]
            # Remaining tokens must all be typed refs (contain ':') or absent
            if all(":" in t for t in remaining):
                candidates.append((plen, canonical))
    if not candidates:
        return None
    max_len = max(plen for plen, _ in candidates)
    best = [c for plen, c in candidates if plen == max_len]
    unique = list(dict.fromkeys(best))   # deduplicate preserving order
    if len(unique) == 1:
        return unique[0]
    raise HILAmbiguityError(
        f"Ambiguous alias {' '.join(tokens)!r} matches {len(unique)} patterns: "
        + ", ".join(repr(m) for m in unique),
        raw=" ".join(tokens),
    )


def list_aliases() -> list[tuple[str, str]]:
    """Return all (input_pattern, canonical) pairs as strings."""
    return [(" ".join(p), c) for p, c in _ALIAS_TABLE]
