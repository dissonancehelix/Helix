# Sound Chip Coverage Map

**Location**: `core/adapters/`
**Updated**: 2026-03-18 (rev 3)

Maps every significant sound chip to its adapter status. "Full" means a dedicated
adapter exists with register map, timing constants, operator layout, and synthesis
parameter encoding. "Partial" means chiptext or a format adapter touches it but no
structural constants are available as queryable Python dicts. "None" means no coverage.

---

## Coverage Status

### FM Synthesis — Yamaha OPN Family

| Chip | Platform | Adapter | Status | Notes |
|------|----------|---------|--------|-------|
| YM2612 (OPN2) | Genesis / Mega Drive (original hardware) | `adapter_nuked_opn2.py` + `adapter_gems.py` + `adapter_smps.py` | **Full** | nuked-opn2, GEMS.DOC, SMPS source. DAC channel 6, ladder distortion characteristic. |
| YM3438 (OPN2C) | Genesis 2 / Genesis 3 / Nomad / 32X | `adapter_nuked_opn2.py` | **Full** | CMOS version of YM2612. Identical register map; no DAC ladder noise. Same adapter covers both. |
| YM2151 (OPM) | Arcade (System 16/24), X68000, Taito | `adapter_nuked_opm.py` | **Full** | 8-operator, 8-channel, hardware LFO with PM/AM. nuked-opm. |
| YM2203 (OPN) | PC-88, MSX, NES (Famicom Disk System adjacent) | — | **None** | 3 FM + SSG (AY-equivalent) + 3 SSG envelope. furnace `ym2203.cpp`, MAME `ymopn.cpp`. |
| YM2608 (OPNA) | PC-88 VA, PC-98 | — | **None** | 6 FM + SSG + ADPCM rhythm (6 PCM drums) + ADPCM-B melody. Entire Falcom and early Konami PC corpus. furnace `ym2608.cpp`, MAME `ymopn.cpp`. |
| YM2610 (OPNB) | Neo Geo AES / MVS | — | **None** | 4 FM + SSG + 6-channel ADPCM-A (samples) + ADPCM-B (streaming). Entire Neo Geo corpus. furnace `ym2610.cpp`, MAME `ymopn.cpp`. |
| YM2610B | Neo Geo variants (later revisions) | — | **None** | 6 FM instead of 4. furnace `ym2610b.cpp`. |
| YM2414 (OPZ) | TX81Z, Yamaha DX11 | — | **None** | 8-operator with fixed-wave table operators and multiple waveforms per operator. furnace `tx81z.cpp`, MAME `ymopz.cpp`. |
| YM2164 (OPP) | Yamaha FB-01, Casio synths | — | **None** | Related to OPM. MAME `ymopn.cpp`. |

### FM Synthesis — Yamaha OPL Family

| Chip | Platform | Adapter | Status | Notes |
|------|----------|---------|--------|-------|
| YM3526 (OPL) | Bubble System, early arcade | `adapter_nuked_opl2.py` | **Full** | 9-channel, 2-operator. nuked-opl2 covers as YM3812 predecessor. Same waveform set (only sine). |
| YM3812 (OPL2) | AdLib, Sound Blaster 1.x/2.x | `adapter_nuked_opl2.py` | **Full** | 9-channel, 2-operator, 4 waveforms. Primary PC game music chip pre-SB16. nuked-opl2. |
| YMF262 (OPL3) | Sound Blaster 16 / Pro / compatible | `adapter_nuked_opl3.py` | **Full** | 18-channel 2-op or 6-channel 4-op. 8 waveforms, stereo panning, 4-op connections. nuked-opl3. |
| YMF278B (OPL4) | Moonsound (MSX-Music) | — | **None** | OPL3 FM section + 24-voice wavetable (external ROM). furnace `opl.cpp`, MAME `ymopl.cpp`. OPL3 FM part covered; wavetable not. |
| YMF271 (OPL4-ML) | Taito FX-1B, Sega Model 2 (sound board) | — | **None** | 12 FM operators (4-op) + 24 wavetable voices with DRAM. MAME `ymf271.cpp`. |
| Y8950 (OPL + ADPCM) | MSX-Audio | — | **None** | OPL FM + ADPCM channel + keyboard interface. furnace `opl.cpp`. |
| YM2413 (OPLL) | FM-PAC, MSX, Sega Master System (JP) | `adapter_nuked_opll.py` | **Full** | 9 channels (6 melody + 5 percussion), 15 ROM patches + 1 custom. nuked-opll. |
| Konami VRC7 | NES Famicom mapper (Lagrange Point) | `adapter_nuked_opll.py` | **Full** | OPLL derivative with 6 custom patches. nuked-opll (VRC7 variant). |
| ESS ESFM | ESS ES1868/1869/1878 soundcards | — | **None** | OPL3-compatible extended mode. 4-op extensions beyond OPL3. furnace `esfm.cpp`. |

