"""Tests for core.hil.normalizer"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from core.hil.normalizer import normalize, normalize_command
from core.hil.errors import HILSyntaxError, HILUnsafeCommandError


class TestNormalize:
    def test_already_canonical(self):
        result = normalize("PROBE invariant:decision_compression")
        assert result == "PROBE invariant:decision_compression"

    def test_alias_integrity(self):
        result = normalize("integrity")
        assert result == "INTEGRITY check"

    def test_alias_integrity_check(self):
        result = normalize("integrity check")
        assert result == "INTEGRITY check"

    def test_alias_compile(self):
        result = normalize("compile")
        assert result == "COMPILE atlas"

    def test_alias_compile_the_atlas(self):
        result = normalize("compile the atlas")
        assert result == "COMPILE atlas"

    def test_alias_probe_decision_compression(self):
        result = normalize("probe decision compression")
        assert result == "PROBE invariant:decision_compression"

    def test_alias_run_decision_compression_probe(self):
        result = normalize("run decision compression probe")
        assert result == "RUN experiment:decision_compression_probe"

    def test_already_canonical_compile(self):
        result = normalize("COMPILE atlas")
        assert result == "COMPILE atlas"

    def test_already_canonical_graph(self):
        result = normalize("GRAPH support invariant:decision_compression")
        assert result == "GRAPH support invariant:decision_compression"

    def test_sweep_canonical(self):
        result = normalize("SWEEP parameter:coupling_strength range:0..1")
        assert result == "SWEEP parameter:coupling_strength range:0..1"

    def test_empty_raises(self):
        with pytest.raises((HILSyntaxError, Exception)):
            normalize("")

    def test_unsafe_raises(self):
        with pytest.raises(HILUnsafeCommandError):
            normalize("rm -rf /")


class TestNormalizeCommand:
    """Compat API: normalize_command returns dict."""

    def test_returns_dict(self):
        result = normalize_command("PROBE invariant:decision_compression")
        assert isinstance(result, dict)
        assert result["source"] == "hil"
        assert result["version"] == "1.0"

    def test_has_canonical(self):
        result = normalize_command("PROBE invariant:decision_compression")
        assert result.get("canonical") == "PROBE invariant:decision_compression"

    def test_verb_lowercase(self):
        result = normalize_command("PROBE invariant:decision_compression")
        assert result["verb"] == "probe"

    def test_alias_normalized(self):
        result = normalize_command("integrity")
        assert result.get("canonical") == "INTEGRITY check"
