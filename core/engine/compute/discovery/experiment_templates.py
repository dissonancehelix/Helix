"""
Discovery Engine — Experiment Templates
=======================================
Reasoning patterns to map structural Atlas gaps to HIL commands.
"""

TEMPLATES = {
    "PROBE": {
        "reasoning": "Invariant has few confirmations",
        "command": "PROBE invariant:{id}",
    },
    "SWEEP": {
        "reasoning": "Parameter sensitivity unknown",
        "command": "SWEEP parameter:{id} range:0..1 steps:10",
    },
    "VALIDATE": {
        "reasoning": "Graph relationship uncertain",
        "command": "VALIDATE experiment:{id}",
    },
    "CROSS_DOMAIN": {
        "reasoning": "Invariant appears across domains",
        "command": "DISCOVER crossdomain invariant:{id}",
    }
}