### PSG / Tone Generators

| Chip | Platform | Adapter | Status | Notes |
|------|----------|---------|--------|-------|
| SN76489 / YM7101 | Genesis, SMS, BBC Micro, ColecoVision, Game Gear | `adapter_nuked_psg.py` | **Full** | 3 tone + 1 noise, 10-bit period, 4-bit volume, 2-bit noise tap select. nuked-psg. Genesis variant at 3.579 MHz. |
| AY-3-8910 / YM2149 | ZX Spectrum, Atari ST, MSX, CPC, arcade | `adapter_ay8910.py` | **Full** | 3 tone + noise + envelope generator. 17-bit LFSR. 16 envelope shapes. AY vs YM2149 different volume tables. furnace `ay.cpp`, MAME `ay8910.cpp`. |
| AY8930 | Enhanced AY (Microchip successor) | — | **None** | AY superset: per-channel envelopes, duty cycle, expanded period range. furnace `ay8930.cpp`. |
| AY-3-8914 | Mattel Intellivision | — | **None** | AY variant with different register ordering (remap known but no adapter). MAME `ay8914.cpp`. |
| Sunsoft 5B / FME-7 | NES mapper 69 (Gimmick!, Hebereke) | `adapter_ay8910.py` | **Full** | AY-3-8910 placed in NES mapper 69. Register map identical; clock = CPU/2 ≈ 894 kHz. Covered by AY8910 adapter. |
| SAA1099 | SAM Coupé, Creative Music System | — | **None** | 6 tone + 2 noise, 8-step envelope, stereo panning per channel. furnace `saa.cpp`, MAME `saa1099.cpp`. |
| Konami K051649 (SCC) | Konami MSX carts, Konami arcade | — | **None** | 5-channel wavetable (32-sample waveform per channel), 12-bit period. furnace `scc.cpp`, MAME `k051649.cpp`. |
| Konami K052539 (SCC+) | Konami MSX (Snatcher, SD Snatcher) | — | **None** | SCC extension: channels 1–4 have independent waveforms (not shared). Additional register mode. |
| T6W28 | Game Gear (stereo SN variant) | — | **None** | SN76489 split across two chips for stereo. furnace `t6w28.cpp`, MAME `t6w28.cpp`. |
| Texas Instruments SN76477 | Arcade (early) | — | **None** | Analog compound sound (not a programmable PSG). Discrete analog. |

### Dedicated Console / Home Computer Chips

