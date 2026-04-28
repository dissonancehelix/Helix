# Next Run — Live Test 3: Inspection Deepening / Collapse

**Test ID:** `ont_003_inspection`
**Run type:** Live operator — scored by you, not by model inference.
**Priority:** Highest-value next run. TEST 3 has the strongest discriminating power in the suite and the most immediately actionable format.
**Scoring file:** `live_test_003_items.jsonl`
**Scoring sheet:** `live_test_003_scoring_sheet.md`
**Output report:** Write completed run to `runs/ont_003_inspection_run_02.md`

---

## Purpose

Measure whether your reaction to an object deepens or collapses after inspection.

The core hypothesis: surfaces are portals, not destinations. Objects with coherent interior structure reward inspection — each layer reveals more. Objects that are surface-only collapse the moment you look past the facade.

This test does work a preference rating cannot do. Initial rating and post-inspection rating are both required. The delta is the measurement.

---

## What "Inspection" Means

Inspect at four layers, in order:

1. **Surface** — first impression. What do you notice? What's the immediate aesthetic signal?
2. **Context / metadata** — who made this, when, under what constraints, for what purpose? Does knowing this change anything?
3. **Mechanics** — how does it work internally? What decisions were made? What structure is present or absent underneath?
4. **Recursive interior** — does the interior model itself? Does looking at the structure reveal something about the system's self-understanding, or expose that no self-understanding is there?

Rate after each layer if you can. Minimum: rate before and after the full ladder.

---

## Required Item Categories

You need at least one item per domain. Aim for two where possible.

| Domain | What to use | What "inspection" means |
|---|---|---|
| **music** | A track you haven't analyzed before — ideally one with ambiguous initial response | Listen first. Then look up composer, context, production notes, structure. Re-listen with that knowledge. |
| **attraction / face** | A photo, video, or person you encountered recently — initial response known | Go past first impression: voice, posture, how they speak, what they avoid saying, how they handle contradiction. |
| **games / media** | Something you started but haven't finished — or something you finished but haven't reflected on | Past surface playthrough: look at design decisions, authorial intent, what the game thinks it's teaching you. |
| **workspace / folder structure** | Any folder structure you didn't design — inside Helix or external | Does it have a real interior? Does the structure protect something? Or is it a bucket with a label? |
| **people / characters** | A fictional character or real person you've interacted with recently | Past behavior: does the stated interior (values, personality) match what actually governs them at the threshold? |

---

## Item Template

Use this for each item. Fill in every field. If a field is genuinely unknown, write `unknown` — do not leave blank.

```
- item_id: [domain_shortcode]_[sequential number] — e.g. music_001, face_001, game_001
- domain: music | attraction_face | games_media | workspace_folder | people_characters
- item_label: [brief descriptive name — not a formal title, just enough to identify it]
- initial_rating_0_5: [0–5 integer]
- initial_reason: [one to three sentences — what produced the initial rating]
- inspection_steps:
    - step_1_surface: [what you noticed at surface level]
    - step_2_context: [what context/metadata added or subtracted]
    - step_3_mechanics: [what examining the internal structure revealed]
    - step_4_recursive: [whether a genuine interior was present or exposed as absent]
- discovered_structure: [what did you find that you didn't know at initial rating?]
- post_inspection_rating_0_5: [0–5 integer]
- delta: [post minus initial — can be negative]
- result_type: deepened | collapsed | unchanged | ambiguous
- notes: [anything anomalous, domain-specific, or that the schema doesn't capture]
```

---

## Result Type Definitions

| Type | Criteria |
|---|---|
| `deepened` | delta ≥ +1 and post-inspection rating ≥ initial; inspection confirmed or exceeded expectation |
| `collapsed` | delta ≤ −1 and post-inspection rating ≤ initial; inspection exposed surface-only construction |
| `unchanged` | delta = 0; inspection neither revealed new structure nor exposed absence |
| `ambiguous` | delta = 0 but response character shifted; or delta diverges from predicted direction; needs notes |

**Important:** Social collapse and artifact collapse are not equivalent even when delta is identical. A collapsed NPC (delta −4, active contempt) and a collapsed ambient track (delta −2, inertness) differ in response character. Note domain when recording collapse.

---

## What Makes a Good Test Item

**For deepening:** Pick something with ambiguous or modest initial rating where you suspect there might be more. Don't pick something you already know is deep — the inspection must be live, not a confirmation of prior knowledge.

**For collapse:** Pick something with a surface that attracted you without much examination. Influencer-aesthetic items, polished but generic tracks, well-written profiles where the writing might be the whole thing.

**Avoid:** Items you've already analyzed extensively. The model run used Outer Wilds and the articulate NPC as archetypes — don't re-score these. Use new material.

---

## Scoring Notes for This Run

- Rate initial_rating before any inspection steps. Commit to it.
- Do not revise initial_rating after the fact. Record what you actually thought before you looked.
- If collapse happens mid-inspection (you don't need to finish the ladder), note at which step it triggered.
- The test is measuring the delta, not the final rating. A 2 → 5 and a 4 → 5 are different results.

---

## Output

When complete, write results to:
`labs/research/personal_ontology/tests/runs/ont_003_inspection_run_02.md`

Use `system/engine/run/templates/test_report_template.md` as the base structure.

Flag any item where the result falsifies or pressures the model prediction from Run 01 (see `reports/mini_test_001.md`).

