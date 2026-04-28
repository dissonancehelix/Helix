/*
  prism_params.h — Prism DSP parameter block
  No external dependencies.
  Binary format: MAGIC(u32) + VERSION(u32) + struct payload (POD floats).
  VERSION 2 presets load forward via zero-init of the v3 Advanced fields.
*/
#pragma once
#include <cstring>
#include <cstdint>

struct PrismParams {
    // ---- Core (VERSION 2, layout fixed) ----
    float amount;       // 0-1    (default 0.75)
    float wrap;         // 0-360  (default 90)
    float front_lock;   // 0-1    (default 0.70)
    float rear_amount;  // 0-1    (default 0.55)
    float focus;        // -1..+1 (default 0)
    float bass_anchor;  // 0-1    (default 0.85)
    float soft_objects; // 0-1    (default 0)
    float use_lfe_f;    // 0 or 1, stored as float for POD layout

    // ---- Advanced v3 — Scene Memory / hysteresis ----
    float enable_scene_memory;   // 1.0 = on (default off)
    float scene_memory_amount;   // 0-1 (default 0.50)

    // ---- Advanced v3 — Height Synth ----
    float enable_height_synth;   // 1.0 = on (default off)
    float height_amount;         // 0-1 (default 0.50)

    // ---- Advanced v3 — Source Spread (scaffolding only) ----
    float enable_source_spread;  // 1.0 = on (default off)
    float source_spread_amount;  // 0-1 (default 0.50)

    // ---- Advanced v3 — Directivity (scaffolding only) ----
    float enable_directivity;    // 1.0 = on (default off)
    float directivity_amount;    // 0-1 (default 0.50)

    // ---- Advanced v3 — Near-field Lift (scaffolding only) ----
    float enable_nearfield_lift; // 1.0 = on (default off)
    float nearfield_amount;      // 0-1 (default 0.50)

    // ---- Advanced v3 — Micro-Room early reflections (scaffolding only) ----
    float enable_micro_room;     // 1.0 = on (default off)
    float micro_room_amount;     // 0-1 (default 0.30)

    // ---- Advanced v3 — Tone Layer (scaffolding only) ----
    float enable_tone_layer;     // 1.0 = on (default off)
    float tone_amount;           // 0-1 (default 0.00)

    bool  use_lfe()       const { return use_lfe_f > 0.5f; }
    void  set_use_lfe(bool v)   { use_lfe_f = v ? 1.0f : 0.0f; }

    PrismParams()
        : amount(0.75f), wrap(90.0f), front_lock(0.70f), rear_amount(0.55f),
          focus(0.0f), bass_anchor(0.85f), soft_objects(0.0f), use_lfe_f(0.0f),
          // Advanced v3 — all modules disabled by default
          enable_scene_memory(0.0f), scene_memory_amount(0.50f),
          enable_height_synth(0.0f),  height_amount(0.50f),
          enable_source_spread(0.0f), source_spread_amount(0.50f),
          enable_directivity(0.0f),   directivity_amount(0.50f),
          enable_nearfield_lift(0.0f), nearfield_amount(0.50f),
          enable_micro_room(0.0f),    micro_room_amount(0.30f),
          enable_tone_layer(0.0f),    tone_amount(0.00f)
    {}

    // -----------------------------------------------------------------------
    // Binary serialization
    // -----------------------------------------------------------------------
    static const uint32_t MAGIC   = 0x5053524Du; // 'PRSM'
    static const uint32_t VERSION = 3u;

    // Bytes occupied by the v2 core fields (8 floats, fixed layout).
    static const unsigned V2_CORE_BYTES = 8u * sizeof(float); // = 32

    // Returns number of bytes written, or 0 on error.
    unsigned to_bytes(void* buf, unsigned buf_size) const {
        if (buf_size < byte_size()) return 0;
        uint8_t* p = (uint8_t*)buf;
        write_u32(p, MAGIC);   p += 4;
        write_u32(p, VERSION); p += 4;
        std::memcpy(p, this, sizeof(PrismParams));
        return byte_size();
    }

    // Returns true on success; on failure leaves *this unchanged (caller
    // should substitute PrismParams() defaults).
    bool from_bytes(const void* buf, unsigned buf_size) {
        const uint8_t* p = (const uint8_t*)buf;
        if (buf_size < 8) return false;
        uint32_t magic   = read_u32(p); p += 4;
        uint32_t version = read_u32(p); p += 4;
        // Accept both PRSM (current) and SCE7 (legacy preset files)
        if (magic != MAGIC && magic != 0x53434537u) return false;

        if (version == 3) {
            if (buf_size < byte_size()) return false;
            std::memcpy(this, p, sizeof(PrismParams));
            return true;
        }
        if (version == 2) {
            // Upgrade path: read the 8 core floats, zero-init all v3 fields
            // so the user sees no change from their existing preset.
            if (buf_size < 8 + V2_CORE_BYTES) return false;
            *this = PrismParams();               // fills defaults (all enables=0)
            std::memcpy(this, p, V2_CORE_BYTES); // overlay core fields
            return true;
        }
        return false; // unknown version — caller uses defaults
    }

    static unsigned byte_size() { return 8u + sizeof(PrismParams); }

private:
    static void     write_u32(uint8_t* p, uint32_t v) { std::memcpy(p, &v, 4); }
    static uint32_t read_u32(const uint8_t* p) { uint32_t v; std::memcpy(&v, p, 4); return v; }
};