| Chip | Platform | Adapter | Status | Notes |
|------|----------|---------|--------|-------|
| NES APU 2A03 (NTSC) | NES / Famicom | `adapter_nes_apu.py` | **Full** | 2 pulse + 1 triangle + 1 noise + 1 DMC. Length counters, sweep, frame sequencer. Non-linear mixing. NesDev wiki. |
| NES APU 2A07 (PAL) | PAL NES | `adapter_nes_apu.py` | **Full** | PAL clock variant. Different DMC + noise period tables. Both tables in adapter. |
| SNES SPC700 + S-DSP | Super Nintendo | `adapter_snes_spc.py` | **Full** | 1.024 MHz SPC700 + 32 kHz DSP. 8-voice BRR PCM, 14-bit pitch, ADSR/GAIN, echo FIR. Hardware-accurate BRR filter coefficients from ares/MAME. |
| Game Boy DMG APU | Game Boy / GBC | `adapter_gb_apu.py` | **Full** | 2 pulse + 1 wave + 1 noise. Frame sequencer at 512 Hz. DAC enable via NR52. Freq formula: 131072/(2048−period). pandocs. |
| HuC6280 | PC Engine / TurboGrafx-16 / SuperGrafx | — | **None** | 6-channel wavetable (32-sample waveform, 5-bit per sample) + LFO (ch2 modulates ch1). furnace `pce.cpp`, MAME `c6280.cpp`. |
| Hudson HuC6230 | PC-FX | — | **None** | 6-channel PCM (16-bit linear), ADPCM mode, stereo panning. Successor to HuC6280 PCM model. |
| MOS 6581 (SID) | Commodore 64 (NTSC) | — | **None** | 3 oscillators (triangle/sawtooth/pulse/noise), resonant filter per-chip (not per-channel), ADSR. Ring mod, hard sync. reSID. |
| MOS 8580 (SID) | Commodore 64C (revised) | — | **None** | Revised SID: different filter characteristics, cleaner waveforms, no 6581 DC offset. reSID. |
| Ricoh RF5C68A | Sega CD / Mega CD | `adapter_rf5c68a.py` | **Full** | 8-channel PCM, 8-bit samples, bank-switched, hardware looping. RF5C68A hardware manual. |
| Ricoh RF5C164 | Sega CD (later revision) | `adapter_rf5c68a.py` | **Full** | Functional variant of RF5C68A; adapter covers both. |
| Ricoh RF5C400 | Saturn (early PCM board) | — | **None** | 32-channel PCM, 16-bit stereo, hardware ADSR. MAME `rf5c400.cpp`. |
| SEGA SCSP (YMF292) | Saturn | — | **None** | 32-voice wavetable, ADSR, DSP effects unit (128 instructions), FM synthesis mode, MIDI interface. MAME `scsp.cpp`. |
| SEGA AICA | Dreamcast | — | **None** | Enhanced SCSP: 64-voice ARM7-controlled ADPCM + DSP, 2MB sound RAM. MAME `aica.cpp`. |
| Sega 32X PWM | Sega 32X (SH2 PWM timer output) | — | **None** | 2-channel stereo, software-driven. Not a separate chip — PWM output from SH2 timers. Typically 20–25 kHz effective rate. |
| Nintendo 64 AI (ADPCM DMA) | Nintendo 64 | — | **None** | RSP-based software audio. N64 SDK uses ADPCM sequences via AudioLib; no dedicated hardware chip. |
| Game Boy Advance Direct Sound | GBA | — | **None** | 2 DMA-fed 8-bit PCM channels mixed with legacy DMG APU. MP2k (Sappy) is the dominant driver. furnace `gbadma.cpp`. |
| PlayStation SPU | PlayStation 1 | — | **None** | 24-voice ADPCM (SPU ADPCM), ADSR per voice, hardware reverb (6 presets), 512 KB sound RAM. MAME `spu.cpp`. |
| PlayStation 2 SPU2 | PlayStation 2 | — | **None** | 48-voice ADPCM, 2 MB sound RAM, two independent cores. ADSR identical to PS1. PCSX2 source / MAME `spu2.cpp`. |
| Nintendo DS DSPCM | Nintendo DS | — | **None** | 16-channel PCM (8/16-bit + IMA-ADPCM + PSG modes), hardware looping, IIR filter. furnace `nds.cpp`. |
| Amiga Paula | Amiga 500/1200 | — | **None** | 4-channel 8-bit PCM, DMA-driven, hardware pitch (period register), no mixing hardware. furnace `amiga.cpp`. |
| Atari POKEY | Atari 8-bit / Atari Lynx | — | **None** | 4 channels (tone/noise, 8/16-bit modes), unusual clock-based tuning, programmable divisors, serial I/O doubles as audio. furnace `pokey.cpp`, MAME `pokey.cpp`. |
| Atari TIA | Atari 2600 | — | **None** | 2 channels, 5-bit frequency divisor, 4-bit tone type (AUDC), very limited pitch set. furnace `tia.cpp`, MAME `tiaintf.cpp`. |
| MOS 7360 / 8360 (TED) | Commodore 16 / Plus/4 | — | **None** | 2-channel square wave generator integrated with video. MAME `mos7360.cpp`. |
| Namco WSG (custom) | Pac-Man, Galaxian, Galaga | — | **None** | 3-channel wavetable (8-sample waveform per channel), simple volume. furnace `namcowsg.cpp`, MAME `namco.cpp`. |
| Namco C140 | Namco System 2 (Assault, Ordyne) | — | **None** | 24-channel PCM, 8-bit µ-law, 32 KB address space. furnace `c140.cpp`, MAME `c140.cpp`. |
| Namco C352 | Namco System 22 / System 23 | — | **None** | 32-channel PCM, µ-law, stereo, hardware ADSR, reverb send. MAME `c352.cpp`. |
| Seta X1-010 | Seta / Allumer arcade | — | **None** | 16-channel PCM + wavetable, dual-clock architecture. furnace `x1_010.cpp`, MAME `x1_010.cpp`. |
| Ensoniq ES5503 | Apple IIGS | — | **None** | 32-oscillator wavetable (DOC: Digital Oscillator Chip), per-oscillator output levels. MAME `es5503.cpp`. |
| Ensoniq ES5505 / ES5506 | 3DO (ES5505), arcade (ES5506) | — | **None** | 32/64-oscillator wavetable, ADSR per voice, stereo mixing. furnace `es5506.cpp`, MAME `es5505.cpp` / `es5506.cpp`. |
| VRC6 | NES mapper 24/26 (Konami — Castlevania III JP) | — | **None** | 2 extra pulse channels (7-bit duty, expanded range) + 1 sawtooth generator. furnace `vrc6.cpp`, MAME `vrc6.cpp`. |
| MMC5 | NES mapper 5 (Nintendo — Castlevania III US, Just Breed) | — | **None** | 2 extra pulse channels + 1 PCM channel. furnace `mmc5.cpp`, MAME `mmc5.cpp`. |
| Namco N163 | NES mapper 19 (Namco) | — | **None** | 1–8 extra wavetable channels (4-bit samples, 128-byte shared waveform RAM). furnace `n163.cpp`. |
| Famicom Disk System (RP2C33) | NES FDS | — | **None** | 1 extra wavetable channel (64-step, 6-bit) + mod unit for vibrato. furnace `fds.cpp`. |
| WonderSwan SoundCore | Bandai WonderSwan / WonderSwan Color | — | **None** | 4-channel wavetable (32-step, 4-bit), channels 2–4 can be DMA PCM. furnace `swan.cpp`. |
| Virtual Boy VSU | Nintendo Virtual Boy | — | **None** | 6-channel wavetable (32-step, 6-bit), stereo panning, modulation unit. furnace `vb.cpp`. |
| Sharp LR35902 (extended) | Game Boy Color extra registers | `adapter_gb_apu.py` | **Full** | CGB wave RAM addressing change + wave channel high-water mark. Covered in GB adapter; same register map with CGB flag notes. |

