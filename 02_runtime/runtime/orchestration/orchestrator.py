import sys
import subprocess
import os
from pathlib import Path

# Helix — Layer 0 Orchestrator
# Enforces the execution of the Constraint Pyramid layers.

ROOT = Path(__file__).resolve().parent.parent.parent
# Corrected: Parent of orchestration is runtime, parent of runtime is Helix root.

# Centralized list of modules to execute in order
PYRAMID_EXECUTION_PLAN = [
    # Infrastructure & Platform
    "runtime/infra/platform/environment.py",
    
    # Layer 3 — Primitives
    "04_workspaces/workspaces/layers/l3_primitives/run_minimal_constraints.py",
    
    # Layer 2 — Structural Elements
    "04_workspaces/workspaces/layers/l2_elements/eigenspace_tracker.py",
    "04_workspaces/workspaces/layers/l2_elements/eip_module.py",
    "04_workspaces/workspaces/layers/l2_elements/expression_kernel.py",
    "04_workspaces/workspaces/layers/l2_elements/deep_layer_compression_suite.py",
    
    # Layer 4 — Generative Operators
    "04_workspaces/workspaces/layers/l4_operators/operator_composer.py",
    "04_workspaces/workspaces/layers/l4_operators/triad_necessity_lab.py",
    "04_workspaces/workspaces/layers/l4_operators/layer3_5_bridge_suite.py",
    "04_workspaces/workspaces/layers/l4_operators/bridge_decoupling_suite.py",
    "04_workspaces/workspaces/layers/l4_operators/emergence_validator.py",
    "04_workspaces/workspaces/layers/l4_operators/structural_chemistry_suite.py",
    "04_workspaces/workspaces/layers/l4_operators/constraint_ecology_suite.py",
    
    # Layer 1 — Phenomena
    "04_workspaces/workspaces/layers/l1_phenomena/fracture_mapper.py",
    "04_workspaces/workspaces/layers/l1_phenomena/rank_collapse_suite.py",
    "04_workspaces/workspaces/layers/l1_phenomena/pathology_probe.py",
    "04_workspaces/workspaces/layers/l1_phenomena/tsm_module.py",
    
    # Layer 5 — Expansion & Stress
    "04_workspaces/workspaces/layers/l5_expansion/numeric_expansion.py",
    "04_workspaces/workspaces/layers/l5_expansion/counterexample_engine.py",
    "04_workspaces/workspaces/layers/l5_expansion/extreme_expansion.py",
    "04_workspaces/workspaces/layers/l5_expansion/hostile_validation.py",
    "04_workspaces/workspaces/layers/l5_expansion/foreign_regime_expansion.py"
]

def execute_pyramid():
    print("Helix: Beginning Pyramid Execution...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    
    for rel_path in PYRAMID_EXECUTION_PLAN:
        abs_path = ROOT / rel_path
        if abs_path.exists():
            print(f"Executing: {rel_path}")
            res = subprocess.run([sys.executable, str(abs_path)], cwd=str(ROOT), env=env)
            if res.returncode != 0:
                print(f"CRITICAL FAILURE: {rel_path} exited with code {res.returncode}")
                sys.exit(1)
        else:
            print(f"Warning: {rel_path} missing. Skipping.")

if __name__ == "__main__":
    execute_pyramid()
