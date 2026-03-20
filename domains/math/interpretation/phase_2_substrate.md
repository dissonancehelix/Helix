# Phase 2 — WSL2 Substrate Hardening

**Date:** 2026-03-15

## Summary
Added substrate enforcement and sandboxing infrastructure to 03_engines.
No changes to 00_kernel, 01_basis, or 02_governance.

## New Files

| File | Purpose |
|------|---------|
| `03_engines/substrate/sandbox_runner.py` | Subprocess probe execution with env injection |
| `03_engines/substrate/kernel_lock.py` | chattr +i on 00_kernel/ (Linux/WSL2) |
| `03_engines/substrate/architecture_watchdog.py` | Periodic integrity polling |
| `03_engines/runtime_hooks/artifact_lock.py` | chattr +i on artifact run dirs |

## CLI Additions
- `helix lock-kernel` / `unlock-kernel` / `kernel-status`
- `helix watchdog-start`

## Windows Note
chattr enforcement is Linux/WSL2 only. Windows logs a warning and continues.
