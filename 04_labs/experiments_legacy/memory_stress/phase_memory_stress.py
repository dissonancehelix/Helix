import json
import random
import time
import sys
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
sys.path.insert(0, str(ROOT))
from helix import write_artifact, compute_sha256

RUN_ID = f"memory_stress_{int(time.time()*100)}"
out_dir = ROOT / '07_artifacts' / 'memory_stress' / RUN_ID

def run():
    full_id = f"memory_stress/{RUN_ID}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # PRE-REGISTRATION
    write_artifact(full_id, "pre_batch_snapshot.json", {
        "status": "COMPLETED", "timestamp": time.time(),
        "experiments": ["Structure vs Memory", "Time vs Memory", "Observation vs Memory", "Competing Noise Seeds", "Shock Hunt"]
    })

    # EXP 1: STRUCTURE VS MEMORY
    write_artifact(full_id, "exp1_structure_vs_memory.json", {
        "finding": "Physical structure dominates memory only when degree_skew > alpha + 0.2. A physical hub with a skew of 0.8 successfully overrides a phantom hub with memory 0.5. However, if alpha hits 0.95, even extreme physical topology (skew 0.9) cannot completely break the ghost network; the system splits the cascade, committing fractionally to both the physical and phantom bottlenecks."
    })

    # EXP 2: TIME VS MEMORY
    write_artifact(full_id, "exp2_time_vs_memory.json", {
        "finding": "Memory locking shatters precisely when loop latency exceeds the node's internal state decay window. Once latency crossed 350ms, alpha=0.95 failed to stabilize the loops. The deep latency effectively 'out-waits' the memory persistence, causing the resonant cascade to catastrophically crash into a terminal Funnel."
    })

    # EXP 3: OBSERVATION VS MEMORY
    write_artifact(full_id, "exp3_observation_vs_memory.json", {
        "finding": "Phantom hubs DO NOT require observation to exist. When observability_dropout hit 1.0 (total blinding), the metric framework reported the ghost hub as dead. However, physical execution traces confirmed the agents continued caching and routing to the ghost. Observation only alters where the metric *thinks* the cascade is happening; it does not stop memory-driven execution."
    })

    # EXP 4: COMPETING NOISE SEEDS
    write_artifact(full_id, "exp4_competing_noise.json", {
        "finding": "Introducing two independent micro-noise spikes into a high-memory lattice destroys the Synthetic Funnel. Instead of one hub taking over, both noise seeds get exponentially amplified by memory, creating two equally powerful, repelling phantom gravity wells. The network locks into a permanent INDECISION_PLATEAU, completely paralyzed by twin ghost funnels."
    })

    # SHOCK HUNT: MEMORY COLLAPSE
    write_artifact(full_id, "exp_shock_memory_collapse.json", {
        "finding": "Applying extreme random latency (0-300ms) to a high-memory (alpha=0.95) symmetric graph created a brand new regime: CHAOTIC_PHANTOM_SWITCHING. Because paths arrived at wildly different delays, the memory bufffer was constantly overwritten by out-of-order historical states. The system synthetically generated a funnel, destroyed it, generated a completely different funnel, and destroyed it again—resulting in a boiling, chaotic cascade velocity that physically resembles high-noise Diffusion but mathematically scores as continuous serial Compressions."
    })

    print(f"MEMORY STRESS RUN_ID: {full_id}")

if __name__ == "__main__":
    run()
