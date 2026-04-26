# Genesis VGM Remaster + Spatial Engine

## Purpose

Build an offline **Genesis / Mega Drive VGM remaster engine** whose primary target is:

> **headphone listening with extreme spatial immersion and higher-budget timbral realization**

The project should produce:

1. **Original Reference** — faithful stereo render for comparison/debugging only
2. **Remaster + Spatial (Headphone Target)** — the main deliverable

The original is never replaced.
The remaster exists in parallel.

This project is not centered on archival emulation fidelity.
It is centered on:

* sounding dramatically better
* preserving recognizability
* using source-channel structure intelligently
* pushing Genesis music toward a richer FM realization and a much more immersive headphone scene

---

## What I Actually Want

I do **not** need a separate "Accurate+" listening mode as a core goal.

I want:

* a faithful stereo **reference** render for A/B comparison
* a **full remaster + spatial output** aimed at headphones
* a pipeline that starts with a **7.1 intermediate scene** if useful
* but is architected so it can later evolve into an **object-based / Ambisonic-style intermediate scene** before binaural output

For headphones, the real ceiling is not just "7.1 binaural".
The better long-term model is:

> channel or role objects -> spatial scene -> binaural render

So the design should treat **7.1 as the first practical milestone**, not the ultimate conceptual limit.

---

## Core Idea

Do **not** start from a finished stereo mix and try to widen it.

Start from the causal source structure:

* YM2612 FM channels
* SN76489 PSG channels
* DAC stream / sample usage
* timing / loop structure
* per-channel musical role inference

Then:

* render source buses first
* enhance timbre second
* build a spatial scene third
* binauralize the scene last

This is a **channel-aware remaster engine**, not a generic stereo upmixer.

---

## Why This Is Interesting

Most VGM players answer:

* How do I emulate this accurately?

This project asks:

* How good can Genesis music sound if the timbral budget is expanded?
* How immersive can it become on headphones if channels are spatialized as source objects?
* How can DAC and FM be enhanced without erasing identity?
* How can we approximate a higher-budget FM realization of the same musical ideas?

Genesis music is especially strong for this because it preserves:

* separable FM voices
* separable PSG roles
* DAC percussion/events
* loop structure
* hardware-constrained orchestration choices

---

## Design Principles

### 1. Original remains available

Every remaster output must be directly comparable to a faithful stereo reference render.

### 2. Headphone-first design

The main experience target is headphones.
Spatial architecture should therefore be optimized around binaural output, not speaker-room realism for its own sake.

### 3. Source-aware before effect-aware

Per-channel and per-role rendering comes before stereoization, widening, or virtual surround tricks.

### 4. Identity preservation matters

Enhancement should preserve:

* contour
* groove structure
* phrase logic
* return behavior
* channel-role logic
* overall recognizability

### 5. Timbral ambition is allowed

The goal is not merely "cleaner YM2612".
The goal is a **higher-budget FM realization** that still feels like the same track.

### 6. Surround/spatial is a remix layer, not historical truth

The original soundtrack was not secretly authored for modern surround headphone playback.
Spatial output is an intelligent reinterpretation built from native source structure.

### 7. Start offline

First build an offline renderer and artifact generator. Do not start inside the foobar component.

### 8. Progressive enhancement

Start with channel extraction and a stable 7.1 intermediate scene. Then move into stronger binaural rendering and later object/Ambisonic evolution.

---

## Scope

### In Scope

* Genesis / Mega Drive VGM as first target
* Sonic 3 & Knuckles as initial validation corpus
* stem rendering by chip channel / logical channel
* role inference by section
* 7.1 intermediate scene rendering
* binaural headphone rendering from the scene
* DAC restoration / enhancement
* FM sweetening / patch-aware enhancement
* optional instrument-enhanced remaster mode
* artifact export for listening and analysis

### Out of Scope for Phase 1

* real-time foobar integration
* every chip family at once
* full 122,000-track library support on day one
* fully AI-generated orchestration replacements
* fancy UI
* automatic perfect authorship reconstruction

---

## Target Output Modes

### 1. Original Reference

* faithful stereo render
* baseline comparison/debug path
* no creative processing

### 2. Remaster + Spatial (Main Deliverable)

* full enhanced mode
* richer FM realization
* improved DAC playback
* role-aware spatial scene
* binaural headphone render from the scene
* still recognizably the same composition and track

Optional later:

* alternate binaural decoders
* object-based or Ambisonic intermediate scene
* multichannel exports for speaker testing

---

## What “Better FM” Means

This does **not** mean replacing FM with unrelated orchestral samples.

It means moving the realization closer to a:

> **cleaner, fuller, more expensive DX7-family-style FM presentation**

than the constrained YM2612 implementation alone.

### A. Cleaner presentation of the same FM patch

* higher-quality chip core where useful
* oversampling
* better resampling
* reduced brittle high-edge character
* smoother transients
* better output filtering

