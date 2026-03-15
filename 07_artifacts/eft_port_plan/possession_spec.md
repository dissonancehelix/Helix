# Possession & Speed Penalty Specification
**Target Subsystem:** `PossessionSystem`

## Formalization
Possession is an absolute boolean state tracked by the Server. It triggers implicitly on contact, dropping the speed limit of the carrier.

### The Immediate Contact Rule
- No delay or input gating.
- If an entity intersects the ball entity's trigger volume, the ball attaches instantly.

### Speed Multiplier Precision
- `CarrierMaxSpeed = V_max * 0.75`
- Evaluates strictly to `350.0 * 0.75 = 262.5 HU/s`.

### Fumble Trigger Conditions
1. **Knockdown triggers Fumble:** If `PossessionSystem` reads `KnockedStatus == true`, instantly unparent Ball entity, apply `1.75 * Carrier.Velocity` ejection impulse.
2. **Throw command:** Player invokes throw windup sequence.
3. **Invalidations (Wall strikes):** A player dropping from 262.5 to 0 because they collided with a wall does **NOT** trigger a fumble. The physics deceleration drops speed, but the ball remains attached.

### Possession State Machine
```
[LOOSE BALL]
     |
     v (Any Hull intersect)
[CARRIER] --> Speed Cap = 262.5 HU/s
     |
     +--> (Event: Wall Hit) -> Velocity = 0; State = [CARRIER]
     |
     +--> (Event: Tackle) -> Velocity = 0; State = [KNOCKED] -> [LOOSE BALL]
     |
     +--> (Event: Release Throw) -> State = [LOOSE BALL_AIRBORNE]
```
