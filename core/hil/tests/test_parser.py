"""Tests for core.hil.parser"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from core.hil.parser import parse
from core.hil.ast_nodes import HILCommand, TypedRef, RangeExpr
from core.hil.errors import (
    HILSyntaxError, HILUnknownCommandError, HILUnsafeCommandError,
)


# ── Valid commands ────────────────────────────────────────────────────────────

class TestProbe:
    def test_basic(self):
        cmd = parse("PROBE invariant:decision_compression")
        assert cmd.verb == "PROBE"
        assert cmd.subcommand is None
        assert cmd.targets == [TypedRef("invariant", "decision_compression")]

    def test_lowercase_verb_normalized(self):
        cmd = parse("probe invariant:decision_compression")
        assert cmd.verb == "PROBE"

    def test_operator_target(self):
        cmd = parse("PROBE operator:commitment_probe")
        assert cmd.targets[0] == TypedRef("operator", "commitment_probe")


class TestRun:
    def test_basic(self):
        cmd = parse("RUN experiment:decision_compression_probe")
        assert cmd.verb == "RUN"
        assert cmd.targets[0] == TypedRef("experiment", "decision_compression_probe")

    def test_with_engine(self):
        cmd = parse("RUN experiment:decision_compression_probe engine:python")
        assert cmd.verb == "RUN"
        assert cmd.get_engine() == "python"
        assert cmd.targets[0] == TypedRef("experiment", "decision_compression_probe")

    def test_engine_is_typed_ref(self):
        cmd = parse("RUN experiment:decision_compression_probe engine:python")
        assert isinstance(cmd.params["engine"], TypedRef)
        assert cmd.params["engine"].prefix == "engine"


class TestSweep:
    def test_basic(self):
        cmd = parse("SWEEP parameter:coupling_strength range:0..1")
        assert cmd.verb == "SWEEP"
        assert cmd.targets[0] == TypedRef("parameter", "coupling_strength")
        rng = cmd.get_range()
        assert rng is not None
        assert rng.low == 0.0
        assert rng.high == 1.0

    def test_float_range(self):
        cmd = parse("SWEEP parameter:threshold range:0.1..0.9")
        rng = cmd.get_range()
        assert abs(rng.low - 0.1) < 1e-9
        assert abs(rng.high - 0.9) < 1e-9

    def test_with_engine(self):
        cmd = parse("SWEEP parameter:coupling_strength range:0..1 engine:python")
        assert cmd.get_engine() == "python"


class TestCompile:
    def test_atlas(self):
        cmd = parse("COMPILE atlas")
        assert cmd.verb == "COMPILE"
        assert cmd.subcommand == "atlas"
        assert cmd.targets == []

    def test_graph(self):
        cmd = parse("COMPILE graph")
        assert cmd.subcommand == "graph"

    def test_entries(self):
        cmd = parse("COMPILE entries")
        assert cmd.subcommand == "entries"


class TestIntegrity:
    def test_check(self):
        cmd = parse("INTEGRITY check")
        assert cmd.verb == "INTEGRITY"
        assert cmd.subcommand == "check"

    def test_report(self):
        cmd = parse("INTEGRITY report")
        assert cmd.subcommand == "report"

    def test_gate(self):
        cmd = parse("INTEGRITY gate")
        assert cmd.subcommand == "gate"


class TestAtlas:
    def test_lookup(self):
        cmd = parse("ATLAS lookup invariant:decision_compression")
        assert cmd.verb == "ATLAS"
        assert cmd.subcommand == "lookup"
        assert cmd.targets[0] == TypedRef("invariant", "decision_compression")

    def test_verify(self):
        cmd = parse("ATLAS verify model:control_subspace_collapse")
        assert cmd.subcommand == "verify"


class TestGraph:
    def test_support(self):
        cmd = parse("GRAPH support invariant:decision_compression")
        assert cmd.verb == "GRAPH"
        assert cmd.subcommand == "support"
        assert cmd.targets[0] == TypedRef("invariant", "decision_compression")

    def test_trace(self):
        cmd = parse("GRAPH trace invariant:decision_compression")
        assert cmd.subcommand == "trace"

    def test_build(self):
        cmd = parse("GRAPH build")
        assert cmd.subcommand == "build"
        assert cmd.targets == []

    def test_export(self):
        cmd = parse("GRAPH export")
        assert cmd.subcommand == "export"


class TestValidateCmd:
    def test_atlas_with_target(self):
        cmd = parse("VALIDATE atlas invariant:decision_compression")
        assert cmd.verb == "VALIDATE"
        assert cmd.subcommand == "atlas"
        assert cmd.targets[0] == TypedRef("invariant", "decision_compression")


class TestTrace:
    def test_basic(self):
        cmd = parse("TRACE experiment:decision_compression_probe")
        assert cmd.verb == "TRACE"
        assert cmd.targets[0] == TypedRef("experiment", "decision_compression_probe")


# ── Canonical serialization ───────────────────────────────────────────────────

class TestCanonical:
    def test_probe_canonical(self):
        cmd = parse("PROBE invariant:decision_compression")
        assert cmd.canonical() == "PROBE invariant:decision_compression"

    def test_run_engine_canonical(self):
        cmd = parse("RUN experiment:decision_compression_probe engine:python")
        assert cmd.canonical() == "RUN experiment:decision_compression_probe engine:python"

    def test_sweep_canonical(self):
        cmd = parse("SWEEP parameter:coupling_strength range:0..1")
        assert cmd.canonical() == "SWEEP parameter:coupling_strength range:0..1"

    def test_compile_canonical(self):
        cmd = parse("COMPILE atlas")
        assert cmd.canonical() == "COMPILE atlas"

    def test_integrity_canonical(self):
        cmd = parse("INTEGRITY check")
        assert cmd.canonical() == "INTEGRITY check"

    def test_graph_canonical(self):
        cmd = parse("GRAPH support invariant:decision_compression")
        assert cmd.canonical() == "GRAPH support invariant:decision_compression"


# ── Invalid commands ──────────────────────────────────────────────────────────

class TestInvalidCommands:
    def test_bare_word_target(self):
        with pytest.raises((HILSyntaxError, HILUnknownCommandError)):
            parse("PROBE banana_space")

    def test_illegal_characters(self):
        with pytest.raises(HILSyntaxError):
            parse("PROBE -> -> collapse")

    def test_shell_rm(self):
        with pytest.raises(HILUnsafeCommandError):
            parse("rm -rf /")

    def test_shell_rm_space(self):
        with pytest.raises(HILUnsafeCommandError):
            parse("rm /home/user/data")

    def test_bare_word_run(self):
        with pytest.raises(HILSyntaxError):
            parse("RUN thing")

    def test_invalid_range(self):
        with pytest.raises(HILSyntaxError):
            parse("SWEEP parameter:foo range:abc")

    def test_reverse_range(self):
        with pytest.raises(HILSyntaxError):
            parse("SWEEP parameter:foo range:1..0")

    def test_unknown_verb(self):
        with pytest.raises(HILUnknownCommandError):
            parse("EXECUTE something")

    def test_empty(self):
        with pytest.raises(HILSyntaxError):
            parse("")

    def test_sql_injection(self):
        with pytest.raises(HILUnsafeCommandError):
            parse("DROP TABLE experiments")

    def test_graph_bare_words(self):
        with pytest.raises((HILSyntaxError, HILUnknownCommandError)):
            parse("GRAPH nonsense garbage")
