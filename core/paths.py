from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / 'docs'
CORE_ROOT = REPO_ROOT / 'core'
CODEX_ROOT = REPO_ROOT / 'codex'
LIBRARY_ROOT = CODEX_ROOT / 'library'
ATLAS_ROOT = CODEX_ROOT / 'atlas'
DOMAINS_ROOT = REPO_ROOT / 'domains'
LABS_ROOT = REPO_ROOT / 'labs'
LAB_DATASETS_ROOT = LABS_ROOT / 'datasets'
EXPERIMENTS_ROOT = LABS_ROOT / 'experiments'
EXECUTION_ROOT = REPO_ROOT / 'execution'
ARTIFACTS_ROOT = EXECUTION_ROOT / 'artifacts'
RUNS_ROOT = EXECUTION_ROOT / 'runs'
LOGS_ROOT = EXECUTION_ROOT / 'logs'
INTEGRITY_ROOT = EXECUTION_ROOT / 'integrity'
APPLICATIONS_ROOT = REPO_ROOT / 'applications'


def ensure_runtime_dirs() -> None:
    for path in (
        CODEX_ROOT,
        LIBRARY_ROOT,
        ATLAS_ROOT,
        LAB_DATASETS_ROOT,
        ARTIFACTS_ROOT,
        RUNS_ROOT,
        LOGS_ROOT,
        INTEGRITY_ROOT,
    ):
        path.mkdir(parents=True, exist_ok=True)