### PCM / ADPCM / Wavetable

| Chip | Platform | Adapter | Status | Notes |
|------|----------|---------|--------|-------|
| OKI M6295 | Arcade (CPS1, many SNK, Data East, Taito) | — | **None** | 4-channel ADPCM (OKI ADPCM variant), bank-switched sample ROM, each channel loops independently. furnace `msm6295.cpp`, MAME `okim6295.cpp`. |
| OKI MSM5205 | Arcade ADPCM (many 1980s boards) | — | **None** | 1-channel IMA/OKI ADPCM, clock-selectable rate (32/24/16 kHz steps), 4-bit nibbles. MAME `msm5205.cpp`. |
| OKI MSM6258 | Sharp X68000 | — | **None** | 1-channel OKI ADPCM, 4 or 8 kHz output, connected to X68000 YM2151 boards. furnace `msm6258.cpp`, MAME `okim6258.cpp`. |
| Yamaha YMZ280B (PCMD8) | Arcade (CPS3, Taito B, many) | — | **None** | 8-channel ADPCM (Yamaha ADPCM-B), 8-bit or 4-bit mode, hardware looping, 8–256 kHz playback rates. furnace `ymz280b.cpp`, MAME `ymz280b.cpp`. |
| Yamaha YMF278B wavetable | Moonsound MSX + OPL4 | — | **None** | 24-voice wavetable section of OPL4. Separate from FM section. MAME `ymopl.cpp`. |
| Sega MultiPCM (YMW258-F) | Sega Model 1 / Model 2 sound board | — | **None** | 28-channel wavetable, 12-bit linear PCM, ADSR, pitch bend, hardware looping. furnace `multipcm.cpp`, MAME `multipcm.cpp`. |
| Sega PCM (custom) | Sega System 16 | — | **None** | 16-channel 8-bit PCM, bank-switched, direct memory access. furnace `segapcm.cpp`, MAME `segapcm.cpp`. |
| Capcom QSound (DSP-16A) | CPS2 | — | **None** | Motorola DSP16A running Capcom's QSound algorithm. 16-channel ADPCM input, DSP-based stereo simulation (not true stereo positioning). furnace `qsound.cpp`, MAME `qsound.cpp`; qsound-hle in repo. |
| Konami K007232 | Konami arcade (Contra, TMNT) | — | **None** | 2-channel PCM, 8-bit samples, rate control, looping. furnace `k007232.cpp`, MAME `k007232.cpp`. |
| Konami K053260 | Konami arcade (Sunset Riders, Metamorphic Force) | — | **None** | 4-channel ADPCM, separate left/right volume, looping. furnace `k053260.cpp`, MAME `k053260.cpp`. |
| Konami K054539 | Konami arcade (Lethal Enforcers, Animaniacs) | — | **None** | 8-channel PCM (16-bit, 8-bit, or ADPCM), reverb send, panning. MAME `k054539.cpp`. |
| Irem GA20 | Irem arcade (R-Type Leo, many) | — | **None** | 4-channel 8-bit PCM, looping, volume control. MAME `iremga20.cpp`. |
| Taito TC0140SYT | Taito F2/B system | — | **None** | Sound communication chip. Routes commands from main CPU to Z80 sound CPU. Not a synthesis chip itself. |
| Taito YMZ770C (ZMUSICII) | Taito Type X | — | **None** | 8-channel ADPCM, hardware ADSR, software-driven via Z80. MAME `ymz770.cpp`. |
| PlayStation SPU ADPCM | PlayStation 1/2 | — | **None** | Format only (not a standalone chip). SPU ADPCM uses 4-bit nibbles, 28-sample blocks, 2 predictor coefficients, loop flags. |
| Nintendo DS DSPADPCM | Nintendo DS | — | **None** | IMA-ADPCM variant used in DS ROM banks. Hardware decode per channel. |
| GBA MP2k ADPCM | Game Boy Advance | — | **None** | Software ADPCM driver (Sappy/MP2k engine). 4-bit IMA-ADPCM decoded by ARM CPU. |

