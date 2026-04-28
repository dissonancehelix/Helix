# Helix: The Constraint Engine

Helix is the pure logic engine that governs the Dissonance workspace. 

It is the kernel. It is not the house. It does not contain apps, data, or experiments.

## Core Responsibilities
1. **Schemas:** Defining the cross-domain Pydantic/dataclass structures.
2. **Validation:** Enforcing pre-commit hooks and repository boundary rules.
3. **The Compiler:** The sole write-authority over the Atlas memory.
4. **Immutability:** Managing the WSL-native `chattr +i` locks that protect the Atlas ledger from accidental Windows-side corruption.

Do not place loose scripts or practical tools here.
