import json
import time
from pathlib import Path

PANIC_TYPES = [
    "INSTRUMENT_INPUT_IMPURITY",
    "INSTRUMENT_THROUGHPUT_STARVATION",
    "INSTRUMENT_NONDETERMINISM",
    "INSTRUMENT_TRACE_ROT",
    "INSTRUMENT_KERNEL_MUTATION",
    "EXECUTION_OVERFLOW"
]

def emit_panic(artifacts_dir: Path, panic_type: str, layer: str, triggering_artifact: str, dataset_hash: str):
    if panic_type not in PANIC_TYPES:
        panic_type = "INSTRUMENT_KERNEL_MUTATION"
        
    print(f"\n[!!!] HALT: PANIC EMITTED [!!!]")
    print(f"Type: {panic_type}")
    print(f"Layer: {layer}")
    print(f"Trigger: {triggering_artifact}")
    
    health_dir = artifacts_dir / "instrument_health"
    health_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "panic_type": panic_type,
        "layer": layer,
        "triggering_artifact": triggering_artifact,
        "dataset_hash": dataset_hash,
        "timestamp": time.time(),
        "status": "PANIC_LOCKED"
    }
    
    with open(health_dir / "panic_report.json", "w", encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    registry_file = health_dir / "instrument_failure_registry.json"
    registry = []
    if registry_file.exists():
        with open(registry_file, 'r') as f:
            registry = json.load(f)
    registry.append(report)
    with open(registry_file, "w") as f:
        json.dump(registry, f, indent=2)
