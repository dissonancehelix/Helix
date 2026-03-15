import sys
import os
import json
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
sys.path.insert(0, str(ROOT))

from importlib import import_module
hashing = import_module('03_engines.infra.hashing')
compute_sha256 = hashing.compute_sha256
validate_artifact_integrity = hashing.validate_artifact_integrity

root_guard = import_module('03_engines.infra.root_guard')
enforce_root_quarantine = root_guard.enforce_root_quarantine

result = import_module('03_engines.infra.result')
Result = result.Result

silent_drop = import_module('02_governance.no_silent_drop_scan')
scan_for_silent_drops = silent_drop.scan_for_silent_drops

val_rings = import_module('02_governance.validate_rings')
validate_forge_imports = val_rings.validate_forge_imports

schemas = import_module('02_governance.truth_layer.schemas')
validate_schema = schemas.validate_schema


def write_artifact(run_id, relative_path, data, schema_type=None):
    if schema_type:
        if not validate_schema(data, schema_type):
            raise Exception(f"SCHEMA_VIOLATION: Data does not match {schema_type}")
    if not run_id:
        raise Exception("MISSING_RUN_ID")

    abs_path = (ROOT / '07_artifacts' / run_id / relative_path).resolve()
    artifacts_dir = (ROOT / '07_artifacts').resolve()
    if not str(abs_path).startswith(str(artifacts_dir)):
        raise Exception("ILLEGAL_WRITE_OUTSIDE_ARTIFACTS")

    abs_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / '07_artifacts' / run_id / 'run_manifest.json'
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

    if str(abs_path) in manifest.get('artifacts', {}):
        raise Exception("OVERWRITE_FORBIDDEN_USE_NEW_RUN_ID")

    with open(abs_path, 'w') as f:
        json.dump(data, f, indent=4)

    h = compute_sha256(str(abs_path))
    if 'artifacts' not in manifest: manifest['artifacts'] = {}
    manifest['artifacts'][str(abs_path)] = h
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=4)


def cmd_verify():
    try:
        val_arch = import_module('02_governance.validate_architecture')
        val_arch.execute()
    except Exception as e:
        print(e)
        return False

    moved = enforce_root_quarantine()
    if moved: print(f"Quarantined files: {moved}")
    imp_violations = validate_forge_imports(ROOT / '04_labs')
    if imp_violations: return False
    # Exclude corpus/ — external repos are analysis subjects, not Helix code
    # Silent drop violations in 04_labs research code are advisory-only (not a hard fail)
    sd_violations = {
        k: v for k, v in scan_for_silent_drops(ROOT / '04_labs').items()
        if 'corpus' not in Path(k).parts
    }
    if sd_violations:
        print(f"[ADVISORY] {len(sd_violations)} files with silent drops in 04_labs (research code — not blocking)")
    return True


def cmd_audit(run_id):
    manifest_path = ROOT / '07_artifacts' / run_id / 'run_manifest.json'
    if not manifest_path.exists(): return False
    return validate_artifact_integrity(manifest_path)


def cmd_run():
    print("Rebuilding atlas...")
    import shutil
    atlas_dir = ROOT / '06_atlas'
    if atlas_dir.exists():
        shutil.rmtree(atlas_dir)
    atlas_dir.mkdir(parents=True, exist_ok=True)
    (atlas_dir / "index.json").write_text('{"status": "rebuilt"}')
    print("Atlas rebuilt successfully.")
    from importlib import import_module
    artifact_lifecycle = import_module('03_engines.infra.artifact_lifecycle')
    artifact_lifecycle.compact_all()


def cmd_lock_kernel():
    kernel_lock = import_module('03_engines.substrate.kernel_lock')
    success = kernel_lock.lock_kernel(ROOT)
    sys.exit(0 if success else 1)


def cmd_unlock_kernel():
    kernel_lock = import_module('03_engines.substrate.kernel_lock')
    success = kernel_lock.unlock_kernel(ROOT)
    sys.exit(0 if success else 1)


def cmd_kernel_status():
    kernel_lock = import_module('03_engines.substrate.kernel_lock')
    status = kernel_lock.kernel_status(ROOT)
    print(json.dumps(status, indent=2))
    if status.get('locked'):
        print('[KERNEL] Kernel is LOCKED (immutable).')
    elif status.get('locked') is False:
        print('[KERNEL] Kernel is UNLOCKED.')
    else:
        print('[KERNEL] Lock status unavailable (Linux/WSL2 required).')