**Result:**
The same patch sounds cleaner, fuller, and less fatiguing.

### B. Sweetened FM realization

* mild EQ or harmonic smoothing per role
* better separation between bass / lead / support voices
* psychoacoustic widening for support channels
* optional saturation / analog-body modeling

**Result:**
The same FM design sounds more confident and less cramped.

### C. Patch-aware enhancement

* detect FM patch families by operator behavior / timbral role
* map them to enhanced synthesis templates
* preserve note data, envelope behavior, and musical function

Examples:

* thin FM brass -> fuller but still FM-derived brass-like layer
* glassy bell lead -> richer but still recognizable bell lead
* weak bass patch -> stronger low-end body without changing note identity
* stacked support voices -> more legible and lush without genericizing them

**Result:**
A “what this patch wanted to be” version while still sounding Genesis-derived.

### D. Hybridized realization

* keep original FM as the identity anchor when useful
* add higher-quality FM-compatible reinforcement beneath or around it
* do not fully replace unless in an explicit experimental mode later

**Result:**
More weight, body, and realism without losing the original contour and articulation.

### Guiding rule

The strongest direction is:

* preserve the **musical identity** of the original patch usage
* but do **not** treat the crushed YM2612 presentation as sacred when it limits the experience

---

## What “Better DAC” Means

DAC material often benefits even more than FM.

Possible upgrades:

* cleaner reconstruction / interpolation
* anti-click handling
* bandwidth recovery / gentle restoration
* better transient articulation for kicks/snares
* optional low-end reinforcement
* optional hybrid layering in a dedicated remaster mode

This can make Genesis percussion and sampled hits feel dramatically better without rewriting the composition.

---

## Spatial Strategy

### What spatial should mean here

Not fake roominess applied after stereo.

Instead:

* separate source buses first
* infer musical roles
* place sources intentionally into a scene
* render that scene to binaural headphones

### Intermediate scene strategy

#### Phase 1 target

Use a **7.1 intermediate scene** because it is easier to implement, debug, and monitor.

#### Long-term target

Architect the system so the 7.1 intermediate scene can later be replaced by:

* object-based source placement
* Ambisonic / HOA-style scene representation

So the project should be:

* **7.1-first in implementation**
* **scene/object-oriented in architecture**

### Initial placement rules

* bass: anchored, narrow, front
* melody: front-center or front-wide
* percussion: front-wide with controlled side spread
* support / pads: wider / side / mild rear
* sparkle / noise channels: wider / optional rear bias
* DAC events: front with optional controlled low-frequency support

### Later spatial options

* section-aware placement
* return-aware widening or collapse
* alternate binaural decoders
* object/scene refinement beyond fixed 7.1
* cinematic immersion presets

---

## Architectural Overview

## Pipeline Stages

### Stage 1 — Ingest

**Input:**

* `.vgm` / `.vgz`

**Output:**

* parsed command stream
* chip/channel inventory
* metadata
* loop information

### Stage 2 — Reference Render

**Output:**

* faithful stereo baseline render

### Stage 3 — Channel Bus Render

Render each source channel to its own isolated bus:

* YM2612 ch1
* YM2612 ch2
* YM2612 ch3
* YM2612 ch4
* YM2612 ch5
* YM2612 ch6 / DAC-aware split if needed
* PSG tone/noise buses or logical groups

**Output:**

* per-channel WAV stems
* timing-aligned buses

### Stage 4 — Role Inference

Infer channel function per section or time window:

* melody
* bass
* percussion
* support/pad
* accent/noise/effect

**Output:**

* role timeline
* confidence per assignment

### Stage 5 — FM / DAC Remaster Layer

Apply optional enhancement:

* DAC restoration / shaping
* FM sweetening / patch-aware enhancement
* role-aware EQ / dynamics
* low-end management
* transient shaping

### Stage 6 — Scene Build

Build a spatial scene from enhanced buses and role labels.

**Phase 1 output target:**

* 7.1 scene render

### Stage 7 — Binaural Render

Render the scene to a headphone-optimized binaural output.

**Main output:**

* Remaster + Spatial headphone render

### Stage 8 — Final Artifact Export

Produce:

* Original Reference stereo
* Remaster + Spatial binaural stereo
* optional 7.1 scene export
* optional stems

---

## First Implementation Plan

### Milestone 1

For **3 Sonic 3 & Knuckles tracks**, generate:

* original stereo reference render
* isolated channel stems
* basic role annotations
* first-pass 7.1 scene render
* binaural render from that 7.1 scene
* DAC-enhanced mix
* first light FM-lift remaster + spatial mix

**Goal:**
Prove the full concept works end-to-end for headphones.

### Milestone 2

Expand to **5 to 10 tracks** representing different cases:

* straightforward zone theme
* percussion / DAC-heavy track
* bass-heavy groove track
* track with strong loop / return behavior
* track with dense multi-voice texture
* track where support channels matter heavily

