"""Tests for core.hil.aliases"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from core.hil.aliases import resolve_alias, list_aliases
from core.hil.errors import HILAmbiguityError


class TestResolveAlias:
    def test_integrity(self):
        assert resolve_alias(["integrity"]) == "INTEGRITY check"

    def test_integrity_check(self):
        assert resolve_alias(["integrity", "check"]) == "INTEGRITY check"

    def test_integrity_report(self):
        assert resolve_alias(["integrity", "report"]) == "INTEGRITY report"

    def test_compile(self):
        assert resolve_alias(["compile"]) == "COMPILE atlas"

    def test_compile_the_atlas(self):
        assert resolve_alias(["compile", "the", "atlas"]) == "COMPILE atlas"

    def test_probe_decision_compression(self):
        result = resolve_alias(["probe", "decision", "compression"])
        assert result == "PROBE invariant:decision_compression"

    def test_run_decision_compression_probe(self):
        result = resolve_alias(["run", "decision", "compression", "probe"])
        assert result == "RUN experiment:decision_compression_probe"

    def test_unknown_returns_none(self):
        assert resolve_alias(["foobar", "baz"]) is None

    def test_empty_returns_none(self):
        assert resolve_alias([]) is None

    def test_case_insensitive(self):
        result = resolve_alias(["INTEGRITY"])
        assert result == "INTEGRITY check"

    def test_graph_build(self):
        result = resolve_alias(["graph", "build"])
        assert result == "GRAPH build"


class TestListAliases:
    def test_returns_list(self):
        aliases = list_aliases()
        assert isinstance(aliases, list)
        assert len(aliases) > 5

    def test_tuples_of_strings(self):
        for pattern, canonical in list_aliases():
            assert isinstance(pattern, str)
            assert isinstance(canonical, str)

    def test_canonical_uppercase_verb(self):
        for _, canonical in list_aliases():
            verb = canonical.split()[0]
            assert verb == verb.upper()