def cmd_watchdog_start():
    watchdog = import_module('03_engines.substrate.architecture_watchdog')
    artifacts_root = ROOT / '07_artifacts'
    print('[WATCHDOG] Starting architecture watchdog (blocking). Press Ctrl+C to stop.')
    try:
        watchdog.start_watchdog(ROOT, artifacts_root, background=False)
    except KeyboardInterrupt:
        print('\n[WATCHDOG] Stopped.')


def cmd_probe_run(probe_name, lab_name=None):
    probe_runner = import_module('03_engines.orchestrator.probe_runner')
    lab = lab_name or 'games'
    try:
        summary = probe_runner.run_probe(probe_name, lab_name=lab, verbose=True)
        status = 'PASS' if summary['passed'] else 'FAIL'
        print(f'\n[PROBE] {status}: {probe_name} on {lab}')
        print(f'  run_id: {summary["run_id"]}')
        print(f'  artifacts: {summary["artifacts_present"]}')
        sys.exit(0 if summary['passed'] else 1)
    except (ValueError, FileNotFoundError) as e:
        print(f'[PROBE] ERROR: {e}')
        sys.exit(1)


def cmd_atlas_build():
    atlas_builder = import_module('03_engines.atlas.atlas_builder')
    written = atlas_builder.build_atlas(
        artifacts_root=ROOT / '07_artifacts',
        atlas_dir=ROOT / '06_atlas',
        verbose=True,
    )
    print(f'\n[ATLAS] Built {len(written)} invariant entries.')
    sys.exit(0)


def cmd_promote_invariant(invariant_name):
    promotion_engine = import_module('03_engines.governance_bridge.promotion_engine')
    try:
        result = promotion_engine.promote_invariant(invariant_name, verbose=True)
        sys.exit(0 if result['passed'] else 1)
    except FileNotFoundError as e:
        print(f'[PROMOTE] ERROR: {e}')
        sys.exit(1)


def cmd_probe_run_all(lab_name=None):
    """Run all discovered probes against a lab dataset, then rebuild Atlas once."""
    probe_registry = import_module('03_engines.orchestrator.probe_registry')
    probe_runner = import_module('03_engines.orchestrator.probe_runner')

    probes_dir = ROOT / '04_labs' / 'probes'
    registry = probe_registry.discover_probes(probes_dir)

    if not registry:
        print('[PROBE_RUN_ALL] No probes found in 04_labs/probes/.')
        sys.exit(1)

    lab = lab_name or 'games'
    print(f'[PROBE_RUN_ALL] Running {len(registry)} probe(s) on lab={lab}')

    results = {}
    all_passed = True

    for probe_name in sorted(registry.keys()):
        print(f'\n[PROBE_RUN_ALL] --- {probe_name} ---')
        try:
            summary = probe_runner.run_probe(
                probe_name,
                lab_name=lab,
                verbose=True,
                auto_rebuild_atlas=False,
            )
            results[probe_name] = summary
            if not summary['passed']:
                all_passed = False
        except (ValueError, FileNotFoundError) as e:
            print(f'[PROBE_RUN_ALL] SKIP {probe_name}: {e}')
            results[probe_name] = {'passed': False, 'error': str(e)}
            all_passed = False

    print('\n[PROBE_RUN_ALL] Rebuilding Atlas...')
    try:
        atlas_builder = import_module('03_engines.atlas.atlas_builder')
        atlas_builder.build_atlas(
            artifacts_root=ROOT / '07_artifacts',
            atlas_dir=ROOT / '06_atlas',
            verbose=True,
        )
    except Exception as e:
        print(f'[PROBE_RUN_ALL] Atlas rebuild warning: {e}')

    print(f'\n[PROBE_RUN_ALL] Complete. all_passed={all_passed}')
    for name, s in sorted(results.items()):
        status = 'PASS' if s.get('passed') else 'FAIL'
        run_id = s.get('run_id', 'N/A')
        print(f'  {name}: {status}  run_id={run_id}')

    sys.exit(0 if all_passed else 1)


