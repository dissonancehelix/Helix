from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from core.engines.python import cross_probe_analysis
from core.kernel.dispatcher import probe_registry, probe_runner
from core.kernel.graph.storage import atlas_builder
from core.kernel.governance_bridge import promotion_engine
from core.kernel.infra.artifact_lifecycle import compact_all
from core.kernel.infra.hashing import compute_sha256, validate_artifact_integrity
from core.kernel.runtime import reproduce_run
from core.kernel.substrate import architecture_watchdog, kernel_lock
from core.paths import ARTIFACTS_ROOT, ATLAS_ROOT

ROOT = Path(__file__).resolve().parent


def write_artifact(run_id, relative_path, data, schema_type=None):
    if not run_id:
        raise Exception("MISSING_RUN_ID")

    abs_path = (ARTIFACTS_ROOT / run_id / relative_path).resolve()
    artifacts_dir = ARTIFACTS_ROOT.resolve()
    if not str(abs_path).startswith(str(artifacts_dir)):
        raise Exception("ILLEGAL_WRITE_OUTSIDE_ARTIFACTS")

    abs_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = ARTIFACTS_ROOT / run_id / 'run_manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    if str(abs_path) in manifest.get('artifacts', {}):
        raise Exception("OVERWRITE_FORBIDDEN_USE_NEW_RUN_ID")

    abs_path.write_text(json.dumps(data, indent=4), encoding='utf-8')
    h = compute_sha256(str(abs_path))
    manifest.setdefault('artifacts', {})[str(abs_path)] = h
    manifest_path.write_text(json.dumps(manifest, indent=4), encoding='utf-8')


def cmd_verify():
    required = [ARTIFACTS_ROOT, ATLAS_ROOT]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(f"[VERIFY] Missing required paths: {missing}")
        return False
    print("[VERIFY] Canonical Helix paths are present.")
    return True


def cmd_audit(run_id):
    manifest_path = ARTIFACTS_ROOT / run_id / 'run_manifest.json'
    if not manifest_path.exists():
        return False
    return validate_artifact_integrity(manifest_path)


def cmd_run():
    print("Rebuilding atlas...")
    if ATLAS_ROOT.exists():
        shutil.rmtree(ATLAS_ROOT)
    (ATLAS_ROOT / 'invariants').mkdir(parents=True, exist_ok=True)
    atlas_builder.build_atlas(verbose=True)
    compact_all()
    print("Atlas rebuilt successfully.")


def cmd_lock_kernel():
    success = kernel_lock.lock_kernel(ROOT)
    sys.exit(0 if success else 1)


def cmd_unlock_kernel():
    success = kernel_lock.unlock_kernel(ROOT)
    sys.exit(0 if success else 1)


def cmd_kernel_status():
    status = kernel_lock.kernel_status(ROOT)
    print(json.dumps(status, indent=2))


def cmd_watchdog_start():
    print('[WATCHDOG] Starting architecture watchdog (blocking). Press Ctrl+C to stop.')
    try:
        architecture_watchdog.start_watchdog(ROOT.parent.parent, ARTIFACTS_ROOT, background=False)
    except KeyboardInterrupt:
        print('\n[WATCHDOG] Stopped.')


def cmd_probe_run(probe_name, lab_name=None):
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
    written = atlas_builder.build_atlas(
        artifacts_root=ARTIFACTS_ROOT,
        atlas_dir=ATLAS_ROOT / 'invariants',
        verbose=True,
    )
    print(f'\n[ATLAS] Built {len(written)} invariant entries.')
    sys.exit(0)


def cmd_promote_invariant(invariant_name):
    try:
        result = promotion_engine.promote_invariant(invariant_name, verbose=True)
        sys.exit(0 if result['passed'] else 1)
    except FileNotFoundError as e:
        print(f'[PROMOTE] ERROR: {e}')
        sys.exit(1)


def cmd_probe_run_all(lab_name=None):
    registry = probe_registry.discover_probes()
    if not registry:
        print('[PROBE_RUN_ALL] No probes found in labs/experiments/invariants/.')
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
    atlas_builder.build_atlas(artifacts_root=ARTIFACTS_ROOT, atlas_dir=ATLAS_ROOT / 'invariants', verbose=True)

    print(f'\n[PROBE_RUN_ALL] Complete. all_passed={all_passed}')
    for name, summary in sorted(results.items()):
        status = 'PASS' if summary.get('passed') else 'FAIL'
        run_id = summary.get('run_id', 'N/A')
        print(f'  {name}: {status}  run_id={run_id}')
    sys.exit(0 if all_passed else 1)


def cmd_reproduce(run_id):
    try:
        result = reproduce_run.reproduce_run(run_id, verbose=True)
        status = 'REPRODUCIBLE' if result.get('reproducible') else 'NON_REPRODUCIBLE'
        print(f'\n[REPRODUCE] {status}: {run_id}')
        if result.get('mismatches'):
            print(f'  Mismatches: {result["mismatches"]}')
        sys.exit(0 if result.get('reproducible') else 1)
    except (FileNotFoundError, ValueError) as e:
        print(f'[REPRODUCE] ERROR: {e}')
        sys.exit(1)


def cmd_cross_probe_analysis(lab_name=None, probe_filter=None):
    probes = probe_filter.split(',') if probe_filter else None
    report = cross_probe_analysis.run_cross_probe_analysis(
        artifacts_root=ARTIFACTS_ROOT,
        probe_filter=probes,
        lab_filter=lab_name,
        verbose=True,
    )
    out_path = ARTIFACTS_ROOT / 'cross_probe_report.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'\n[CROSS_PROBE] Report written: {out_path}')
    sys.exit(0)


def _parse_flag(args, flag):
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
            cmd_probe_run(sys.argv[2], _parse_flag(sys.argv, '--lab'))
        elif cmd == 'probe-run-all':
            cmd_probe_run_all(_parse_flag(sys.argv, '--lab'))
        elif cmd == 'reproduce' and len(sys.argv) > 2:
            cmd_reproduce(sys.argv[2])
        elif cmd == 'cross-probe-analysis':
            cmd_cross_probe_analysis(_parse_flag(sys.argv, '--lab'), _parse_flag(sys.argv, '--probes'))
        elif cmd == 'atlas-build':
            cmd_atlas_build()
        elif cmd == 'promote-invariant' and len(sys.argv) > 2:
            cmd_promote_invariant(sys.argv[2])
        else:
            print(
                'Usage: helix.py <command>\n'
                'Commands:\n'
                '  run                                       Rebuild atlas and compact artifacts\n'
                '  verify                                    Validate canonical path layout\n'
                '  audit <run_id>                            Verify artifact integrity for a run\n'
                '  probe-run <probe> [--lab <lab>]           Run a probe against a lab dataset\n'
                '  probe-run-all [--lab <lab>]               Run all probes against a lab, rebuild Atlas\n'
                '  reproduce <run_id>                        Re-run probe and verify within tolerance\n'
                '  cross-probe-analysis [--lab <l>] [--probes p1,p2]  Compare outputs across probes\n'
                '  atlas-build                               Scan artifacts and generate Atlas entries\n'
                '  promote-invariant <name>                  Run promotion gate for an invariant\n'
                '  lock-kernel                               Set chattr +i on the kernel (Linux/WSL2)\n'
                '  unlock-kernel                             Remove chattr +i (requires HELIX_KERNEL_UNLOCK=1)\n'
                '  kernel-status                             Report current kernel lock state\n'
                '  watchdog-start                            Start architecture watchdog (blocking)\n'
            )
            sys.exit(1)
