# Collision Resolution Specification
**Target Subsystem:** `CombatResolutionSystem`

## Formalization
When two players with `BoundingRadius` intersection collide, resolve tackle outcome based on authoritative Server Physics.

### Pre-collision Velocity Sampling
Velocity must be sampled on the exact tick *before* physical collision repulsion math is applied by the engine, otherwise physics clipping may alter speed values artificially.

### Head-On Vector Comparison Method
1. Determine intersection.
2. Check `C_active(A)` and `C_active(B)`.
3. If both `true`, execute `HeadOnResolve(v_A, v_B)`.
4. If one `true` and one `false`, the `true` agent applies Knockdown to the `false` agent.

### Vector Comparison Math
```csharp
// Both are charging
float diff = Math.Abs(v_A.Magnitude - v_B.Magnitude);

if (diff < 24.0f) {
   // Tie-breaking rule / Close outcome
   ApplyMutualKnockback(A, B); 
} else if (v_A.Magnitude > v_B.Magnitude) {
   ApplyKnockdown(B, A.VelocityVector);
} else {
   ApplyKnockdown(A, B.VelocityVector);
}
```

### Server-Authoritative Enforcement
Client-predicted impacts must only play visual UI feedback. Server strictly evaluates the magnitude on its tick memory representation and issues discrete RPC events indicating exactly who fell.

### Edge-Case Handling
- **Equal Speed:** Yields mutual stun with faster recovery times (Head-On Mutual Knockback).
- **Diagonal Collisions:** Resolved strictly via magnitude array checks, disregarding approach angle if bounding boxes intersect.