**Goal:**
Stress-test the remaster and spatial model on varied material.

### Milestone 3

Add:

* stronger FM patch-aware enhancement
* better binaural tuning
* optional alternate scene representations
* better role inference
* comparison tooling / listening harness

---

## Module Layout

Suggested repo structure:

```text
remaster_engine/
  ingest/
    vgm_parser/
    metadata/
  render/
    reference_render/
    stem_render/
  analysis/
    role_infer/
    loop_structure/
    patch_fingerprint/
  enhance/
    dac_enhance/
    fm_sweeten/
    hybrid_instrument/
  spatial/
    scene_builder_7_1/
    binaural_render/
    scene_objects/
  mix/
    mode_original_reference/
    mode_remaster_spatial/
  outputs/
    wav/
    stems/
    reports/
    comparisons/
```

---

## Suggested Technical Order

### Phase 1 — Build the stems

This is the foundation. Without isolated buses, everything else is weaker.

**Deliverables:**

* faithful stereo render
* per-channel stems
* timing alignment verified

### Phase 2 — Build the first 7.1 scene

No fancy dynamic motion yet.
Just static role-aware placement.

**Deliverables:**

* 7.1 scene render
* binaural render from the 7.1 scene
* A/B against stereo reference

### Phase 3 — DAC enhancement

Highest audible payoff.

**Deliverables:**

* cleaner drums / hits
* less brittle DAC behavior
* stronger punch in the remaster path

### Phase 4 — FM-lift remaster layer

This is the most important creative layer.
Do not settle for “slightly cleaner YM2612.”
Aim for a richer, more DX7-like FM realization while preserving identity.

**Deliverables:**

* cleaner / fuller FM output
* patch-aware enhancement prototypes
* integrated remaster stems

### Phase 5 — Final headphone remaster render

Combine:

* stems
* roles
* FM enhancement
* DAC enhancement
* 7.1 scene
* binaural output

**Deliverables:**

* Original Reference stereo
* Remaster + Spatial headphone render
* optional 7.1 export for testing

---

## Evaluation Criteria

The engine succeeds if the remaster output is:

* dramatically more immersive on headphones
* clearly more legible
* stronger in bass articulation
* richer in FM presentation
* better in DAC punch and clarity
* still immediately recognizable as the same composition

It fails if:

* spatialization becomes phasey mush
* bass loses definition
* FM identity disappears entirely
* DAC becomes over-processed
* the track stops sounding like the track
* the binaural result sounds big but blurry

---

## Listening Test Questions

For each track and mode, ask:

* Is the groove clearer?
* Is the bass more articulate and satisfying?
* Do the FM parts feel richer and more expensive?
* Are melody and support easier to separate?
* Does the headphone scene feel larger without becoming smeared?
* Does the remaster still feel Genesis-derived rather than generic modern soundtrack sludge?
* Would a fan of the original still recognize the musical identity immediately?

---

## Phase 1 Corpus Recommendation

Use Sonic 3 & Knuckles as the starting test bed because it offers:

* iconic FM material
* DAC percussion cases
* strong bass-driven tracks
* distinct section/loop logic
* enough stylistic variation to expose weaknesses quickly

Select 5–10 tracks with contrasting traits instead of batch-processing the full soundtrack immediately.

---

## Deliverables for Claude Code

Claude should implement:

1. a reference Genesis VGM stereo render path
2. a stem extraction path
3. a first-pass role inference system
4. a 7.1 scene renderer
5. a binaural renderer from the 7.1 scene
6. a DAC enhancement module
7. a strong first-pass FM-lift remaster module
8. a final remaster + spatial headphone render mode
9. comparison artifacts for A/B evaluation

Outputs should include:

* stereo WAVs
* binaural WAVs
* optional 7.1 renders
* isolated stems
* simple JSON/CSV reports describing track/channel/role assignments

---

## Long-Term Possibilities

Once the offline headphone-first system works well, later expansions could include:

* foobar integration
* track presets by game / composer / style
* stronger patch-family remastering
* fingerprint-preserving instrument substitution
* alternate binaural decoders
* object-based or Ambisonic scene representations
* adaptive section-aware spatial movement
* soundtrack-wide remaster profiles

But none of that should happen until the offline renderer already produces clearly better results.

---

## Final Compression

This project is not about replacing Genesis music.

It is about using the unusually rich source structure of VGM to build:

* faithful stereo reference playback
* source-aware spatial scene rendering
* a richer, more expensive FM realization
* stronger DAC presentation
* a truly immersive headphone remaster path

The first practical goal is simple:

> turn Sonic 3 & Knuckles tracks into isolated source buses, then prove that a richer FM realization, stronger DAC treatment, and role-aware scene rendering can produce a dramatically better binaural headphone experience without erasing the track’s identity.
