# Charge State Specification
**Target Subsystem:** `ChargeStateSystem`

## Formal Condition
`C_active` = `(v_actual >= 300.0) && (IsGrounded == true) && (IsKnocked == false)`

## Rules
- **Threat requirement:** Charge state triggers automatically inside the physics tick.
- **Air-state instant removal:** If a player jumps or falls, `C_active = false`.
- **Boolean flip timing:** Zero interpolation. If the condition drops to `299.9` due to a wall, the boolean is instantly false on that tick.

## Truth Table of State Transitions

| Action | Current Speed | Grounded? | Knocked? | Resulting `C_active` |
|--------|---------------|-----------|----------|----------------------|
| W held | `299.9`       | Yes       | No       | `false`              |
| W held | `300.0`       | Yes       | No       | `true`               |
| W held | `350.0`       | Yes       | No       | `true`               |
| Jump   | `350.0`       | No        | No       | `false`              |
| Land   | `350.0`       | Yes       | No       | `true`               |
| Impact | `350.0`       | Yes       | No       | `true` (wins collision) |
| Impact | `0.0`         | Yes       | Yes      | `false`              |

## Edge-Case Evaluation
- **Frame-perfect jump:** If `IsGrounded` flips false immediately on frame `t`, `C_active(t)` MUST evaluate to false. A player cannot jump and tackle simultaneously.
- **Micro-stutters:** Temporary drops to `299.9` (e.g., from sharp turning) instantly rip authorization.

## Latency Tolerance Bounds
- Predictable locally, but the Server determines the absolute state. If a client mispredicts a sharp turn and evaluates `300.1` locally, while the Server evaluates `299.5`, the Server forcibly revokes `C_active` and the tackle fails. Tolerances: `<1ms` logic delay on fixed server ticks.
