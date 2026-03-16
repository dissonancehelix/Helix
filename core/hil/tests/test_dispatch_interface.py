"""Tests for core.hil.dispatch_interface"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from core.hil.dispatch_interface import dispatch
from core.hil.errors import HILError


class TestDispatch:
    def test_valid_no_dispatcher_returns_validated(self):
        result = dispatch("PROBE invariant:decision_compression", dispatcher=None, log=False)
        assert result["status"] == "validated"
        assert result["canonical"] == "PROBE invariant:decision_compression"
        assert "ast" in result

    def test_compile_atlas(self):
        result = dispatch("COMPILE atlas", dispatcher=None, log=False)
        assert result["status"] == "validated"
        assert result["canonical"] == "COMPILE atlas"

    def test_integrity_check(self):
        result = dispatch("INTEGRITY check", dispatcher=None, log=False)
        assert result["status"] == "validated"

    def test_graph_support(self):
        result = dispatch(
            "GRAPH support invariant:decision_compression",
            dispatcher=None, log=False
        )
        assert result["status"] == "validated"

    def test_invalid_command_returns_error(self):
        result = dispatch("rm -rf /", dispatcher=None, log=False)
        assert result["status"] == "hil_error"
        assert "error" in result

    def test_unknown_verb_returns_error(self):
        result = dispatch("EXECUTE something:foo", dispatcher=None, log=False)
        assert result["status"] == "hil_error"

    def test_bare_word_returns_error(self):
        result = dispatch("PROBE banana_space", dispatcher=None, log=False)
        assert result["status"] == "hil_error"

    def test_empty_returns_error(self):
        result = dispatch("", dispatcher=None, log=False)
        assert result["status"] == "hil_error"

    def test_ast_contains_verb(self):
        result = dispatch("SWEEP parameter:coupling_strength range:0..1",
                          dispatcher=None, log=False)
        assert result["ast"]["verb"] == "SWEEP"

    def test_dispatcher_mock(self):
        class MockDispatcher:
            def route(self, envelope):
                return {"status": "ok", "routed_to": envelope.get("engine", "python")}

        result = dispatch(
            "RUN experiment:decision_compression_probe engine:python",
            dispatcher=MockDispatcher(), log=False,
        )
        assert result["status"] == "ok"
        assert result["routed_to"] == "python"
