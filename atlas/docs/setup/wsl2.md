# WSL2 Setup for Helix Substrate

Helix substrate hardening features (kernel lock, artifact lock) require Linux/WSL2.

## Setup

```bash
wsl --install -d Ubuntu
wsl
cd /home/dissonance/Helix  # or mount Windows path
```

## Kernel Lock

```bash
python helix.py lock-kernel    # chattr +i on 00_kernel/ (requires sudo in WSL2)
python helix.py kernel-status  # verify lock state
```

## Artifact Immutability

Probe run artifacts are locked with `chattr +i` after write on WSL2.
On Windows, a warning is logged but execution continues.

## Sandbox Runner

All probes execute as subprocesses with `HELIX_SYSTEM_INPUT` and `HELIX_ARTIFACT_DIR`
environment variables set. No network, no write outside artifact dir.
