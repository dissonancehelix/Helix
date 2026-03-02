# Helix Ring 0: Feasibility Coordinates
# SACRED: No non-stdlib imports.

class FeasibilityCoordinate:
    def __init__(self, id, name, condition):
        self.id = id
        self.name = name
        self.condition = condition

COORDINATES = {
    "SF1": FeasibilityCoordinate("SF1", "Latency Ratio", "feedback_delay < runaway_timescale"),
    "SF2": FeasibilityCoordinate("SF2", "Observability Locality", "state is measurable (LOCAL/GLOBAL)"),
    "SF3": FeasibilityCoordinate("SF3", "Enforcement Topology", "enforcement_authority is (PROTOCOL/CENTRAL)"),
    "SF4": FeasibilityCoordinate("SF4", "Time Constant Compatibility", "controller_update_rate > disturbance_rate")
}

def get_coordinate(sf_id):
    return COORDINATES.get(sf_id)
