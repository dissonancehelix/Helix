# Extreme Football Throwdown: S&box Architecture Plan

## 1. Subsystem Boundaries (ECS Abstraction)
The port to S&box drops Garry's Mod monolithic `__index` OOP behavior in favor of strict, componentized systems:
*   **Physics Translation Layer (`EftMovementController`):** Recreates the specific `(15 + 0.5 * (400 - curspeed)) * acceleration` Havok-quirk physics logic and wall-slam cancellation. This is the bedrock; if movement feels wrong, EFT breaks.
*   **State Machine Component (`ChargeStateSystem`):** A strictly polling component that checks `Velocity > 300` AND `IsGrounded` to flip a boolean `IsThreat`. 
*   **Interaction Manager (`CombatResolutionSystem`):** Computes head-on trajectory margins. Replaces the old `Touch` hook mess into deterministic bounding-box raycasts ahead of the player hull.
*   **Possession Arbiter (`PossessionSystem`):** Handles `HasBall`, sets the 0.75x max speed penalty, and triggers fumble instances.

## 2. ECS Component Mapping
*   **`PlayerComponent`** (Base Identity)
*   **`TackleHitboxComponent`** (Predictive bounding radius for hits)
*   **`BallMagnetComponent`** (Detects touching the loose ball)
*   **`KnockedStatusComponent`** (Handles 2.75s timer, disables input vectors)
*   **`InventoryComponent`** (Strictly limits holding to `1`, handles the wind-up lock state)

## 3. Networking Strategy
S&box relies heavily on Client-Side Prediction to avoid latency feeling awful.
*   **Fully Predicted (Client & Server):** Movement acceleration, Charge Threat generation, jumping, jumping-penalty.
*   **Server Authoritative (Client interpolates):** Tackle collisions, Ball physics, Fumbles, Goal Triggers, Respawns.
*   *Why?* The exact margin of a 358 HU/s vs 357 HU/s head-on collision must be globally undisputed. A client thinking they won a tackle and rubber-banding backwards is unacceptable. The Server mandates the tackle winner.

## 4. Rewrite vs Restructure
**What must be strictly completely REWRITTEN:**
*   **Movement hooks.** S&box's `CharacterController` works vastly differently than Source 1's `SetupMove`. The air strafe cap and "curve" grace period must be written manually to simulate old engine jank.
*   **Punch Cross-Counter timings.** The `0.2s` window needs a precision timer based on actual animation frame events, not `RealTime()`.
*   **Ball Physics.** Havok physics on prop_physics are not 1:1 with S&box's physics engine. Damping and restitution values (`0.01` linear, `0.25` angular) will need manual tuning against the new physics solver.

**What can be RESTRUCTURED (Ported Logic):**
*   Tackle force math (`velocity * 1.65`).
*   Knockdown immunities (`0.45` post-hit, `2.0` anti-stunlock).
*   Scoreboard counting logic and match timing (`15` minute loop, `20`s reset).

## 5. Phased Roadmap

### **Phase 1: The Movement Sandbox**
*   Build the `EftMovementController`.
*   Replicate the 350 MAX speed, 1.5s acceleration curve, and wall-penalty instantly zeroing velocity.
*   *Validation:* Does turning sharply cause a predictable speed drop? Does jumping strip the ability to turn cleanly?

### **Phase 2: The Charge & Interaction Core**
*   Implement `ChargeStateSystem` and `KnockdownStatusComponent`.
*   Establish Head-on logic. Two bodies colliding must output a discrete winner and apply the stun state.
*   *Validation:* Can two players consistently resolve a head-on by out-curving each other?

### **Phase 3: The Ball Domain**
*   Create `BallEntity` and Auto-Pickup logic.
*   Implement the 75% carrier penalty.
*   Implement fumble spawning upon the carrier receiving `KnockdownStatus`.
*   *Validation:* Can the carrier realistically survive ~2 seconds before a 350-speed attacker closes the gap?

### **Phase 4: Advanced Combat & Passing**
*   Implement the 1-second pass windup (speed capped to 0).
*   Implement Air Dives and Punch Cross-Counters.
*   *Validation:* Does throwing feel incredibly dangerous and punishable?

### **Phase 5: Arena and Goals**
*   Implement Goal Zones.
*   Implement Hazard triggers (Lava, Void, Water).
*   Implement `20`s match stall resets.
*   *Validation:* Does the system continuously cycle interaction -> score -> reset -> engagement?
