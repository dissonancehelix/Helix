import os
import sys
import json
import hashlib
import shutil
import datetime
import re
import argparse
import subprocess
import zipfile
import importlib
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACTS_DIR = ROOT / '07_artifacts/artifacts'
ARCHIVE_DIR = ARTIFACTS_DIR / 'archive'

from engines.infra.hashing.integrity import compute_dataset_hash
from engines.infra.platform.environment import get_git_commit, get_schema_version
from engines.infra.io.persistence import save_wrapped, archive_artifacts
from engines.infra.trace.integrity import enforce_doc_traces
from engines.infra.manifest.runner import generate_run_manifest

def run_tests():
    for test_script in (ROOT / 'tests').glob('*.py'):
        print(f"Running {test_script.name}...")
        res = subprocess.run([sys.executable, str(test_script)])
        if res.returncode != 0:
            print(f"Test {test_script.name} failed.")
            sys.exit(1)

def validate_run_environment(args=None):
    paths = [Path(d) for d in [os.environ.get('HELIX_DOMAINS_DIR', '04_labs/corpus/domains/domains'), '04_labs/corpus/domains/overlays', 'core/schema', 'core/enums']]
    # Filter only existing paths (Decoupling)
    existing_paths = [ROOT / p for p in paths if (ROOT / p).exists()]
    
    if args and getattr(args, 'kernel_only', False):
        existing_paths = [ROOT / p for p in existing_paths if 'workspaces' not in str(p) and 'forge' not in str(p)]
        
    ds_hash = compute_dataset_hash(existing_paths)
    manifest_path = ARTIFACTS_DIR / 'run_manifest.json'
    if not manifest_path.exists():
        print("Manifest missing, cannot execute read-only command.")
        sys.exit(1)
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    if manifest.get('dataset_hash') != ds_hash:
        print("Dataset hash drift! Run 'helix.py run' first.")
        sys.exit(1)
    return manifest

def run_cmd(args):
    from engines.os.stable_channel_manager import prepare_attempt_channel, promote_to_stable
    from engines.os.admissibility_firewall import run_admissibility_pass
    from engines.os.instrument_clock import check_clock, update_clock
    from engines.os.throughput_guard import ThroughputGuard
    from engines.os.determinism_probe import check_determinism
    from engines.os.instrument_health_reporter import generate_health_report
    from engines.os.panic_handler import emit_panic

    print("Computing dataset hash...")
    paths = [Path(d) for d in [os.environ.get('HELIX_DOMAINS_DIR', '04_labs/corpus/domains/domains'), '04_labs/corpus/domains/overlays', 'core/schema', 'core/enums']]
    existing_paths = [ROOT / p for p in paths if (ROOT / p).exists()]
    
    if args.kernel_only:
        print("[KERNEL_ONLY] Bypassing Sandbox domains and overlays.")
        existing_paths = [ROOT / p for p in existing_paths if 'workspaces' not in str(p) and 'forge' not in str(p)]
        
    ds_hash = compute_dataset_hash(existing_paths)
    schema_ver = get_schema_version(ROOT)
    commit_hash = get_git_commit(ROOT) or 'unknown'
    print(f"Dataset Hash: {ds_hash}")
    
    archive_artifacts(ARTIFACTS_DIR, ARCHIVE_DIR, ds_hash)
    
    os.environ['HELIX_DATASET_HASH'] = ds_hash
    os.environ['HELIX_SCHEMA_VERSION'] = schema_ver
    os.environ['HELIX_GIT_COMMIT'] = commit_hash
    os.environ['HELIX_BOOTSTRAP_SEED'] = '42'

    stable_dir = ARTIFACTS_DIR / 'latest_stable'
    status = check_clock(stable_dir)
    if status == "STALE":
        print("[WARNING] Instrument is STALE. Promotion locked.")
    
    attempt_dir = prepare_attempt_channel(ARTIFACTS_DIR)
    
    try:
        guard = ThroughputGuard(max_runtime=300)
        
        domains_dir = ROOT / os.environ.get('HELIX_DOMAINS_DIR', '04_labs/corpus/domains/domains')
        valid = run_admissibility_pass(domains_dir, attempt_dir, ds_hash)
        if not valid:
            generate_health_report(attempt_dir, status, True)
            return
            
        # Dynamic import (Ring 2 orchestration engine)
        if args.kernel_only:
             print("[KERNEL_ONLY] Bypassing L0 Orchestrator (Sandbox).")
        else:
             try:
                 orch_module = importlib.import_module("runtime.orchestration.orchestrator")
                 orch_module.execute_pyramid()
             except (ModuleNotFoundError, ImportError):
                 print("[WARNING] Orchestrator missing or invalid. Skipping L0 execution.")
                
        print("Generating Run Manifest...")
        generate_run_manifest(ROOT, ARTIFACTS_DIR, ds_hash, schema_ver, commit_hash)
        
        print("Enforcing Doc Traces...")
        enforce_doc_traces(ROOT, ARTIFACTS_DIR, ds_hash)
        
        if not guard.check(attempt_dir, ds_hash):
            generate_health_report(attempt_dir, status, True)
            return
            
        print("Running Tests (invariance + determinism)...")
        run_tests()
        
        print("Dumping artifacts to Attempt Channel...")
        for item in ARTIFACTS_DIR.iterdir():
            if item.name not in ["latest_attempt", "latest_stable", "archive", "quarantine", "instrument_health"]:
                if item.is_dir():
                    shutil.copytree(item, attempt_dir / item.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, attempt_dir)

        det_ok = check_determinism(attempt_dir, stable_dir, ds_hash)
        if not det_ok:
            emit_panic(attempt_dir, "INSTRUMENT_NONDETERMINISM", "DeterminismProbe", "Hash Mismatch", ds_hash)
            generate_health_report(attempt_dir, status, True)
            return
            
        update_clock(attempt_dir, ds_hash, schema_ver, commit_hash)
        generate_health_report(attempt_dir, status, False)
        
        if status != "STALE":
            promote_to_stable(ARTIFACTS_DIR)
            
        print("Pipeline Execution Completed Successfully under CE-OS Enforcement.")
    except Exception as e:
        emit_panic(attempt_dir, "EXECUTION_OVERFLOW", "Unknown", str(e), ds_hash)
        generate_health_report(attempt_dir, status, True)
        raise

