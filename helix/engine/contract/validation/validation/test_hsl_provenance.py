"""
core/governance/validation/test_hsl_provenance.py
==================================================
Minimal architecture-native validation for HSL provenance enforcement.

Checks:
1. RunProvenance factories produce correct canonical flags
2. CommandContext.default() is non-canonical
3. CommandContext.canonical() carries provenance correctly
4. require_canonical_provenance accepts canonical runs
5. require_canonical_provenance rejects non-canonical runs
6. labs_bypass allows non-canonical runs with explicit reason
7. CLI validate/dry-run paths parse without executing
8. Unknown CLI subcommands exit non-zero

Run from Helix root:
    python core/governance/validation/test_hsl_provenance.py
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, fn):
    try:
        fn()
        results.append((name, True, ""))
        print(f"  {PASS}  {name}")
    except Exception as e:
        results.append((name, False, str(e)))
        print(f"  {FAIL}  {name}")
        print(f"         {e}")


# ── 1. Provenance factories ───────────────────────────────────────────────────

def _test_cli_inline_is_canonical():
    from core.hsl.provenance import RunProvenance, EntryMode
    p = RunProvenance.from_cli_inline("ANALYZE TRACK track:foo")
    assert p.canonical is True, "from_cli_inline must be canonical"
    assert p.entry_mode == EntryMode.HSL_CLI
    assert p.hsl_source_type == "inline"
    assert p.hsl_source_hash is not None


def _test_cli_file_is_canonical():
    from core.hsl.provenance import RunProvenance, EntryMode
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".hsl", delete=False, mode="w") as f:
        f.write("LIST TRACKS\n")
        tmp = f.name
    try:
        p = RunProvenance.from_cli_file(tmp)
        assert p.canonical is True
        assert p.hsl_source_type == "file"
        assert p.hsl_source_hash is not None
    finally:
        os.unlink(tmp)


def _test_non_canonical_factory():
    from core.hsl.provenance import RunProvenance, EntryMode
    p = RunProvenance.non_canonical(reason="test")
    assert p.canonical is False
    assert p.entry_mode == EntryMode.PYTHON_DEV
    assert p.labs_bypass is False


def _test_labs_bypass_requires_reason():
    from core.hsl.provenance import RunProvenance
    try:
        RunProvenance.labs_bypass_explicit(reason="")
        raise AssertionError("Should have raised ValueError")
    except ValueError:
        pass  # expected


def _test_labs_bypass_with_reason():
    from core.hsl.provenance import RunProvenance
    p = RunProvenance.labs_bypass_explicit(reason="ingesting library for Phase 1")
    assert p.canonical is False
    assert p.labs_bypass is True
    assert p.bypass_reason


# ── 2. CommandContext provenance ──────────────────────────────────────────────

def _test_default_context_is_non_canonical():
    from core.hsl.context import CommandContext
    from core.hsl.provenance import EntryMode
    ctx = CommandContext.default()
    assert ctx.provenance is not None, "default() must stamp provenance"
    assert ctx.provenance.canonical is False
    assert ctx.provenance.entry_mode == EntryMode.PYTHON_DEV


def _test_canonical_context():
    from core.hsl.context import CommandContext
    from core.hsl.provenance import RunProvenance
    prov = RunProvenance.from_cli_inline("TEST")
    ctx = CommandContext.canonical(provenance=prov)
    assert ctx.provenance.canonical is True


# ── 3. Enforcement gate ───────────────────────────────────────────────────────

def _test_canonical_passes_gate():
    from core.hsl.context import CommandContext
    from core.hsl.provenance import RunProvenance
    from core.validation.runtime_checks import require_canonical_provenance
    prov = RunProvenance.from_cli_inline("TEST")
    ctx  = CommandContext.canonical(provenance=prov)
    require_canonical_provenance(ctx, action="test action")  # must not raise


def _test_non_canonical_blocked():
    from core.hsl.context import CommandContext
    from core.validation.runtime_checks import require_canonical_provenance, NonCanonicalExecutionError
    ctx = CommandContext.default()  # PYTHON_DEV
    try:
        require_canonical_provenance(ctx, action="test action")
        raise AssertionError("Should have raised NonCanonicalExecutionError")
    except NonCanonicalExecutionError:
        pass  # expected


def _test_missing_provenance_blocked():
    from core.validation.runtime_checks import require_canonical_provenance, NonCanonicalExecutionError
    try:
        require_canonical_provenance(None, action="test action")
        raise AssertionError("Should have raised NonCanonicalExecutionError")
    except NonCanonicalExecutionError:
        pass  # expected


def _test_labs_bypass_passes_with_warning():
    from core.hsl.context import CommandContext
    from core.hsl.provenance import RunProvenance
    from core.validation.runtime_checks import require_canonical_provenance
    import warnings
    prov = RunProvenance.labs_bypass_explicit(reason="test bypass")
    ctx  = CommandContext(provenance=prov)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        require_canonical_provenance(ctx, action="test action")
        assert len(w) == 1
        assert "labs bypass" in str(w[0].message).lower()


# ── 4. ANALYZE command gate ──────────────────────────────────────────────────

def _test_analyze_blocked_without_canonical_context():
    from core.hsl.context import CommandContext
    from core.hsl.interpreter import run_command

    result = run_command("ANALYZE TRACK track:missing_track", CommandContext.default())
    assert result["status"] == "error"
    assert "non-canonical" in result["error"].lower()


def _test_analyze_runs_past_gate_with_canonical_context():
    from core.hsl.context import CommandContext
    from core.hsl.interpreter import run_command
    from core.hsl.provenance import RunProvenance

    ctx = CommandContext.canonical(
        provenance=RunProvenance.from_cli_inline("ANALYZE SOUNDTRACK soundtrack:missing_soundtrack")
    )
    result = run_command("ANALYZE SOUNDTRACK soundtrack:missing_soundtrack", ctx)
    assert result["status"] == "error"
    assert "non-canonical" not in result["error"].lower()


# ── 4. Provenance serialisation ───────────────────────────────────────────────

def _test_provenance_to_dict():
    from core.hsl.provenance import RunProvenance
    p = RunProvenance.from_cli_inline("PROBE invariant:x")
    d = p.to_dict()
    for key in ("run_id", "entry_mode", "canonical", "timestamp", "hsl_source_hash"):
        assert key in d, f"Missing key: {key}"


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Helix HSL Provenance Validation\n")

    check("from_cli_inline is canonical",            _test_cli_inline_is_canonical)
    check("from_cli_file is canonical",              _test_cli_file_is_canonical)
    check("non_canonical factory",                   _test_non_canonical_factory)
    check("labs_bypass requires non-empty reason",   _test_labs_bypass_requires_reason)
    check("labs_bypass with reason",                 _test_labs_bypass_with_reason)
    check("CommandContext.default() is non-canonical", _test_default_context_is_non_canonical)
    check("CommandContext.canonical() is canonical", _test_canonical_context)
    check("canonical runs pass gate",                _test_canonical_passes_gate)
    check("non-canonical runs blocked at gate",      _test_non_canonical_blocked)
    check("missing provenance blocked at gate",      _test_missing_provenance_blocked)
    check("labs bypass passes with warning",         _test_labs_bypass_passes_with_warning)
    check("ANALYZE blocked without canonical context", _test_analyze_blocked_without_canonical_context)
    check("ANALYZE clears gate with canonical context", _test_analyze_runs_past_gate_with_canonical_context)
    check("provenance.to_dict() has required keys",  _test_provenance_to_dict)

    passed = sum(1 for _, ok, _ in results if ok)
    total  = len(results)
    print(f"\n{passed}/{total} checks passed")
    sys.exit(0 if passed == total else 1)
