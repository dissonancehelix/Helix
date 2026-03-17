# Movement Validation Specification
**Target Subsystem:** `EftMovementController`

## 1. Acceleration Curve Formula
*   **Mathematical Model:** `v(t) = min(V_max, v(t-1) + dt * (15 + 0.5 * (400 - v(t-1))) * 5.0)`
*   **Validation Condition:** Time to reach 350 HU/s starting from 0 HU/s on a flat surface.
*   **Pass/Fail Threshold:** Exactly `1.5` seconds (+/- 0.05s).
*   **Numeric Tolerance:** `<= 1%` drift.

## 2. Maximum Speed Cap
*   **Mathematical Model:** `V_max = 350.0 HU/s`
*   **Validation Condition:** Ground velocity after 3 seconds of holding forward on an infinite flat plane.
*   **Pass/Fail Threshold:** Exact peak velocity equals `350.0`.
*   **Numeric Tolerance:** `0%` drift. Must strictly clamp.

## 3. Charge Threshold
*   **Mathematical Model:** `C_active = (v_current >= 300.0) && IsGrounded == true`
*   **Validation Condition:** Boolean `ChargeState` evaluates to true precisely when velocity crosses `300.0`.
*   **Pass/Fail Threshold:** `true` at `300.000` or above.
*   **Numeric Tolerance:** No interpolation. Hard boundary.

## 4. Wall Collision Zeroing Rule
*   **Mathematical Model:** `If Dot(VelocityVector, WallNormal) < 0.7, v_current = 0`
*   **Validation Condition:** Player hits a 90-degree wall at `350` HU/s.
*   **Pass/Fail Threshold:** X and Y velocity components instantly become `0.0` within exactly 1 tick.
*   **Numeric Tolerance:** Must zero out completely. No residual slide.

## 5. Jump / Air Charge Stripping
*   **Mathematical Model:** `v_air_z = 200.0` | `IsGrounded = false` -> `C_active = false`
*   **Validation Condition:** Player presses jump while `v = 350`.
*   **Pass/Fail Threshold:** `C_active` sets to `false` in the exact tick `IsGrounded` triggers false.
*   **Numeric Tolerance:** 0 frames latency permitted on state flip.

## 6. Turn-Induced Velocity Decay
*   **Mathematical Model:** Turning strictly decays speed: `v_new = v_current * (1 - max(0, abs(yaw_diff) - 4) / 360)`
*   **Validation Condition:** Sudden 90-degree mouse yaw turn while moving at 350 HU/s.
*   **Pass/Fail Threshold:** Velocity should immediately drop proportional to the angle difference past the 4-degree grace threshold.
*   **Numeric Tolerance:** `<= 1%` drift from original Source 1 formula scale.
