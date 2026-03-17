# Throw Commitment Specification
**Target Subsystem:** `InventoryComponent / ThrowSystem`

## Formalization
Throwing is the longest voluntary vulnerability state. It requires total forfeiture of movement.

### Speed Clamp Rule
- During the `[WINDUP]` state, max forward/sideways/backward movement is explicitly zeroed (0 HU/s).
- **Previous Value:** 100 HU/s (Draft/Attempted). **Corrected Protocol Contract:** 0 HU/s.

### Immediate Clamp on Activation
The exact frame the client signals right-click hold (Windup initiated), the `EftMovementController` receives an absolute command `MaxVelocity = 0`. Acceleration ceases.

### Immediate Release on Cancel
If windup is aborted (input released below threshold, or cancel key pressed), `MaxVelocity` returns to `262.5 HU/s` (Carrier speed). **Zero acceleration memory retention** — player must re-accelerate from `0`.

### No Sliding Exploit
A bug native to old Source involved jumping *before* throwing to maintain horizontal arc momentum while throwing. This is permitted if `IsGrounded` evaluating false, but the player gives up all steering control and charge state.

### Exploit Detection Edge Cases
- **Strafing during windup:** Client `tick` processing must zero A/D inputs. Movement code evaluates to 0 regardless of keyboard input array.
- **Tackled mid-windup:** Windup aborted, `State = [KNOCKED]`, Throw impulse cancelled, Ball yields as an standard fumble instead of a parabolic pass arc.