---

### Driver Layer

| Driver | Chip(s) | Adapter | Status | Notes |
|--------|---------|---------|--------|-------|
| GEMS v2.0 | YM2612 + SN76489 | `adapter_gems.py` | **Full** | Sega's in-house driver. gems2mid.c source in MidiConverters. |
| SMPS (S1/S2/S3/SK/S3D) | YM2612 + SN76489 | `adapter_smps.py` | **Full** | All five variants. S1 operator order [1,3,2,4]. SK adds 4-byte SSGEG suffix. |
| flamedriver (S3&K Z80) | YM2612 + SN76489 | `adapter_s3k_driver.py` | **Full** | Naka/Kojin Z80 driver. zTrack struct (48 bytes). UniBank vs inline voice sourcing. |
| PMD (PC-88/98 FM) | YM2203 / YM2608 + PSG | — | **None** | pmd2mid.c in MidiConverters. Chip adapter for YM2203/YM2608 needed first. |
| FMP (PC-98 FM) | YM2608 | — | **None** | fmp2mid.c in MidiConverters. |
| Mucom88 | YM2203 | — | **None** | mucom2mid.c in MidiConverters. |
| Akao (Square PS1/SNES) | PlayStation SPU / SPC700 | — | **None** | VGMTrans handles SNES Akao variant (SquSnes format). PS1 Akao via VGMTrans AkaoSeq. |
| MP2k / Sappy | GBA Direct Sound | — | **None** | VGMTrans covers via MP2kFormat. |
| Konami MD driver | YM2612 + SN76489 | — | **None** | konamimd2mid.c in MidiConverters. |
| Ghouls n Ghosts / GRC | YM2612 + SN76489 | — | **None** | grc2mid.c in MidiConverters. |
| Ys II driver | — | — | **None** | ys2mid.c in MidiConverters. |
| Tales of Phantasia driver | — | — | **None** | top2mid.c in MidiConverters (SNES + arcade variants). |

### Chip → MIDI Pipeline

