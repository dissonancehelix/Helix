# Helix: The Constraint Engine

Helix's core engine is the shared logic and validation layer that governs the
workspace.

It is the nervous machinery. It is not the house. Domain-owned tools, data, and
experiments belong inside `domains/<domain>/`.

## Core Responsibilities
1. **Schemas:** Defining the cross-domain Pydantic/dataclass structures.
2. **Validation:** Enforcing pre-commit hooks and repository boundary rules.
3. **The Compiler:** The sole write-authority over the Atlas memory.
4. **Immutability:** Managing the WSL-native `chattr +i` locks that protect the Atlas ledger from accidental Windows-side corruption.

Do not place loose scripts or domain workflows here.
