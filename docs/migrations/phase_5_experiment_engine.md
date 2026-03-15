# Helix Phase 5 — Experiment Engine + Discovery Automation

Date: 2026-03-15
Executor: Helix Automated Orchestrator

## 1. Experiment Architecture
- Configured a YAML-based Sweep Config schema under `04_labs/experiments/` mapping out exact permutations for dimensions like `agent_count`, `competition_strength`, `topology`, and more.
- Built parameter generator for autonomous dataset generation mapping combinatorial expansions to precise structures parsed by arbitrary probes.

## 2. Parameter Sweep Engine
- Orchestrated concurrent execution across multi-core systems natively targeting the `sandbox_runner`.
- Stores completely serialized isolated run folders safely under `07_artifacts/experiments/<experiment_name>/<run_id>/`

## 3. Cross-Probe Analysis
- Analyzed and successfully evaluated the capacity to correlate multi-probe outputs.
- Retained Pearson correlation models across datasets validating signals mapping metrics like `domain_overlap` and structural alignment (`pearson_r`).

## 4. Regime Detection
- Engineered `03_engines/analysis/regime_detection.py` resolving exact bounding domains mapping where invariants emerge or collapse securely into `regime_map.json`.

## 5. Atlas Extensibility
- Repurposed `03_engines/atlas/atlas_builder.py` to seamlessly ingest outputs from `regime_map.json` into final invariant knowledge graphs (`06_atlas/*.json`).
- Enables `parameter_regimes` to be dynamically captured and recorded in the canonical representation.