| Format | Tool | Adapter | Status | Notes |
|--------|------|---------|--------|-------|
| VGM (YM2612 FM) | `vgm_note_reconstructor.py` built-in | — | **Active** | F-number → MIDI. No external binary. |
| VGM (SN76489 PSG) | `vgm_note_reconstructor.py` built-in | — | **Active** | 10-bit period → MIDI. Volume gate for note detection. Logical channels 6–8. |
| SPC (SNES — 21 drivers) | VGMTrans | `adapter_vgmtrans.py` | **Tier B** | Capcom, Konami, Nintendo, Rare, Square, and others. Needs compiled binary. |
| NDS .mini2sf (MP2k) | VGMTrans | `adapter_vgmtrans.py` | **Tier B** | MP2k / Sappy engine. Same binary. |
| PSF (PS1 — Akao, HeartBeat) | VGMTrans | `adapter_vgmtrans.py` | **Tier B** | Akao (Final Fantasy), HeartBeatPS1, TriAcePS1, Sony PS2 VAB. Same binary. |
| Saturn (.SegSat) | VGMTrans | `adapter_vgmtrans.py` | **Tier B** | SegSat driver. Same binary. |
| VGM (broader — GEMS, Konami MD) | ValleyBell MidiConverters | — | **Pending** | gems2mid.c, konamimd2mid.c, grc2mid.c in repo. Need compile step. |
| GBS (Game Boy) | VGMTrans (limited) | — | **Pending** | No reliable general converter. VGMTrans has partial GBS support. |
| NSF (NES) | nsf2vgm → reconstructor | `adapter_nsf2vgm.py` | **Tier A** | Binary ships in repo. Synthesises M3U from NSF header, converts to per-track VGM, feeds reconstructor. All expansion chips: FDS, VRC6, VRC7, MMC5, N163, FME7. |
| PSF2 (PS2) | VGMTrans | `adapter_vgmtrans.py` | **Tier B** | SonyPS2 + SquarePS2 formats. Same binary. |
| Organya (.org) | VGMTrans | `adapter_vgmtrans.py` | **Tier B** | Cave Story music format. Same binary. |

VGMTrans binary not included. Build from `data/music/source/code/vgmtrans/` using CMake,
or download the release binary from `github.com/vgmtrans/vgmtrans/releases`.
Once built, place at `data/music/source/code/vgmtrans/build/Release/VGMTrans.exe`.

---

## Build Priority

### Tier 1 — Highest corpus value

| Chip | Reason | Status |
|------|--------|--------|
| NES APU (2A03/2A07) | Largest retro game music corpus. 5 channels, fully documented. NesDev wiki is authoritative. | **Done** — `adapter_nes_apu.py` |
| SNES S-DSP | Second-largest corpus. 8-voice BRR PCM, rich ADSR system. ares/MAME-accurate BRR coefficients. | **Done** — `adapter_snes_spc.py` |
| Game Boy DMG APU | Massive corpus. 4 channels. pandocs is authoritative. | **Done** — `adapter_gb_apu.py` |
| AY-3-8910 / YM2149 | ZX Spectrum, Atari ST, MSX, CPC, dozens of arcade boards. 3 tone + noise + envelope. | **Done** — `adapter_ay8910.py` |
| MOS SID 6581/8580 | Most analytically distinctive chip. Ring mod, hard sync, resonant filter — unique fingerprint per revision. reSID is authoritative. | **Remaining** |

### Tier 2 — Important platform coverage

| Chip | Reason | Status |
|------|--------|--------|
| HuC6280 | PC Engine corpus. 6-channel wavetable + LFO. Used in entire TurboGrafx library. | **Remaining** |
| YM2608 (OPNA) | PC-98 corpus. All Falcom (Dragon Slayer, Ys, Sorcerian), early Konami. 6 FM + SSG + ADPCM rhythm + ADPCM-B. | **Remaining** |
| YM2610 (OPNB) | Neo Geo entire sound identity. 4 FM + SSG + 6 ADPCM-A + ADPCM-B. SNK corpus. | **Remaining** |
| Capcom QSound | CPS2 corpus. DSP16A-based stereo simulation — structurally unusual, not real FM or PCM. qsound-hle source in repo. | **Remaining** |
| OKI M6295 | Ubiquitous in CPS1-era arcade (Forgotten Worlds, U.N. Squadron, many SNK/Data East boards). 4-channel ADPCM. | **Remaining** |
| PlayStation SPU | PS1 corpus. 24-voice ADPCM. ADSR identical structure to SPC700. Entire PlayStation library. | **Remaining** |

### Tier 3 — Specialized / niche