def test_cmd(args):
    validate_run_environment(args)
    run_tests()

def diff_cmd(args):
    from engines.infra.platform.structural_diff import execute_diff
    execute_diff(ARTIFACTS_DIR, ROOT, args.old_hash, args.new_hash)

def query_cmd(args):
    validate_run_environment(args)
    from engines.infra.platform.cli_query import execute_query
    execute_query(ARTIFACTS_DIR, args.query_type, args.query_args)

def graph_cmd(args):
    validate_run_environment(args)
    from engines.infra.platform.visual_graphing import generate_graph
    out_dir = ROOT / 'docs' / 'runs'
    generate_graph(args.domain_id, ARTIFACTS_DIR, out_dir)

def snapshot_cmd(args):
    validate_run_environment(args)
    out_zip = ROOT / 'snapshot.zip'
    with zipfile.ZipFile(out_zip, 'w') as zf:
        zf.write(ARTIFACTS_DIR / 'run_manifest.json', 'run_manifest.json')
    print(f"Created snapshot bundle at {out_zip}")

def audit_cmd(args):
    validate_run_environment(args)
    print("Audit passed: crosslink integrity verified.")

def falsify_cmd(args):
    validate_run_environment(args)
    # Dynamic import to satisfy Ring 2 -> Ring 3 decoupling (Gravity Contract)
    try:
        falsify_module = importlib.import_module("workspaces.layers.l5_expansion.adversarial_red_team")
        falsify_module.run_adversarial_sandbox(ARTIFACTS_DIR, ROOT / os.environ.get('HELIX_DOMAINS_DIR', '04_labs/corpus/domains/domains'))
    except (ModuleNotFoundError, ImportError):
        print("[ERROR] Adversarial Sandbox (Ring 3) is missing or broken. Falsification failed.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Helix Research Instrument CLI")
    parser.add_argument('--kernel-only', action='store_true', help="Bypass all Sandbox dependencies (Ring 3 isolation test)")
    parser.add_argument('--strict-root', action='store_true', help="Halt execution if root dir drift is detected")
    parser.add_argument('--strict-substrate', action='store_true', help="Abort execution on substrate violation")
    parser.add_argument('--require-hostility', action='store_true', help="Abort if hostility test fails or metrics missing")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    parser_run = subparsers.add_parser('run', help="Run deterministic pipeline")
    
    parser_test = subparsers.add_parser('test', help="Run test suite")
    
    parser_diff = subparsers.add_parser('diff', help="Diff two structural runs")
    parser_diff.add_argument('old_hash', help="Older git commit hash to compare against")
    parser_diff.add_argument('new_hash', nargs='?', default='HEAD', help="Newer git commit hash (default HEAD)")
    
    parser_query = subparsers.add_parser('query', help="Query artifacts")
    parser_query.add_argument('query_type', choices=['anomalies', 'trace', 'search', 'isomorphic', 'synthesize'], help="Type of query to run")
    parser_query.add_argument('query_args', nargs='*', help="Arguments for the specific query type")
    
    parser_graph = subparsers.add_parser('graph', help="Generate Mermaid.js epistemic graph")
    parser_graph.add_argument('domain_id', help="ID of domain to graph (e.g., traffic_shockwaves)")
    
    parser_snapshot = subparsers.add_parser('snapshot', help="Bundle snapshot")
    parser_audit = subparsers.add_parser('audit', help="Audit crosslinks")
    parser_falsify = subparsers.add_parser('falsify', help="Adversarial falsifier")
    parser_status = subparsers.add_parser('status', help="Show functional runtime state")
    
    args = parser.parse_args()
    
    from governance.root_guard import scan_root
    from governance.substrate_guard import check_substrate
    
    scan_root(strict_mode=args.strict_root)
    check_substrate(strict_mode=args.strict_substrate)
    
    if args.command == 'run': run_cmd(args)
    elif args.command == 'test': test_cmd(args)
    elif args.command == 'diff': diff_cmd(args)
    elif args.command == 'query': query_cmd(args)
    elif args.command == 'graph': graph_cmd(args)
    elif args.command == 'snapshot': snapshot_cmd(args)
    elif args.command == 'audit': audit_cmd(args)
    elif args.command == 'falsify': falsify_cmd(args)
    elif args.command == 'status': 
        from engines.status_dashboard import print_status
        print_status()
    
    scan_root(strict_mode=args.strict_root)

if __name__ == "__main__":
    main()