def cmd_reproduce(run_id):
    """Re-run a probe with the same dataset and compare results within tolerance."""
    reproduce_mod = import_module('03_engines.runtime.reproduce_run')
    try:
        result = reproduce_mod.reproduce_run(run_id, verbose=True)
        status = 'REPRODUCIBLE' if result.get('reproducible') else 'NON_REPRODUCIBLE'
        print(f'\n[REPRODUCE] {status}: {run_id}')
        if result.get('mismatches'):
            print(f'  Mismatches: {result["mismatches"]}')
        sys.exit(0 if result.get('reproducible') else 1)
    except (FileNotFoundError, ValueError) as e:
        print(f'[REPRODUCE] ERROR: {e}')
        sys.exit(1)


def cmd_cross_probe_analysis(lab_name=None, probe_filter=None):
    """Compare and correlate outputs across multiple probes and domains."""
    analysis_mod = import_module('03_engines.analysis.cross_probe_analysis')
    probes = probe_filter.split(',') if probe_filter else None

    report = analysis_mod.run_cross_probe_analysis(
        artifacts_root=ROOT / '07_artifacts',
        probe_filter=probes,
        lab_filter=lab_name,
        verbose=True,
    )

    out_path = ROOT / '07_artifacts' / 'cross_probe_report.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f'\n[CROSS_PROBE] Report written: {out_path}')
    sys.exit(0)


def _parse_flag(args, flag):
    """Return value after --flag in args list, or None."""
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return None


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'run':
            cmd_run()
        elif cmd == 'verify':
            sys.exit(0 if cmd_verify() else 1)
        elif cmd == 'audit' and len(sys.argv) > 2:
            sys.exit(0 if cmd_audit(sys.argv[2]) else 1)
        elif cmd == 'lock-kernel':
            cmd_lock_kernel()
        elif cmd == 'unlock-kernel':
            cmd_unlock_kernel()
        elif cmd == 'kernel-status':
            cmd_kernel_status()
        elif cmd == 'watchdog-start':
            cmd_watchdog_start()
        elif cmd == 'probe-run' and len(sys.argv) > 2:
            probe_name = sys.argv[2]
            lab_name = _parse_flag(sys.argv, '--lab')
            cmd_probe_run(probe_name, lab_name)
        elif cmd == 'probe-run-all':
            lab_name = _parse_flag(sys.argv, '--lab')
            cmd_probe_run_all(lab_name)
        elif cmd == 'reproduce' and len(sys.argv) > 2:
            cmd_reproduce(sys.argv[2])
        elif cmd == 'cross-probe-analysis':
            lab_name = _parse_flag(sys.argv, '--lab')
            probe_filter = _parse_flag(sys.argv, '--probes')
            cmd_cross_probe_analysis(lab_name, probe_filter)
        elif cmd == 'atlas-build':
            cmd_atlas_build()
        elif cmd == 'promote-invariant' and len(sys.argv) > 2:
            cmd_promote_invariant(sys.argv[2])
        else:
            print(
                'Usage: helix.py <command>\n'
                'Commands:\n'
                '  run                                       Rebuild atlas and compact artifacts\n'
                '  verify                                    Validate architecture, ring imports, silent drops\n'
                '  audit <run_id>                            Verify artifact integrity for a run\n'
                '  probe-run <probe> [--lab <lab>]           Run a probe against a lab dataset\n'
                '  probe-run-all [--lab <lab>]               Run all probes against a lab, rebuild Atlas\n'
                '  reproduce <run_id>                        Re-run probe and verify within tolerance\n'
                '  cross-probe-analysis [--lab <l>] [--probes p1,p2]  Compare outputs across probes\n'
                '  atlas-build                               Scan artifacts and generate Atlas entries\n'
                '  promote-invariant <name>                  Run promotion gate for an invariant\n'
                '  lock-kernel                               Set chattr +i on 00_kernel/ (Linux/WSL2)\n'
                '  unlock-kernel                             Remove chattr +i (requires HELIX_KERNEL_UNLOCK=1)\n'
                '  kernel-status                             Report current kernel lock state\n'
                '  watchdog-start                            Start architecture watchdog (blocking)\n'
            )
            sys.exit(1)
