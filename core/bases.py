# Helix Ring 0: Structural Bases
# SACRED: No non-stdlib imports. No upward dependencies.

class StructuralBasis:
    def __init__(self, id, name, description, topological_proxy):
        self.id = id
        self.name = name
        self.description = description
        self.topological_proxy = topological_proxy

BASES = {
    "B1": StructuralBasis(
        "B1_BASIN",
        "Basin Commitment",
        "Scalar boundary on energy or effort required to transition between macro-states.",
        "Delta energy gap / Defect amplitude"
    ),
    "B2": StructuralBasis(
        "B2_EXPRESSION",
        "Expression Capacity",
        "Volumetric boundary bounding total combinatorially resolvable states.",
        "State-space dimensionality span"
    ),
    "B3": StructuralBasis(
        "B3_COORDINATION",
        "Coordination Complexity",
        "Graph matrix limitation tracking the depth of required multi-agent coupling.",
        "Graph clustering coefficient / Adjacency dependencies"
    ),
    "B4": StructuralBasis(
        "B4_SYMBOLIC_DEPTH",
        "Symbolic Depth",
        "Limits on referential abstraction logic layers before execution recursion saturates.",
        "Policy stack depth / Abstraction pointer nesting"
    )
}

def get_basis(basis_id):
    return BASES.get(basis_id)
