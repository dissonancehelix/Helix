# foo_dragonfly_reverb

A native foobar2000 DSP component wrapping the **Dragonfly Hall Reverb** engine (GPL v3, by Michael Willis & Rob van den Berg). No VST host needed — compiles directly against the foobar2000 SDK.

**Output DLL:** `foo_dragonfly_reverb.dll`  
**Install path:** `%APPDATA%\foobar2000-v2\user-components-x64\foo_dragonfly_reverb\foo_dragonfly_reverb.dll`  
**DSP chain position:** before `foo_prism` — reverb runs on the dry stereo signal, Prism spatializes the result.

---

## Parameters

| Parameter | Range | Default | Notes |
|---|---|---|---|
| Dry | 0–100% | 80% | Unprocessed signal passthrough |
| Early | 0–100% | 20% | Early reflections level |
| Late | 0–100% | 30% | Late reverb (FDN hall) level |
| Room Size | 10–60 m | 32 m | Acoustic space size |
| Decay | 0.1–10 s | 3.2 s | RT60 reverb time |
| Diffuse | 0–100% | 80% | Diffusion / density of the tail |
| High Cut | 1000–16000 Hz | 12000 Hz | Output low-pass filter |
| Pre-delay | 0–100 ms | 12 ms | Delay before late reverb onset |

### Recommended: Lush Hall (for use before Prism)

| Parameter | Value | Why |
|---|---|---|
| Dry | 80% | Keeps original signal intact |
| Early | 15% | Light room texture |
| Late | 35% | Rich, full tail |
| Room Size | 55 m | Grand hall spread |
| Decay | 4.5 s | Long romantic tail |
| Diffuse | 90% | Smooth, no slap |
| High Cut | 14000 Hz | Air and shimmer |
| Pre-delay | 20 ms | Depth separation from dry |

---

## Engine

- **Early reflections**: `fv3::earlyref_f` — FV3_EARLYREF_PRESET_1, stereo width=0.8, L/R delay + cross-AP decorrelation
- **Late reverb**: `fv3::zrev2_f` — FDN hall algorithm, stereo width=1.0
- **Freeverb3 library**: compiled with `LIBFV3_FLOAT` (single-precision) and `DISABLE_UNDENORMAL`
- **Denormal suppression**: SSE2 DAZ+FTZ via `ScopedDenormalDisable` on every `run()` call
- **Preset system**: 25 presets across 5 banks; default = "Large Clear Hall" (bank 4, preset 1)
- **Serialization**: binary blob, MAGIC=`'DFRV'` (0x44465256), VERSION=1, 8 floats

### Signal Path
```
Input (stereo)
  └─► Early Reflections (earlyref_f)
        └─► early_out
  └─► Late FDN input = 20% early_out + 100% dry input
        └─► Late Reverb (zrev2_f)
              └─► late_out

Output = Dry*input + Early*early_out + Late*late_out
```

---

## Source Layout

```
foo_dragonfly_reverb/
  dragonfly_reverb.cpp       foobar2000 DSP wrapper (dragonfly_dsp, CDragonflyDialog)
  DSP.cpp / DSP.hpp           Reverb engine (DPF framework stripped)
  PluginInfo.h                18-param enum, bank/preset table, defaults
  AbstractDSP.hpp             Minimal base class (replaces DPF's Plugin)
  Param.hpp                   Param struct typedef
  ScopedDenormalDisable.hpp   MSVC/SSE2 DAZ+FTZ implementation
  fv3_config.h                Autoconf stub (defines passed via compiler flags)
  dragonfly_reverb.rc         MFC dialog resource (8 sliders, Reset, Close)
  dragonfly_resource.h        IDC_* defines
  stdafx.h                    Windows / MFC prelude
  freeverb/                   Freeverb3 library sources
    earlyref.cpp/hpp          Early reflections
    zrev2.cpp/hpp             FDN late reverb
    ... (allpass, biquad, comb, delay, delayline, efilter, nrev, nrevb,
         progenitor, progenitor2, revbase, slot, strev, utils, zrev)
  foo_dragonfly_reverb.vcxproj
  foo_dragonfly_reverb.sln
```

---

## Build

CI: `.github/workflows/build.yml` builds `foo_dragonfly_reverb\foo_dragonfly_reverb.sln` (x64 Release) and uploads the DLL as the `foo_dragonfly_reverb` artifact.

Local: open `foo_dragonfly_reverb.sln` in VS2022, build Release|x64. The solution uses the same SDK junction layout as the rest of the repo (`../SDK`, `../../pfc`, etc.).

**Key compiler flags:** `LIBFV3_FLOAT`, `DISABLE_UNDENORMAL`, `_AFXDLL`
