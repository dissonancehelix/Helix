# EIP Python Implementation
**Canonical implementation of the Epistemic Irreversibility Principle.**

## Structure
- **core/**: Essential math primitives (`keff.py`), threat models (`threat_model.py`), and experiment runners (`suite_runner.py`).
- **suites/**: Grouped test runners for stress testing and hostile environment validation.
- **experiments/**: Focused research scripts for Scarcity Gap, Interaction Asymmetry, and Locality Horizons.
- **results/**: Consolidated technical data and findings.

## Usage
Run the master suite for full validation:
```bash
python python/suites/master_suite.py
```