| Chip | Reason | Status |
|------|--------|--------|
| Atari POKEY | Atari 8-bit corpus. Unusual pitch table — integer divisors produce non-equal-tempered scale. Lynx variant. | **Remaining** |
| SEGA SCSP (YMF292) | Saturn corpus. 32-voice wavetable + DSP effects block. Complex but Sega CD transition tracks it. | **Remaining** |
| Konami SCC / K051649 | Gradius, Castlevania, Parodius MSX identity. 5-channel wavetable, distinctive timbre. | **Remaining** |
| VRC6 | NES expansion. Castlevania III JP, Akumajou Densetsu. 2 pulse + 1 sawtooth. Small but high-value corpus. | **Remaining** |
| MMC5 | NES expansion. Just Breed, Castlevania III US. 2 pulse + PCM. | **Remaining** |
| YM2203 (OPN) | PC-88 / early MSX corpus. Predecessor to OPNA. 3 FM + SSG. PMD and FMP drivers. | **Remaining** |
| Nintendo DS DSPCM | DS corpus. 16-channel, multi-mode. MP2k dominant engine covered via VGMTrans; chip layer still missing. | **Remaining** |
| Amiga Paula | Amiga MOD corpus. 4-channel 8-bit PCM, 28 base periods. Large demoscene/tracker body. | **Remaining** |
| Seta X1-010 | Seta arcade corpus (Willow, Twin Eagle II). 16-channel wavetable + PCM. | **Remaining** |
| WonderSwan SoundCore | WonderSwan corpus. 4-channel wavetable. Small but self-contained. | **Remaining** |

---

## What "Full" Coverage Means

An adapter is **Full** when it provides all four layers needed for Helix to treat
the chip as a known processor rather than opaque hardware:

1. **Register map** — every addressable register, its bit fields, its range, its effect
2. **Voice/operator layout** — synthesis parameters, operator ordering, carrier/modulator topology per algorithm
3. **Timing constants** — clock dividers, sample rate derivation, envelope rate tables, LFO period tables
4. **Driver conventions** — key-on sequencing, volume scaling, channel allocation (where a standard driver exists)

Chiptext (`adapter_chiptext.py`) provides register text output for many chips but
does not satisfy conditions 1–4 as queryable structured constants. It is not counted
as "covered" in this map.

---

## Source Repositories

| Repo | URL | Chips / Use |
|------|-----|-------------|
| furnace | github.com/tildearrow/furnace | 100+ chips — `src/engine/platform/` |
| MAME | github.com/mamedev/mame | 270+ sound devices — `src/devices/sound/` |
| nuked-opn2 | github.com/nukeykt/Nuked-OPN2 | YM2612 / YM3438 |
| nuked-opm | github.com/nukeykt/Nuked-OPM | YM2151 |
| nuked-opl3 | github.com/nukeykt/Nuked-OPL3 | YMF262 |
| nuked-opll | github.com/nukeykt/Nuked-OPLL | YM2413, VRC7 |
| nuked-psg | github.com/nukeykt/Nuked-PSG | SN76489 |
| reSID | github.com/libsidplayfp/libsidplayfp | SID 6581/8580 |
| ares | github.com/ares-emulator/ares | SNES S-DSP (hardware-accurate BRR), SFC, N64, Saturn |
| NesDev wiki | wiki.nesdev.org/w/index.php/APU | NES APU — authoritative register and timing reference |
| pandocs | gbdev.io/pandocs | Game Boy APU — authoritative register reference |
| SNESAPU / spc\_dec | github.com/Caitsith2/snesemulist | SPC700 + S-DSP alternative reference |
| VGMTrans | github.com/vgmtrans/vgmtrans | SPC, PSF, NDS, Saturn → MIDI (24 driver families) |
| ValleyBell MidiConverters | github.com/ValleyBell/MidiConverters | GEMS, Konami MD, PMD, FMP, and 50+ format converters |
| qsound-hle | in repo: `data/music/source/code/qsound-hle/` | Capcom QSound DSP algorithm reference |
| nsf2vgm | in repo: `data/music/source/code/nsf2vgm/` | NSF → VGM converter (binary included at v1.0) |
| PCSX2 | github.com/PCSX2/pcsx2 | PlayStation 2 SPU2 — `pcsx2/SPU2/` |
| HuC6280 | huc6280.c in MAME `src/devices/sound/` | PC Engine audio — primary timing reference |
| no$gba | problemkaputt.de/gbatek.htm | GBA Direct Sound + DS DSPCM — register reference |
| anomie's SNES docs | anomie.x.fc2.com | SPC700 instruction set, S-DSP (16-bit precision BRR coefficients) |
