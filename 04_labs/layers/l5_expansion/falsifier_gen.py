#!/usr/bin/env python3
import sys
import json

def generate_falsifiers(claim_id):
    return [
        {"title": "Extreme limit of each observable", "template": f"Push observables in {claim_id} to +/- infinity until metric diverges."},
        {"title": "Topology toggle", "template": f"Change topology of state space in {claim_id}, expect discontinuous failure."},
        {"title": "Perturbation amplification", "template": f"Increase perturbation delta in {claim_id} and observe collapse trajectory."},
        {"title": "Timescale inversion", "template": f"If slow-varying, make fast-varying in {claim_id}."},
        {"title": "Noise-construction regime", "template": f"Remove noise entirely in {claim_id} to see if order is lost."}
    ]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: falsifier_gen.py <claim_id>")
        sys.exit(1)
    print(json.dumps(generate_falsifiers(sys.argv[1]), indent=2))
