# foo_snesapu + foo_input_vgm 7.1 Surround Upmix — Implementation Plan

## Context

`foo_snesapu` is a foobar2000 input plugin for SPC files (SNES audio). We have the source at
`c:\Users\dissonance\Desktop\foo_snesapu_v0.90`. Dissonance runs a HeSuVi/Dolby Atmos/Trifield
convolution chain in foobar and wants native 7.1 output from SPC playback rather than stereo.

The x64 build runs SNESAPU.dll in a **subprocess** via named pipes (`spcplayer_controller`),
so there is no direct DSP register or voice-level access. The upmix must be pure post-processing
of the stereo PCM output from `EmuAPU`.

---

## Approach: L/R Matrix Upmix

Convert the stereo signal to 8-channel after decoding. No AI, no convolution — simple coefficient
matrix derived from the L−R difference signal, which carries stereo width information.

```
FL  = L
FR  = R
FC  = (L + R) * 0.7071f      // center mix, -3dB
LFE = 0                       // silent — let the convolution chain handle bass
RL  = (L - R) * 0.5f         // rear left from difference
RR  = (R - L) * 0.5f         // rear right from difference
SL  = (L - R) * 0.7f         // side left
SR  = (R - L) * 0.7f         // side right
```

Channel order matches foobar2000's 7.1 layout (FL FR FC LFE RL RR SL SR).

---

## Files Modified

### Completed

| File | Change |
|------|--------|
| `resource.h` | Added `#define IDC_SURROUND_71 1029` |
| `resource.rc` | Replaced "Enable surround sound" checkbox with "7.1 surround upmix" at same position |
| `preferences_snesapu.cpp` | Added `cfg_surround_71`, wired into OnInitDialog / apply / HasChanged / reset; removed `IDC_DSP_SURROUND` from DSP option table |

### Remaining

| File | Change needed |
|------|---------------|
| `input_snesapu.hpp` | Add `bool m_CnfSurround71;` and `pfc::array_t<t_uint8> m_SurroundBuffer;` to private members |
| `input_snesapu.cpp` | (1) `extern cfg_int cfg_surround_71;` near other externs; (2) read into `m_CnfSurround71` inside `open()`; (3) in `decode_initialize()`, allocate buffer 4× larger when surround enabled and call `audio_chunk::g_guess_channel_config(8)`; (4) in `decode_run()`, after `EmuAPU` fills stereo buffer, apply matrix to produce 8-ch output |

---

## decode_run Matrix Implementation (pseudocode)

```cpp
// after EmuAPU writes stereo samples into m_DecodeBuffer:
if (m_CnfSurround71) {
    t_size stereo_samples = decoded_bytes / (m_CnfBPS / 8);  // L+R interleaved count
    t_size frames = stereo_samples / 2;
    // resize output buffer to 8 channels
    m_SurroundBuffer.set_size(frames * 8 * (m_CnfBPS / 8));

    if (m_CnfBPS == 16) {
        const int16_t *src = (int16_t *)m_DecodeBuffer.get_ptr();
        int16_t       *dst = (int16_t *)m_SurroundBuffer.get_ptr();
        for (t_size i = 0; i < frames; ++i) {
            float L = src[i*2 + 0] / 32768.f;
            float R = src[i*2 + 1] / 32768.f;
            dst[i*8 + 0] = (int16_t)(L * 32767.f);                  // FL
            dst[i*8 + 1] = (int16_t)(R * 32767.f);                  // FR
            dst[i*8 + 2] = (int16_t)((L+R) * 0.7071f * 32767.f);   // FC
            dst[i*8 + 3] = 0;                                        // LFE
            dst[i*8 + 4] = (int16_t)((L-R) * 0.5f  * 32767.f);     // RL
            dst[i*8 + 5] = (int16_t)((R-L) * 0.5f  * 32767.f);     // RR
            dst[i*8 + 6] = (int16_t)((L-R) * 0.7f  * 32767.f);     // SL
            dst[i*8 + 7] = (int16_t)((R-L) * 0.7f  * 32767.f);     // SR
        }
    }
    // (similar block for 32-bit float path)

    p_chunk.set_data_fixedpoint(
        m_SurroundBuffer.get_ptr(),
        frames * 8 * (m_CnfBPS / 8),
        m_CnfSampleRate, 8,
        m_CnfBPS,
        audio_chunk::g_guess_channel_config(8)
    );
} else {
    // existing stereo path unchanged
}
```

---

## Notes

- The old "Enable surround sound" (`DSP_SURND`) checkbox was a SNESAPU-internal fake widening
  effect. It has been replaced by our upmix checkbox; the `DSP_SURND` flag is no longer set.
- The upmix is intentionally simple — the convolution chain (HeSuVi / Dolby / Trifield) does
  the heavy lifting for room simulation and HRTF. This just feeds it proper 7.1 routing.
- LFE is silent here. If bass management is wanted later, a low-shelf sum of L+R can be added.
- The 32-bit path uses float math directly without the /32768 normalization step.

---

## foo_input_vgm — Same Plan

Source is at `c:\Users\dissonance\Desktop\foo_input_vgm_v0.30\src\foobar2000\foo_input_vgm`.

The same L/R matrix upmix will be applied. VGM files cover a wide range of chips (OPN2, SN76489,
OPLL, etc.) and the plugin outputs stereo PCM — identical post-processing point as foo_snesapu.

### Key differences to account for during implementation

- Different preferences dialog (separate .rc / preferences .cpp) — add the same "7.1 surround upmix"
  checkbox under whatever Misc/Output groupbox exists there.
- Different input class name — locate the `decode_run` equivalent and apply the same matrix block.
- VGM has its own cfg GUID namespace — generate a fresh GUID for `guid_surround_71` specific to
  foo_input_vgm (do not reuse the foo_snesapu one).
- The matrix coefficients and channel layout are identical; the same pseudocode applies verbatim.

### Status

Not yet started. Do foo_snesapu first (finish `input_snesapu.hpp` and `input_snesapu.cpp`),
build and verify, then port to foo_input_vgm.

---

## Surround Quality by Chip

The upmix is a matrix — surrounds are only as wide as the source's L−R difference content.

| Chip | Stereo content | Upmix result |
|------|---------------|--------------|
| SNES DSP (SPC) | Full stereo — 8 voices independently panned, echo with stereo FIR | **Best case.** Rich L−R difference, surrounds active and musical |
| YM2612/OPN2 (Genesis) | Per-channel hard pan L/C/R | Good. Pan separation feeds surrounds well |
| SN76489 (SMS/Genesis) | Mono or hard-panned | Thin surrounds, mostly center |
| OPL2 (PC) | Mono | Effectively center-only |
| OPL3 (PC) | True stereo | Good |
| YM2151 (arcade) | Per-operator stereo panning | Good |
| PSG / AY-3-8910 | Mono | Minimal surround content |

SNES is the best case: per-voice panning + stereo echo FIR means genuine spatial content in
the difference signal. HeSuVi/Trifield then handles HRTF and room simulation on top.

---

## Compilation

Both projects use **Visual Studio 2019/2022**, toolset v142, Windows 10 SDK.
Requires "Desktop development with C++" workload (includes ATL). The foobar2000 SDK is
already bundled in each source tree — no extra downloads needed.

### foo_snesapu (two builds required)

```
# Step 1 — 32-bit subprocess that hosts SNESAPU.dll
Solution: foo_snesapu_v0.90\src\spcplayer\spcplayer.sln
Config:   Release | x86
Output:   spcplayer.exe  — must sit alongside the .foo in the components folder

# Step 2 — the foobar2000 plugin
Solution: foo_snesapu_v0.90\src\foobar2000\foo_snesapu\foo_snesapu.sln
Config:   Release | x64
Output:   foo_snesapu.dll → rename to foo_snesapu.foo
```

### foo_input_vgm

```
Solution: foo_input_vgm_v0.30\src\foobar2000\foo_input_vgm\foo_input_vgm.sln
Config:   Release | x64
Output:   foo_input_vgm.dll → rename to foo_input_vgm.foo
```

Drop `.foo` files (and `spcplayer.exe`) into the foobar2000 `components` folder and restart.
