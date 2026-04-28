"""
Codec Pipeline — model/domains/music/analysis/codec_pipeline.py
==========================================================
The unified per-file analysis entrypoint.

Translates any supported music format into a schema-consistent TrackAnalysis.
Think of this as the "translator": many input codecs, one output schema.

Tier routing:
  Tier A = hardware register log → chip note events (key-on/off from register writes)
  Tier B = symbolic / sheet-music analysis (MIDI → music21: key, harmony, melody, rhythm)
  Tier C = waveform analysis (essentia/librosa: spectral, MFCCs, BPM)

  VGM/VGZ   → A+B  (register log → note reconstruction → music21)
  SPC       → B    (SPC2MID → music21) + hardware BRR/voice snapshot
  NSF/NSFe  → B    (nsf2vgm → music21) + header snapshot
  SID       → C    (waveform only)
  MP3/Opus  → C    (essentia/librosa waveform only)
  USF/PSF/* → C    (vgmstream render → essentia)

Metadata policy:
  Never reads embedded tags. All metadata joined from codex/library/music/.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Optional

from model.domains.music.analysis.track_analysis import (
    TrackAnalysis,
    ChipVoiceSnapshot,
    NoteEvent,
    StructuralSection,
    DCPProxies,
    SubstrateVector,
    WaveformFeatures,
    SymbolicFeatures,
)
from model.domains.music.parsing.router import FormatRouter

_router = FormatRouter()


# ---------------------------------------------------------------------------
# Substrate vector lookup: hardware ceiling per chip
# Loaded from core adapter data (static constants)
# ---------------------------------------------------------------------------

def _substrate_for_chip(chip_name: str) -> Optional[SubstrateVector]:
    """
    Return the substrate capability vector for a chip.
    This is the DCP profile of the medium — static generative ceiling.
    Values are normalised 0-1 against the highest known ceiling for each axis.
    """
    # possibility_space: max expressible pitch/timbre entropy
    # constraint:        how tightly the hardware limits output
    # attractor_stability: loop/repeat support quality
    # basin_permeability:  envelope flexibility
    # recurrence_depth:    polyphony x patch variation ceiling
    _VECTORS: dict[str, dict[str, float]] = {
        "YM2612": {
            "possibility_space":   0.90,
            "constraint":          0.85,
            "attractor_stability": 0.70,
            "basin_permeability":  0.75,
            "recurrence_depth":    0.95,
        },
        "SN76489": {
            "possibility_space":   0.25,
            "constraint":          0.30,
            "attractor_stability": 0.50,
            "basin_permeability":  0.60,
            "recurrence_depth":    0.20,
        },
        "SNES_SPC700_SDSP": {
            "possibility_space":   0.80,
            "constraint":          0.88,
            "attractor_stability": 0.65,
            "basin_permeability":  0.82,
            "recurrence_depth":    0.90,
        },
        "YM2151": {
            "possibility_space":   0.82,
            "constraint":          0.80,
            "attractor_stability": 0.68,
            "basin_permeability":  0.72,
            "recurrence_depth":    0.88,
        },
        "YM2413": {
            "possibility_space":   0.65,
            "constraint":          0.50,
            "attractor_stability": 0.60,
            "basin_permeability":  0.65,
            "recurrence_depth":    0.55,
        },
        "YM3812": {
            "possibility_space":   0.72,
            "constraint":          0.68,
            "attractor_stability": 0.62,
            "basin_permeability":  0.70,
            "recurrence_depth":    0.70,
        },
        "AY8910": {
            "possibility_space":   0.30,
            "constraint":          0.35,
            "attractor_stability": 0.48,
            "basin_permeability":  0.55,
            "recurrence_depth":    0.25,
        },
        "HuC6280": {
            "possibility_space":   0.60,
            "constraint":          0.65,
            "attractor_stability": 0.58,
            "basin_permeability":  0.62,
            "recurrence_depth":    0.65,
        },
        "NES_APU": {
            "possibility_space":   0.35,
            "constraint":          0.40,
            "attractor_stability": 0.55,
            "basin_permeability":  0.50,
            "recurrence_depth":    0.30,
        },
        "YM2203": {     # OPN — 3 FM + SSG (AY-3-8910 compatible)
            "possibility_space":   0.70,
            "constraint":          0.72,
            "attractor_stability": 0.62,
            "basin_permeability":  0.68,
            "recurrence_depth":    0.72,
        },
        "YM2608": {     # OPNA — 6 FM + SSG + ADPCM (PC-88, Sega System E)
            "possibility_space":   0.88,
            "constraint":          0.84,
            "attractor_stability": 0.70,
            "basin_permeability":  0.78,
            "recurrence_depth":    0.92,
        },
        "YM2610": {     # OPNB — 4 FM + SSG + ADPCM (Neo Geo)
            "possibility_space":   0.85,
            "constraint":          0.82,
            "attractor_stability": 0.68,
            "basin_permeability":  0.76,
            "recurrence_depth":    0.88,
        },
        "YM3526": {     # OPL — 9 operators (MSX-MUSIC base)
            "possibility_space":   0.62,
            "constraint":          0.58,
            "attractor_stability": 0.60,
            "basin_permeability":  0.65,
            "recurrence_depth":    0.60,
        },
        "YMF262": {     # OPL3 — 18 operators, stereo, 4-op modes
            "possibility_space":   0.80,
            "constraint":          0.75,
            "attractor_stability": 0.68,
            "basin_permeability":  0.74,
            "recurrence_depth":    0.80,
        },
        "YMF278B": {    # OPL4 — OPL3 + wavetable ROM
            "possibility_space":   0.85,
            "constraint":          0.78,
            "attractor_stability": 0.70,
            "basin_permeability":  0.76,
            "recurrence_depth":    0.83,
        },
        "DMG": {        # Game Boy sound — 2 pulse + 1 wave + 1 noise
            "possibility_space":   0.28,
            "constraint":          0.32,
            "attractor_stability": 0.52,
            "basin_permeability":  0.45,
            "recurrence_depth":    0.22,
        },
        "K051649": {    # SCC (Konami wavetable, 5 channels)
            "possibility_space":   0.45,
            "constraint":          0.50,
            "attractor_stability": 0.55,
            "basin_permeability":  0.58,
            "recurrence_depth":    0.42,
        },
        "K054539": {    # Konami Advanced ADPCM
            "possibility_space":   0.75,
            "constraint":          0.70,
            "attractor_stability": 0.65,
            "basin_permeability":  0.72,
            "recurrence_depth":    0.78,
        },
    }

    data = _VECTORS.get(chip_name)
    if not data:
        return None
    return SubstrateVector(chip_id=chip_name, **data)


# ---------------------------------------------------------------------------
# Library metadata join
# ---------------------------------------------------------------------------

def _join_library_metadata(file_path: Path, analysis: TrackAnalysis) -> None:
    """
    Join library metadata from codex/library/music/ into analysis.
    Match order: exact path → title+artist → filename stem.
    Adds: library_title, library_artist, library_game, library_platform,
          library_year, library_is_loved, library_meta.
    """
    # Walk up to find Helix root (contains codex/)
    root = file_path
    for _ in range(10):
        if (root / "codex").exists():
            break
        root = root.parent

    library_root = root / "codex" / "library" / "music"
    if not library_root.exists():
        return

    stem = file_path.stem.lower()
    best: Optional[dict] = None

    # Search all JSON files in library
    for json_file in library_root.rglob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            # Handle both single records and lists
            records = data if isinstance(data, list) else [data]
            for record in records:
                rec_path = str(record.get("file_path", record.get("path", ""))).lower()
                rec_title = str(record.get("title", record.get("name", ""))).lower()

                # Priority 1: exact path match
                if str(file_path).lower() in rec_path or rec_path in str(file_path).lower():
                    best = record
                    break
                # Priority 2: stem match
                if stem and stem in rec_path:
                    best = record
        except Exception:
            continue
        if best:
            break

    if not best:
        return

    analysis.library_title    = best.get("title", best.get("name", ""))
    analysis.library_artist   = best.get("artist", best.get("composer", ""))
    analysis.library_game     = best.get("game", best.get("album", ""))
    analysis.library_platform = best.get("platform", best.get("system", ""))
    analysis.library_year     = str(best.get("year", best.get("date", "")))
    analysis.library_is_loved = bool(best.get("loved", best.get("rating", 0)))
    analysis.library_meta     = best


# ---------------------------------------------------------------------------
# Tier C: waveform analysis
# ---------------------------------------------------------------------------

def _run_waveform(path: Path) -> Optional[WaveformFeatures]:
    """Run waveform analysis (librosa + madmom)."""
    try:
        result = _router.waveform_analyze(path)
        if not result.get("available", False):
            return None
        # spectral_centroid may be a dict (librosa) or float (essentia)
        sc = result.get("spectral_centroid", 0.0)
        sc_val = sc.get("mean", 0.0) if isinstance(sc, dict) else float(sc or 0.0)

        dyn = result.get("dynamic_envelope", {})
        dyn_range = result.get("dynamic_range",
                               dyn.get("peak_rms", 0.0) - dyn.get("mean_rms", 0.0))

        # chord_sequence [{start, end, chord}] → histogram over 24 chord classes
        chord_seq = result.get("chord_sequence", [])
        chord_histogram = result.get("chord_histogram", [0.0] * 24)
        if chord_seq and all(v == 0.0 for v in chord_histogram):
            # build duration-weighted histogram from chord_sequence
            counts = [0.0] * 24
            _chord_labels = [
                "C","C#","D","D#","E","F","F#","G","G#","A","A#","B",
                "Cm","C#m","Dm","D#m","Em","Fm","F#m","Gm","G#m","Am","A#m","Bm",
            ]
            for seg in chord_seq:
                label = str(seg.get("chord", ""))
                dur   = float(seg.get("end", 0)) - float(seg.get("start", 0))
                if label in _chord_labels:
                    counts[_chord_labels.index(label)] += dur
            total = sum(counts) or 1.0
            chord_histogram = [v / total for v in counts]

        return WaveformFeatures(
            bpm               = result.get("bpm") or result.get("tempo"),
            key               = result.get("key_label") or result.get("key"),
            key_strength      = result.get("key_confidence") or result.get("key_strength"),
            spectral_centroid = sc_val,
            spectral_complexity = result.get("spectral_complexity", 0.0),
            dissonance        = result.get("dissonance", 0.0),
            dynamic_complexity = result.get("dynamic_complexity", 0.0),
            hfc               = result.get("hfc", 0.0),
            tonal_centroid    = result.get("tonal_centroid", [0.0] * 6),
            chord_histogram   = chord_histogram,
            mfcc_means        = result.get("mfcc_means", [0.0] * 13),
            chroma_means      = result.get("chroma_means", [0.0] * 12),
            spectral_contrast = result.get("spectral_contrast", [0.0] * 7),
            tonnetz_means     = result.get("tonnetz_means", [0.0] * 6),
            onset_density     = result.get("onset_density", 0.0),
            dynamic_range     = float(dyn_range or 0.0),
            adapter           = result.get("adapter", ""),
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Tier B: symbolic analysis
# ---------------------------------------------------------------------------

def _run_symbolic(
    midi_path: Path,
    midi_source: str,
    loop_point_s: Optional[float] = None,
) -> Optional[SymbolicFeatures]:
    """
    Run symbolic MIDI analysis and return SymbolicFeatures.
    """
    from model.domains.music.analysis.symbolic_analyzer import analyze_midi, SymbolicAnalysis

    try:
        sa: SymbolicAnalysis = analyze_midi(midi_path, midi_source=midi_source,
                                             loop_point_s=loop_point_s)
        if sa.error:
            return None

        # Map SymbolicAnalysis → SymbolicFeatures (unified schema)
        return SymbolicFeatures(
            note_count           = sa.total_notes,
            unique_pitches       = sa.unique_pitches,
            pitch_range          = sa.pitch_range,
            pitch_center         = sa.pitch_center,
            pitch_entropy        = sa.pitch_entropy,
            avg_note_duration    = sa.duration_s / max(1, sa.total_notes),
            rhythmic_entropy     = sa.rhythmic_entropy,
            note_density         = sa.note_density,
            active_channels      = sa.active_channels,
            estimated_key        = sa.estimated_key,
            loop_start_beat      = None,  # could compute from loop_point_s × tempo
            loop_end_beat        = None,
            channel_note_counts  = sa.channel_note_counts,
            channel_pitch_ranges = sa.channel_pitch_ranges,
            midi_source          = midi_source,
            # Music theory fields (stored in library_meta for now, full schema extension TBD)
        )
    except Exception:
        return None


def _run_symbolic_full(
    midi_path: Path,
    midi_source: str,
    loop_point_s: Optional[float] = None,
) -> tuple[Optional[SymbolicFeatures], dict]:
    """Returns (SymbolicFeatures, full_symbolic_dict) for the rich music theory layer."""
    from model.domains.music.analysis.symbolic_analyzer import analyze_midi
    from dataclasses import asdict

    try:
        sa = analyze_midi(midi_path, midi_source=midi_source, loop_point_s=loop_point_s)
        sf = _run_symbolic(midi_path, midi_source, loop_point_s)
        return sf, asdict(sa)
    except Exception:
        return None, {}


# ---------------------------------------------------------------------------
# VGM pipeline
# ---------------------------------------------------------------------------

def _analyze_vgm(path: Path) -> TrackAnalysis:
    from model.domains.music.parsing.vgm_parser import parse as vgm_parse, VGMEvent

    track = vgm_parse(path)
    if track.error:
        return TrackAnalysis.error_record(path, track.error)

    h = track.header
    loop_s = (0x1C + h.loop_offset) / 44100.0 if h.loop_offset else None

    # Chip list and Substrate Capability Vector
    chips = _vgm_chip_names(h)
    primary_chip = chips[0] if chips else ""

    analysis = TrackAnalysis(
        file_path     = str(path),
        format        = "VGM" if path.suffix.lower() == ".vgm" else "VGZ",
        chips         = chips,
        has_loop      = bool(h.loop_offset),
        loop_start_s  = loop_s,
        duration_s    = h.total_samples / 44100.0,
        analysis_tier = "A",
        confidence    = 0.7,
    )

    # Structural section: loop point
    if loop_s:
        analysis.sections.append(StructuralSection(
            time_s=0.0, label="loop_start", confidence=1.0
        ))
        analysis.sections.append(StructuralSection(
            time_s=loop_s, label="loop_seam", confidence=1.0
        ))

    # Substrate Capability Vector
    if primary_chip:
        analysis.substrate = _substrate_for_chip(primary_chip)

    # Tier A: note events from hardware register trace (key-on/off from chip writes)
    note_events = _extract_vgm_note_events(track.events, chips)
    analysis.note_events = note_events
    if note_events:
        analysis.analysis_tier = "A"

    # DCP proxies from loop structure
    if loop_s and note_events:
        analysis.dcp = _compute_vgm_dcp(note_events, loop_s, analysis.duration_s)

    _join_library_metadata(path, analysis)

    # Tier B: symbolic analysis — reconstruct MIDI from register trace, run music21
    try:
        from model.domains.music.domain_analysis.symbolic_music.vgm_note_reconstructor import reconstruct
        from model.domains.music.analysis.symbolic_analyzer import analyze_midi
        from dataclasses import asdict
        import tempfile
        import os
        from pathlib import Path

        score = reconstruct(track)
        
        # We write the extracted score into a temporary MIDI file. 
        # This bridges the gap, allowing music21 to run deeper 
        # Schenkerian/Roman numeral analysis over the hardware log.
        import pretty_midi
        pm = pretty_midi.PrettyMIDI()
        
        # Group notes by channel to keep lines distinct
        channels: dict[int, list[pretty_midi.Note]] = {}
        if hasattr(score, 'notes') and score.notes:
            for note in score.notes:
                ch = note.channel
                if ch not in channels:
                    channels[ch] = []
                channels[ch].append(
                    pretty_midi.Note(
                        velocity=note.velocity if hasattr(note, 'velocity') else 100,
                        pitch=note.note if hasattr(note, 'note') else note.pitch,
                        start=note.start if hasattr(note, 'start') else note.onset_s,
                        end=(note.start + note.duration) if hasattr(note, 'duration') else note.offset_s
                    )
                )

        for ch_idx, notes in channels.items():
            inst = pretty_midi.Instrument(program=0)
            inst.notes = notes
            pm.instruments.append(inst)

        if channels:
            fd, temp_path = tempfile.mkstemp(suffix=".mid")
            os.close(fd)
            try:
                pm.write(temp_path)
                sa = analyze_midi(Path(temp_path), midi_source="vgm_reconstructor",
                                 loop_point_s=loop_s)
                if sa and not getattr(sa, 'error', ""):
                    analysis.symbolic = sa
                    analysis.library_meta["symbolic_full"] = asdict(sa)
                    analysis.analysis_tier = "AB"
                    analysis.confidence    = 0.9

            except Exception:
                pass
            finally:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass


    except Exception:
        pass  # Tier B is best-effort; Tier A note events are still available

    # 🔴 HACK: Extract Timbre Patches explicitly requested for Sega Sound Team matching
    if track.events and primary_chip == "YM2612":
        analysis.library_meta["fm_patch_hashes"] = _extract_vgm_fm_patches(track.events)

    return analysis


def _extract_vgm_fm_patches(events) -> list[dict]:
    """
    Extracts complete FM synthesis patches used by the composer at the moment of Key-On.
    Decodes the YM2612 registers into literal sound-design presets (vgm2pre-style).
    Returns a list of unique decoded patch dictionaries.
    """
    import json
    fm_state = {p: {c: {r: 0 for r in range(0x100)} for c in range(3)} for p in (0, 1)}
    unique_patches = set()

    for ev in events:
        if ev.kind == "ym2612_p0":
            port = 0
        elif ev.kind == "ym2612_p1":
            port = 1
        else:
            continue
            
        reg, val = ev.reg, ev.val
        
        if 0x30 <= reg <= 0x9F or 0xB0 <= reg <= 0xB4:
            ch_idx = reg & 0x03
            if ch_idx < 3:
                fm_state[port][ch_idx][reg] = val
                
        if ev.kind == "ym2612_p0" and reg == 0x28:
            ch_idx = val & 0x03
            port_idx = (val >> 2) & 0x01
            op_mask = (val >> 4) & 0x0F
            if ch_idx < 3 and op_mask > 0:
                c_state = fm_state[port_idx][ch_idx]
                
                # Decode directly to preset
                patch = {
                    "alg": c_state[0xB0] & 0x07,
                    "fb": (c_state[0xB0] >> 3) & 0x07,
                    "ams": (c_state[0xB4] >> 4) & 0x03,
                    "pms": c_state[0xB4] & 0x07,
                    "lr": (c_state[0xB4] >> 6) & 0x03,
                    "operators": []
                }
                
                for op_num, op_offset in enumerate((0, 8, 4, 12)):
                    op = {
                        "detune": (c_state[0x30 + op_offset + ch_idx] >> 4) & 0x07,
                        "multiplier": c_state[0x30 + op_offset + ch_idx] & 0x0F,
                        "total_level": c_state[0x40 + op_offset + ch_idx] & 0x7F,
                        "key_scale": (c_state[0x50 + op_offset + ch_idx] >> 6) & 0x03,
                        "attack_rate": c_state[0x50 + op_offset + ch_idx] & 0x1F,
                        "am_enable": (c_state[0x60 + op_offset + ch_idx] >> 7) & 0x01,
                        "decay_1_rate": c_state[0x60 + op_offset + ch_idx] & 0x1F,
                        "decay_2_rate": c_state[0x70 + op_offset + ch_idx] & 0x1F,
                        "sustain_level": (c_state[0x80 + op_offset + ch_idx] >> 4) & 0x0F,
                        "release_rate": c_state[0x80 + op_offset + ch_idx] & 0x0F
                    }
                    patch["operators"].append(op)
                
                # Serialize to string to make hashable, ignore empty blocks
                patch_str = json.dumps(patch, sort_keys=True)
                # Quick filter to ignore complete 0-state null patches that haven't been loaded
                if sum(op["attack_rate"] for op in patch["operators"]) > 0:
                    unique_patches.add(patch_str)
                    
    # Return as list of parsed dicts so the pipeline can read them functionally
    return [json.loads(p) for p in unique_patches]


def _extract_vgm_note_events(events, chips: list[str]) -> list[NoteEvent]:
    """
    Extract note-on events from VGM register stream for all supported chips.

    Supported chips:
      YM2612 / YM2203 / YM2608 / YM2610  — OPN family (block/fnum + key-on reg 0x28)
      YM2151                              — OPM (key-on reg 0x08, KC pitch)
      YM2413                              — OPLL (key-on bit 5 in 0x20-0x28)
      YM3812 / YM3526 / YMF262           — OPL family (key-on bit 5 in 0xB0-0xB8)
      SN76489 (PSG)                       — latch/data byte, 3 tone channels
      AY8910                              — 3 tone channels, amplitude regs 0x08-0x0A
      NES APU                             — 5 channels via reg 0x00-0x17
      DMG (Game Boy)                      — 4 channels via reg 0x10-0x3E
      HuC6280 (PC Engine)                 — 6 channels via reg 0x00-0x07
    """
    import math
    note_events: list[NoteEvent] = []

    # -------------------------------------------------------------------------
    # Shared OPN family handler: YM2612, YM2203, YM2608, YM2610
    # -------------------------------------------------------------------------
    def _handle_opn(ev, kind_p0: str, kind_p1: str, ch_base: int, prefix: str):
        port = 1 if ev.kind == kind_p1 else 0
        ch_offset = 3 if port else 0
        # Key-on: register 0x28 only appears on port-0 events.
        # val bits[2:0] encode channel: 0-2 = bank-0 (ch0-2), 4-6 = bank-1 (ch3-5).
        # Values 3 and 7 are invalid. Bit 2 is the bank selector.
        if ev.kind == kind_p0 and ev.reg == 0x28:
            ch_raw  = ev.val & 0x07
            if ch_raw == 3 or ch_raw == 7:
                pass  # invalid slot — skip
            else:
                ch_bank = (ch_raw >> 2) & 0x01        # 0 = first bank, 1 = second bank
                ch_within = ch_raw & 0x03              # position within bank (0-2)
                ch_idx  = ch_within + ch_bank * 3      # logical channel 0-5
                op_mask = (ev.val >> 4) & 0x0F
                ch_id   = f"{prefix}{ch_idx}"
                st = _fm_state.setdefault(ch_id, {"block": 0, "fnum": 0,
                                                   "fnum_low": 0, "pitch_midi": -1})
                if op_mask > 0 and st["pitch_midi"] >= 0:
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=ch_base + ch_idx,
                        pitch_midi=st["pitch_midi"], pitch_hz=_midi_to_hz(st["pitch_midi"]),
                        velocity=0.7, is_loop=ev.is_loop,
                    ))
        # fnum high + block
        elif 0xA4 <= ev.reg <= 0xA6:
            ch_idx = ev.reg - 0xA4
            ch_id  = f"{prefix}{ch_idx + ch_offset}"
            st = _fm_state.setdefault(ch_id, {"block": 0, "fnum": 0,
                                               "fnum_low": 0, "pitch_midi": -1})
            st["block"] = (ev.val >> 3) & 0x07
            st["fnum"]  = ((ev.val & 0x07) << 8) | st["fnum_low"]
            st["pitch_midi"] = _ym2612_to_midi(st["block"], st["fnum"])
        # fnum low
        elif 0xA0 <= ev.reg <= 0xA2:
            ch_idx = ev.reg - 0xA0
            ch_id  = f"{prefix}{ch_idx + ch_offset}"
            _fm_state.setdefault(ch_id, {"block": 0, "fnum": 0,
                                          "fnum_low": 0, "pitch_midi": -1})["fnum_low"] = ev.val

    # Per-chip state tables
    _fm_state:  dict[str, dict] = {}   # OPN family: ch_id → {block, fnum, fnum_low, pitch_midi}
    _opl_state: dict[str, dict] = {}   # OPL family
    _psg_state: dict[int, dict] = {}   # SN76489: ch → {period_low, period_high, attenuation}
    _ay_state:  dict[str, int]  = {}   # AY8910 registers
    _nes_state: dict[str, dict] = {}   # NES APU
    _dmg_state: dict[str, dict] = {}   # Game Boy DMG
    _huc_state: dict[str, dict] = {}   # HuC6280
    _huc_sel:   int             = 0    # HuC6280 selected channel

    for ev in events:

        # ------------------------------------------------------------------
        # YM2612 (Mega Drive)
        # ------------------------------------------------------------------
        if ev.kind in ("ym2612_p0", "ym2612_p1"):
            _handle_opn(ev, "ym2612_p0", "ym2612_p1", 0, "FM2612_")

        # ------------------------------------------------------------------
        # YM2203 (OPN — PC-88, Arcade)  ch_base=20 so IDs don't collide
        # ------------------------------------------------------------------
        elif ev.kind == "ym2203":
            # YM2203 has only 3 channels, single port
            if ev.reg == 0x28:  # key-on
                ch_idx  = ev.val & 0x03
                op_mask = (ev.val >> 4) & 0x0F
                ch_id   = f"FM2203_{ch_idx}"
                st = _fm_state.setdefault(ch_id, {"block": 0, "fnum": 0,
                                                    "fnum_low": 0, "pitch_midi": -1})
                if op_mask > 0 and st["pitch_midi"] >= 0:
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=20 + ch_idx,
                        pitch_midi=st["pitch_midi"], pitch_hz=_midi_to_hz(st["pitch_midi"]),
                        velocity=0.7, is_loop=ev.is_loop,
                    ))
            elif 0xA4 <= ev.reg <= 0xA6:
                ch_idx = ev.reg - 0xA4
                ch_id  = f"FM2203_{ch_idx}"
                st = _fm_state.setdefault(ch_id, {"block": 0, "fnum": 0,
                                                    "fnum_low": 0, "pitch_midi": -1})
                st["block"] = (ev.val >> 3) & 0x07
                st["fnum"]  = ((ev.val & 0x07) << 8) | st["fnum_low"]
                st["pitch_midi"] = _ym2612_to_midi(st["block"], st["fnum"])
            elif 0xA0 <= ev.reg <= 0xA2:
                ch_idx = ev.reg - 0xA0
                _fm_state.setdefault(f"FM2203_{ch_idx}", {"block": 0, "fnum": 0,
                                                           "fnum_low": 0, "pitch_midi": -1})["fnum_low"] = ev.val

        # ------------------------------------------------------------------
        # YM2608 (OPNA — PC-88VA, Arcade) ch_base=30
        # ------------------------------------------------------------------
        elif ev.kind in ("ym2608_p0", "ym2608_p1"):
            _handle_opn(ev, "ym2608_p0", "ym2608_p1", 30, "FM2608_")

        # ------------------------------------------------------------------
        # YM2610 (OPNB — Neo Geo) ch_base=40
        # ------------------------------------------------------------------
        elif ev.kind in ("ym2610_p0", "ym2610_p1"):
            _handle_opn(ev, "ym2610_p0", "ym2610_p1", 40, "FM2610_")

        # ------------------------------------------------------------------
        # YM2151 (OPM — X68000, Arcade)
        # Key-on: reg 0x08 (bits 6-3 = slot mask, bits 2-0 = channel)
        # KC pitch: reg 0x28+ch (bits 6-4 = octave, bits 3-0 = key code)
        # ------------------------------------------------------------------
        elif ev.kind == "ym2151":
            if ev.reg == 0x08:
                ch_idx  = ev.val & 0x07
                slot_mask = (ev.val >> 3) & 0x0F
                ch_id   = f"OPM_{ch_idx}"
                kc = _fm_state.get(ch_id, {}).get("kc", -1)
                if slot_mask > 0 and kc >= 0:
                    # YM2151 KC: octave = kc>>4, note = kc & 0x0F
                    # note codes skip 0x0C (C#?) — approximate with semitone math
                    octave = (kc >> 4) & 0x07
                    note   = kc & 0x0F
                    # Remap 16-code note to 12-tone chromatic (YM2151 uses 4 unused codes)
                    note_map = {0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:11,12:11,13:11,14:11,15:11}
                    semitone = note_map.get(note, note % 12)
                    midi = (octave + 1) * 12 + semitone
                    midi = max(0, min(127, midi))
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=50 + ch_idx,
                        pitch_midi=midi, pitch_hz=_midi_to_hz(midi),
                        velocity=0.7, is_loop=ev.is_loop,
                    ))
            elif 0x28 <= ev.reg <= 0x2F:  # KC registers
                ch_id = f"OPM_{ev.reg - 0x28}"
                _fm_state.setdefault(ch_id, {})["kc"] = ev.val

        # ------------------------------------------------------------------
        # YM2413 (OPLL — MSX-MUSIC, Sega Master System FM)
        # Key-on bit 5 in regs 0x20-0x28; F-number in 0x10-0x18 + 0x20-0x28
        # ------------------------------------------------------------------
        elif ev.kind == "ym2413":
            if 0x20 <= ev.reg <= 0x28:
                ch_idx = ev.reg - 0x20
                key_on = (ev.val >> 4) & 0x01
                block  = (ev.val >> 1) & 0x07
                fnum_hi = ev.val & 0x01
                ch_id  = f"OPLL_{ch_idx}"
                st = _opl_state.setdefault(ch_id, {"fnum_low": 0, "block": 0, "pitch_midi": -1})
                st["block"]   = block
                st["fnum_hi"] = fnum_hi
                fnum = (fnum_hi << 8) | st.get("fnum_low", 0)
                # OPLL F-number → pitch (similar to OPL2)
                if fnum > 0:
                    f_hz = fnum * 49716.0 / (1 << (19 - block))
                    midi = 69 + 12 * math.log2(f_hz / 440.0) if f_hz > 0 else -1
                    st["pitch_midi"] = max(0, min(127, round(midi))) if f_hz > 0 else -1
                if key_on and st.get("pitch_midi", -1) >= 0:
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=60 + ch_idx,
                        pitch_midi=st["pitch_midi"], pitch_hz=_midi_to_hz(st["pitch_midi"]),
                        velocity=0.7, is_loop=ev.is_loop,
                    ))
            elif 0x10 <= ev.reg <= 0x18:
                ch_idx = ev.reg - 0x10
                _opl_state.setdefault(f"OPLL_{ch_idx}", {})["fnum_low"] = ev.val

        # ------------------------------------------------------------------
        # YM3812 / YM3526 / YMF262 (OPL2/OPL3)
        # Key-on bit 5 in 0xB0-0xB8; F-number in 0xA0-0xA8 + 0xB0-0xB8
        # ------------------------------------------------------------------
        elif ev.kind in ("ym3812", "ym3526", "y8950"):
            if 0xB0 <= ev.reg <= 0xB8:
                ch_idx  = ev.reg - 0xB0
                key_on  = (ev.val >> 5) & 0x01
                block   = (ev.val >> 2) & 0x07
                fnum_hi = ev.val & 0x03
                ch_id   = f"OPL2_{ch_idx}"
                st = _opl_state.setdefault(ch_id, {"fnum_low": 0, "pitch_midi": -1})
                fnum = (fnum_hi << 8) | st.get("fnum_low", 0)
                if fnum > 0:
                    f_hz = fnum * 49716.0 / (1 << (19 - block))
                    midi = 69 + 12 * math.log2(f_hz / 440.0) if f_hz > 0 else -1
                    st["pitch_midi"] = max(0, min(127, round(midi))) if f_hz > 0 else -1
                if key_on and st.get("pitch_midi", -1) >= 0:
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=70 + ch_idx,
                        pitch_midi=st["pitch_midi"], pitch_hz=_midi_to_hz(st["pitch_midi"]),
                        velocity=0.7, is_loop=ev.is_loop,
                    ))
            elif 0xA0 <= ev.reg <= 0xA8:
                ch_idx = ev.reg - 0xA0
                _opl_state.setdefault(f"OPL2_{ch_idx}", {})["fnum_low"] = ev.val

        elif ev.kind in ("ymf262_p0", "ymf262_p1"):
            port = 1 if ev.kind == "ymf262_p1" else 0
            if 0xB0 <= ev.reg <= 0xB8:
                ch_idx  = ev.reg - 0xB0 + (9 if port else 0)
                key_on  = (ev.val >> 5) & 0x01
                block   = (ev.val >> 2) & 0x07
                fnum_hi = ev.val & 0x03
                ch_id   = f"OPL3_{ch_idx}"
                st = _opl_state.setdefault(ch_id, {"fnum_low": 0, "pitch_midi": -1})
                fnum = (fnum_hi << 8) | st.get("fnum_low", 0)
                if fnum > 0:
                    f_hz = fnum * 49716.0 / (1 << (19 - block))
                    midi = 69 + 12 * math.log2(f_hz / 440.0) if f_hz > 0 else -1
                    st["pitch_midi"] = max(0, min(127, round(midi))) if f_hz > 0 else -1
                if key_on and st.get("pitch_midi", -1) >= 0:
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=80 + ch_idx,
                        pitch_midi=st["pitch_midi"], pitch_hz=_midi_to_hz(st["pitch_midi"]),
                        velocity=0.7, is_loop=ev.is_loop,
                    ))
            elif 0xA0 <= ev.reg <= 0xA8:
                ch_idx = ev.reg - 0xA0 + (9 if port else 0)
                _opl_state.setdefault(f"OPL3_{ch_idx}", {})["fnum_low"] = ev.val

        # ------------------------------------------------------------------
        # SN76489 / PSG — latch byte val format:
        #   bit 7=1 (latch): bit6-5 = channel (0-2 tone, 3 noise),
        #                    bit4 = type (0=freq, 1=vol), bits3-0 = data nibble
        #   bit 7=0 (data):  6 MSBs of frequency (channel from last latch)
        # ------------------------------------------------------------------
        elif ev.kind == "psg":
            val = ev.val
            if val & 0x80:  # latch byte
                ch  = (val >> 5) & 0x03
                typ = (val >> 4) & 0x01
                dat = val & 0x0F
                st  = _psg_state.setdefault(ch, {"period_low": 0, "period_hi": 0, "attenuation": 15})
                st["_last_latch"] = (ch, typ)
                if typ == 0:   # frequency latch — lower 4 bits
                    st["period_low"] = dat
                else:          # volume write
                    prev_att = st["attenuation"]
                    st["attenuation"] = dat
                    # Note-on: went from silent (15) to audible
                    if prev_att == 15 and dat < 15 and ch < 3:
                        # compute hz from period
                        period = (st["period_hi"] << 4) | st["period_low"]
                        # PSG clock typically 3.58 MHz on SMS, 3.546895 on PAL
                        psg_clock = 3_579_545
                        f_hz = psg_clock / (32 * period) if period > 0 else 0.0
                        midi = _hz_to_midi(f_hz) if f_hz > 0 else -1
                        note_events.append(NoteEvent(
                            time_s=ev.time_s, channel=90 + ch,
                            pitch_midi=midi if midi >= 0 else 0,
                            pitch_hz=f_hz, velocity=(15 - dat) / 14.0,
                            is_loop=ev.is_loop,
                        ))
            else:  # data byte — update period high bits
                for ch, st in _psg_state.items():
                    if st.get("_last_latch", (None, 1))[1] == 0:  # last latch was freq
                        st["period_hi"] = val & 0x3F

        # ------------------------------------------------------------------
        # AY-3-8910 — 3 tone channels
        # Regs: 0-1 = ch A period, 2-3 = ch B, 4-5 = ch C
        # Regs: 8-10 = amplitude A/B/C (bit4=env, bits3-0=level)
        # ------------------------------------------------------------------
        elif ev.kind == "ay8910":
            _ay_state[ev.reg] = ev.val
            # Amplitude regs 0x08-0x0A — note-on when level goes above 0
            if 0x08 <= ev.reg <= 0x0A:
                ch_idx  = ev.reg - 0x08
                level   = ev.val & 0x0F
                prev    = _ay_state.get(ev.reg + 0x10, 0)  # shadow reg for prev
                _ay_state[ev.reg + 0x10] = ev.val
                if level > 0 and (prev & 0x0F) == 0:
                    # compute pitch from period regs
                    lo = _ay_state.get(ch_idx * 2, 0)
                    hi = _ay_state.get(ch_idx * 2 + 1, 0) & 0x0F
                    period = (hi << 8) | lo
                    ay_clock = 2_000_000  # common AY clock
                    f_hz = ay_clock / (16 * period) if period > 0 else 0.0
                    midi = _hz_to_midi(f_hz) if f_hz > 0 else -1
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=95 + ch_idx,
                        pitch_midi=midi if midi >= 0 else 0,
                        pitch_hz=f_hz, velocity=level / 15.0,
                        is_loop=ev.is_loop,
                    ))

        # ------------------------------------------------------------------
        # NES APU — 5 channels; detect note-on from length counter reloads
        # Regs 0x00-0x03 pulse1, 0x04-0x07 pulse2, 0x08-0x0B triangle,
        #      0x0C-0x0F noise, 0x10-0x13 DMC
        # Reg x3 (e.g. 0x03 for pulse1) = period high + length counter → key-on
        # ------------------------------------------------------------------
        elif ev.kind == "nes_apu":
            reg = ev.reg
            # Key-on events: writes to the 4th register of each channel
            if reg in (0x03, 0x07, 0x0B, 0x13):
                ch_map = {0x03: (100, "P1"), 0x07: (101, "P2"),
                          0x0B: (102, "TRI"), 0x13: (104, "DMC")}
                ch_base, prefix = ch_map[reg]
                lo = _nes_state.get(prefix, {}).get("period_lo", 0)
                period_hi = ev.val & 0x07
                period = (period_hi << 8) | lo
                nes_clock = 1_789_773
                if reg == 0x0B:  # triangle
                    f_hz = nes_clock / (32 * (period + 1)) if period >= 0 else 0.0
                else:
                    f_hz = nes_clock / (16 * (period + 1)) if period >= 0 else 0.0
                midi = _hz_to_midi(f_hz) if f_hz > 0 else -1
                note_events.append(NoteEvent(
                    time_s=ev.time_s, channel=ch_base,
                    pitch_midi=midi if midi >= 0 else 0,
                    pitch_hz=f_hz, velocity=0.7,
                    is_loop=ev.is_loop,
                ))
            elif reg in (0x02, 0x06, 0x0A):
                prefix_map = {0x02: "P1", 0x06: "P2", 0x0A: "TRI"}
                _nes_state.setdefault(prefix_map[reg], {})["period_lo"] = ev.val

        # ------------------------------------------------------------------
        # Game Boy DMG — 4 channels mapped to regs 0x10-0x3E (relative to 0xFF10)
        # Channel 1 pulse: 0x10-0x14, Ch2 pulse: 0x15-0x19
        # Ch3 wave: 0x1A-0x1E, Ch4 noise: 0x1F-0x23
        # Freq high reg (trigger bit 7): 0x14, 0x19, 0x1E, 0x23
        # ------------------------------------------------------------------
        elif ev.kind == "dmg":
            reg = ev.reg
            if reg in (0x14, 0x19, 0x1E, 0x23):
                trigger = (ev.val >> 7) & 0x01
                if trigger:
                    ch_map  = {0x14: (110, "CH1"), 0x19: (111, "CH2"),
                               0x1E: (112, "CH3"), 0x23: (113, "CH4")}
                    ch_base, prefix = ch_map[reg]
                    lo = _dmg_state.get(prefix, {}).get("freq_lo", 0)
                    hi = ev.val & 0x07
                    period = (hi << 8) | lo
                    dmg_clock = 4_194_304
                    f_hz = dmg_clock / (32 * (2048 - period)) if period < 2048 else 0.0
                    midi = _hz_to_midi(f_hz) if f_hz > 0 else -1
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=ch_base,
                        pitch_midi=midi if midi >= 0 else 0,
                        pitch_hz=f_hz, velocity=0.7,
                        is_loop=ev.is_loop,
                    ))
            elif reg in (0x13, 0x18, 0x1D):
                prefix_map = {0x13: "CH1", 0x18: "CH2", 0x1D: "CH3"}
                _dmg_state.setdefault(prefix_map[reg], {})["freq_lo"] = ev.val

        # ------------------------------------------------------------------
        # HuC6280 (PC Engine PSG) — 6 channels
        # Reg 0x00 = channel select, 0x02 = freq lo, 0x03 = freq hi
        # Reg 0x04 = volume (bit7=on/off, bits3-0=volume)
        # ------------------------------------------------------------------
        elif ev.kind == "huc6280":
            if ev.reg == 0x00:
                _huc_sel = ev.val & 0x07
            elif ev.reg == 0x02:
                _huc_state.setdefault(f"HUC{_huc_sel}", {})["freq_lo"] = ev.val
            elif ev.reg == 0x03:
                _huc_state.setdefault(f"HUC{_huc_sel}", {})["freq_hi"] = ev.val & 0x0F
            elif ev.reg == 0x04:
                on  = (ev.val >> 7) & 0x01
                vol = ev.val & 0x0F
                ch_id = f"HUC{_huc_sel}"
                st    = _huc_state.setdefault(ch_id, {})
                prev_on = st.get("on", 0)
                st["on"]  = on
                st["vol"] = vol
                # Note-on: channel just enabled
                if on and not prev_on:
                    lo = st.get("freq_lo", 0)
                    hi = st.get("freq_hi", 0)
                    period = (hi << 8) | lo
                    huc_clock = 3_579_545
                    f_hz = huc_clock / (32 * period) if period > 0 else 0.0
                    midi = _hz_to_midi(f_hz) if f_hz > 0 else -1
                    note_events.append(NoteEvent(
                        time_s=ev.time_s, channel=120 + _huc_sel,
                        pitch_midi=midi if midi >= 0 else 0,
                        pitch_hz=f_hz, velocity=vol / 15.0,
                        is_loop=ev.is_loop,
                    ))

    return note_events


def _ym2612_to_midi(block: int, fnum: int) -> int:
    """Convert YM2612 block/fnum to approximate MIDI note."""
    if fnum == 0:
        return -1
    import math
    # f_hz = fnum × clock / (144 × 2^(20 - block))
    # YM2612 clock typically 7.67 MHz on Mega Drive
    clock = 7_670_454
    f_hz  = fnum * clock / (144 * (1 << (20 - block)))
    if f_hz <= 0:
        return -1
    midi = 69 + 12 * math.log2(f_hz / 440.0)
    return max(0, min(127, round(midi)))


def _midi_to_hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0)) if midi >= 0 else 0.0


def _vgm_chip_names(header) -> list[str]:
    chips = []
    if getattr(header, "ym2612_clock",  0): chips.append("YM2612")
    if getattr(header, "sn76489_clock", 0): chips.append("SN76489")
    if getattr(header, "ym2151_clock",  0): chips.append("YM2151")
    if getattr(header, "ym2413_clock",  0): chips.append("YM2413")
    if getattr(header, "ym2203_clock",  0): chips.append("YM2203")
    if getattr(header, "ym2608_clock",  0): chips.append("YM2608")
    if getattr(header, "ym2610_clock",  0): chips.append("YM2610")
    if getattr(header, "ym3812_clock",  0): chips.append("YM3812")
    if getattr(header, "ym3526_clock",  0): chips.append("YM3526")
    if getattr(header, "y8950_clock",   0): chips.append("Y8950")
    if getattr(header, "ymf262_clock",  0): chips.append("YMF262")
    if getattr(header, "ymf278b_clock", 0): chips.append("YMF278B")
    if getattr(header, "ymf271_clock",  0): chips.append("YMF271")
    if getattr(header, "ymz280b_clock", 0): chips.append("YMZ280B")
    if getattr(header, "ay8910_clock",  0): chips.append("AY8910")
    if getattr(header, "dmg_clock",     0): chips.append("DMG")
    if getattr(header, "nes_apu_clock", 0): chips.append("NES_APU")
    if getattr(header, "huc6280_clock", 0): chips.append("HuC6280")
    if getattr(header, "k051649_clock", 0): chips.append("K051649")
    if getattr(header, "k054539_clock", 0): chips.append("K054539")
    return chips


def _compute_vgm_dcp(
    note_events: list[NoteEvent],
    loop_s: float,
    duration_s: float,
) -> DCPProxies:
    """
    Compute DCP proxies from VGM note events around the loop seam.
    The loop_offset gives us an explicit structural boundary — highest
    confidence DCP event type in the music domain.
    """
    import math

    if not note_events or loop_s <= 0:
        return DCPProxies()

    # Window: final 10% before seam = pre-seam tension zone
    window = duration_s * 0.1
    seam_start = max(0.0, loop_s - window)

    pre_events  = [e for e in note_events if seam_start <= e.time_s < loop_s]
    post_events = [e for e in note_events if loop_s <= e.time_s < loop_s + 2.0]
    all_events  = note_events

    if not pre_events:
        return DCPProxies()

    # Possibility space: pitch entropy of entire track (pre-loop region)
    pre_loop_events = [e for e in all_events if not e.is_loop]
    pitches = [e.pitch_midi for e in pre_loop_events if e.pitch_midi >= 0]
    pc_counts = [pitches.count(p % 12) for p in range(12)]
    total = sum(pc_counts)
    poss = -sum((c/total)*math.log2(c/total) for c in pc_counts if c > 0) / math.log2(12) if total else 0.0

    # Collapse: sharpness of density change at loop seam
    pre_density  = len(pre_events) / max(0.01, window)
    overall_density = len(all_events) / max(0.01, duration_s)
    collapse = min(1.0, max(0.0, pre_density / max(0.01, overall_density) - 1.0) / 2.0)

    # Tension: active channels in pre-seam window
    pre_channels = len({e.channel for e in pre_events})
    all_channels = len({e.channel for e in all_events})
    tension = pre_channels / max(1, all_channels)

    # Post-narrowing: channel count drop after seam
    post_channels = len({e.channel for e in post_events}) if post_events else 1
    post_narrow = max(0.0, 1.0 - (post_channels / max(1, pre_channels)))

    # Composite
    components = [poss, collapse, tension, post_narrow]
    available  = [c for c in components if c > 0]
    composite  = sum(available) / len(available) if available else 0.0

    qual = "FULL" if len(available) >= 4 else ("UNCONFIRMED" if len(available) >= 2 else "INSUFFICIENT")

    return DCPProxies(
        possibility_space = poss,
        collapse          = collapse,
        tension           = tension,
        post_narrowing    = post_narrow,
        composite         = composite,
        qualification     = qual,
    )


# ---------------------------------------------------------------------------
# SPC pipeline
# ---------------------------------------------------------------------------

def _analyze_spc(path: Path) -> TrackAnalysis:
    from model.domains.music.parsing.spc_parser import parse as spc_parse
    from core.engine.adapters.adapter_snes_spc import VOICE_COUNT, PITCH_FREQ_FORMULA

    spc = spc_parse(path)

    analysis = TrackAnalysis(
        file_path     = str(path),
        format        = "SPC",
        chips         = ["SNES_SPC700_SDSP"],
        voice_count   = VOICE_COUNT,  # 8
        analysis_tier = "A",
        confidence    = 0.5,
        substrate     = _substrate_for_chip("SNES_SPC700_SDSP"),
    )

    # Extract voice snapshots from DSP register state
    # SPCVoice is a dataclass — access fields directly, not via .get()
    if hasattr(spc, "voices") and spc.voices:
        for v in spc.voices:
            pitch_raw = v.pitch if hasattr(v, "pitch") else 0
            pitch_hz  = pitch_raw * 32000 / 0x1000
            midi      = _hz_to_midi(pitch_hz)
            analysis.voices.append(ChipVoiceSnapshot(
                voice_index  = v.voice_index,
                active       = v.active,
                pitch_raw    = pitch_raw,
                pitch_hz     = pitch_hz,
                pitch_midi   = midi,
                vol_l        = abs(v.vol_l) / 127.0,
                vol_r        = abs(v.vol_r) / 127.0,
                adsr_enabled = v.adsr_enabled,
                attack       = v.attack,
                decay        = v.decay,
                sustain      = v.sustain_level,
                release      = v.release,
                srcn         = v.srcn,
            ))
        analysis.active_voices = sum(1 for v in analysis.voices if v.active)

    # SPC has no explicit loop point in the header — loop detection requires emulation
    analysis.sections.append(StructuralSection(
        time_s=0.0, label="snapshot", confidence=1.0,
    ))

    # --- NEW: DSP Acoustic Profiles (Spatial/Mix fingerprint) ---
    analysis.library_meta["spc_acoustic_profile"] = {
        "echo_enabled": spc.echo_enabled,
        "echo_delay": spc.echo_delay,
        "echo_feedback": spc.echo_feedback,
        "echo_vol_l": spc.echo_vol_l,
        "echo_vol_r": spc.echo_vol_r,
        "fir_coefs": spc.fir_coefs,
        "mvol_l": spc.mvol_l,
        "mvol_r": spc.mvol_r
    }

    # --- NEW: BRR Sample Payload Hashing (Custom Soundfont fingerprint) ---
    try:
        import hashlib
        raw_spc_data = path.read_bytes()
        dir_offset = 0x100 + (spc.dir_page * 256)
        used_samples = {v.srcn for v in spc.voices if v.active or v.envx > 0}
        brr_hashes = {}
        for srcn in used_samples:
            entry_offset = dir_offset + (srcn * 4)
            if entry_offset + 4 <= len(raw_spc_data):
                start_ptr = raw_spc_data[entry_offset] | (raw_spc_data[entry_offset+1]<<8)
                ptr = 0x100 + start_ptr
                sample_data = bytearray()
                iters = 0
                while ptr + 9 <= len(raw_spc_data) and iters < 8000:
                    chunk = raw_spc_data[ptr:ptr+9]
                    sample_data.extend(chunk)
                    iters += 1
                    if chunk[0] & 0x01: # BRR end marker
                        break
                    ptr += 9
                if sample_data:
                    brr_hashes[srcn] = hashlib.md5(sample_data).hexdigest()
        analysis.library_meta["spc_brr_hashes"] = list(set(brr_hashes.values()))
    except Exception as e:
        analysis.library_meta["_spc_brr_err"] = str(e)

    _join_library_metadata(path, analysis)

    # Tier B: SPC2MID → MIDI → symbolic analysis
    analysis = _try_spc2mid(path, analysis)

    return analysis


def _hz_to_midi(hz: float) -> int:
    import math
    if hz <= 0:
        return -1
    m = 69 + 12 * math.log2(hz / 440.0)
    return max(0, min(127, round(m)))


def _try_spc2mid(path: Path, analysis: TrackAnalysis) -> TrackAnalysis:
    """
    Attempt SPC → MIDI via SPC2MID binary.
    SPC2MID is engine-specific. We try SNESNint (N-SPC, Nintendo) first
    as it covers the most SNES titles, then fall back to other binaries.

    Binary lookup order (from PATH or Helix tools/ directory):
      SNESNint.exe, SNESCapcom.exe, SNESSculpt.exe, SNESDW.exe, etc.
    """
    import shutil, subprocess

    # All SPC2MID engine binaries, roughly ordered by library coverage
    spc2mid_binaries = [
        "SNESNint",     # Nintendo N-SPC (FF, DQ, Zelda, Kirby, Mario, Donkey Kong, etc.)
        "SNESCapcom",   # Capcom (Mega Man X, Street Fighter II, Breath of Fire)
        "SNESSculpt",   # Sculptured Software (Mortal Kombat, Aero the Acro-Bat)
        "SNESDW",       # David Whittaker engine
        "SNESKAZe",     # KAZe / Meldac
        "SNESKrisalis", # Krisalis Software
        "SNESClimax",   # Climax Entertainment
        "SNESArc",      # Arc System Works
        "SNESProbe",    # Probe Software
        "SNESSV",       # Silicon & Synapse / Interplay
        "SNESMW",       # Michael Williams / Kemco
    ]

    midi_path = None
    used_binary = None

    # SPC2MID binaries live in model/domains/music/tools/spc2mid/
    _helix_spc2mid = Path(__file__).parents[1] / "tools" / "spc2mid"

    # SPC2MID writes {stem}_1.mid next to the input file — copy SPC to a
    # temp directory so we can find the output without polluting the source.
    import os as _os
    tmp_dir = Path(tempfile.mkdtemp())
    spc_copy = tmp_dir / path.name
    import shutil as _shutil_copy
    _shutil_copy.copy2(str(path), str(spc_copy))

    try:
        for binary in spc2mid_binaries:
            bin_path = shutil.which(binary) or shutil.which(binary + ".exe")
            if not bin_path:
                candidate = _helix_spc2mid / (binary + ".exe")
                if candidate.exists():
                    bin_path = str(candidate)

            if bin_path:
                try:
                    subprocess.run(
                        [bin_path, str(spc_copy)],
                        capture_output=True, timeout=30, cwd=str(tmp_dir)
                    )
                    # Output is written as {stem}_1.mid (or _2.mid, etc.)
                    midi_candidates = sorted(tmp_dir.glob(f"{spc_copy.stem}_*.mid"))
                    if midi_candidates and midi_candidates[0].stat().st_size > 128:
                        midi_path = midi_candidates[0]
                        used_binary = binary
                        break
                except Exception:
                    pass
    finally:
        # Clean temp dir after we're done (or on error)
        if not midi_path:
            _shutil_copy.rmtree(str(tmp_dir), ignore_errors=True)

    if midi_path:
        try:
            # Note events from SPC2MID MIDI (no hardware register log for SPC)
            try:
                import pretty_midi as _pm
                _midi_obj = _pm.PrettyMIDI(str(midi_path))
                # SPC2MID outputs each SPC voice as a separate MIDI track.
                # pretty_midi merges all tracks into instruments ordered by
                # first appearance; we use instrument index (0-7) as the
                # voice/channel identifier, matching SPC voice numbering.
                for _ch_idx, _inst in enumerate(_midi_obj.instruments):
                    for _n in _inst.notes:
                        analysis.note_events.append(NoteEvent(
                            time_s=_n.start,
                            channel=_ch_idx,
                            pitch_midi=_n.pitch,
                            pitch_hz=440.0 * 2 ** ((_n.pitch - 69) / 12),
                            velocity=_n.velocity / 127.0,
                        ))
            except Exception:
                pass

            # Tier B: symbolic analysis via music21
            sf, full = _run_symbolic_full(midi_path, f"spc2mid_{used_binary}", loop_point_s=None)
            if sf:
                analysis.symbolic = sf
                analysis.library_meta["symbolic_full"] = full
                analysis.library_meta["spc2mid_binary"] = used_binary
                analysis.analysis_tier = "B"
                analysis.confidence = 0.88
        finally:
            _shutil_copy.rmtree(str(tmp_dir), ignore_errors=True)

    return analysis



# ---------------------------------------------------------------------------
# NSF pipeline
# ---------------------------------------------------------------------------

def _analyze_nsf(path: Path) -> TrackAnalysis:
    from model.domains.music.parsing.nsf_parser import parse as nsf_parse

    nsf = nsf_parse(path)

    analysis = TrackAnalysis(
        file_path     = str(path),
        format        = "NSF",
        chips         = _nsf_chip_names(nsf),
        analysis_tier = "A",
        confidence    = 0.4,
        substrate     = _substrate_for_chip("NES_APU"),
    )

    _join_library_metadata(path, analysis)
    return analysis


def _nsf_chip_names(nsf) -> list[str]:
    chips = ["NES_APU"]
    flags = getattr(nsf, "extra_sound_chip", 0) if hasattr(nsf, "extra_sound_chip") else \
            (nsf.to_dict().get("extra_sound_chip", 0) if hasattr(nsf, "to_dict") else 0)
    if flags & 0x01: chips.append("VRC6")
    if flags & 0x02: chips.append("VRC7")
    if flags & 0x04: chips.append("FDS")
    if flags & 0x08: chips.append("MMC5")
    if flags & 0x10: chips.append("N163")
    if flags & 0x20: chips.append("Sunsoft5B")
    return chips


# ---------------------------------------------------------------------------
# S98 pipeline  (PC-88/PC-98 chip register log — same concept as VGM)
# ---------------------------------------------------------------------------

_S98_DEVICE_NAMES = {
    0x01: "ay_3_8910",
    0x02: "ym2203",
    0x03: "ym2612",
    0x04: "ym2608",
    0x05: "ym2151",
    0x06: "ym2413",
    0x07: "ym3526",
    0x08: "ymf262",
    0x09: "sn76489",
}


def _analyze_s98(path: Path) -> TrackAnalysis:
    """
    Parse S98 header to identify chips and clock rates.
    Full note reconstruction (event parsing) is deferred to a second pass —
    S98 event format differs from VGM but uses the same OPN/PSG chips.
    """
    import struct

    analysis = TrackAnalysis(
        file_path     = str(path),
        format        = "S98",
        analysis_tier = "A",
        confidence    = 0.5,
    )

    try:
        data = path.read_bytes()
        if len(data) < 4 or data[:3] != b"S98":
            analysis.error = "not a valid S98 file"
            _join_library_metadata(path, analysis)
            return analysis

        version = chr(data[3])

        chips: list[str] = []

        if version == "3" and len(data) >= 32:
            timer_num, timer_den, compress, ntag_off, loop_off, dev_count = struct.unpack_from("<iiiiii", data, 4)
            header_end = 28 + dev_count * 16
            if len(data) >= header_end:
                for i in range(dev_count):
                    offset = 28 + i * 16
                    dev_type, clock, pan, _reserved = struct.unpack_from("<iiii", data, offset)
                    name = _S98_DEVICE_NAMES.get(dev_type)
                    if name and clock > 0:
                        chips.append(name)

            # Estimate duration from file size vs event density (rough proxy)
            if timer_num > 0 and timer_den > 0:
                ticks_per_sec = timer_den / timer_num
                analysis.library_meta["s98_ticks_per_sec"] = ticks_per_sec
            analysis.has_loop = bool(loop_off)
        else:
            # v1/v2: no device list, assume YM2203 + PSG (most common PC-88 config)
            chips = ["ym2203", "ay_3_8910"]

        analysis.chips = chips
        if chips:
            analysis.substrate = _substrate_for_chip(chips[0])

        analysis.library_meta["s98_version"] = version

    except Exception as e:
        analysis.error = str(e)

    _join_library_metadata(path, analysis)
    return analysis


# ---------------------------------------------------------------------------
# SID pipeline
# ---------------------------------------------------------------------------

def _analyze_sid(path: Path) -> TrackAnalysis:
    from model.domains.music.parsing.sid_parser import parse as sid_parse

    sid = sid_parse(path)
    d   = sid.to_dict() if hasattr(sid, "to_dict") else {}

    analysis = TrackAnalysis(
        file_path     = str(path),
        format        = "SID",
        chips         = ["SID_6581" if d.get("sid_model") == "6581" else "SID_8580"],
        voice_count   = 3,
        analysis_tier = "A",
        confidence    = 0.5,
    )

    # Voice snapshots from SID register state
    for vi in range(3):
        vkey = f"voice{vi + 1}"
        if vkey in d:
            v = d[vkey]
            freq_hz = v.get("frequency_hz", 0.0)
            analysis.voices.append(ChipVoiceSnapshot(
                voice_index  = vi,
                active       = v.get("gate", False),
                pitch_raw    = v.get("frequency_raw", 0),
                pitch_hz     = freq_hz,
                pitch_midi   = _hz_to_midi(freq_hz),
                vol_l        = d.get("master_volume", 15) / 15.0,
                vol_r        = d.get("master_volume", 15) / 15.0,
                adsr_enabled = True,
                attack       = v.get("attack", 0),
                decay        = v.get("decay", 0),
                sustain      = v.get("sustain", 0),
                release      = v.get("release", 0),
                waveform     = v.get("waveform", ""),
            ))

    _join_library_metadata(path, analysis)

    # SID: waveform path (reSID render) — symbolic not supported yet
    wav = _run_waveform(path)
    if wav:
        analysis.waveform = wav
        analysis.analysis_tier = "AC"
        analysis.confidence = 0.65

    return analysis


# ---------------------------------------------------------------------------
# Waveform-only pipeline (MP3, Opus, FLAC, etc.)
# ---------------------------------------------------------------------------

def _analyze_waveform(path: Path) -> TrackAnalysis:
    analysis = TrackAnalysis(
        file_path     = str(path),
        format        = path.suffix.lstrip(".").upper(),
        analysis_tier = "C",
        confidence    = 0.4,
    )

    wf = _run_waveform(path)
    if wf:
        analysis.waveform = wf
        analysis.confidence = 0.55
    else:
        analysis.error = "waveform analysis failed (librosa could not decode file)"
        analysis.confidence = 0.0

    _join_library_metadata(path, analysis)
    return analysis


# ---------------------------------------------------------------------------
# Render-then-analyze pipeline (USF, PSF, mini*)
# ---------------------------------------------------------------------------

def _analyze_render(path: Path) -> TrackAnalysis:
    """
    Render via vgmstream to a temp WAV, then run waveform analysis.
    Waveform only — no chip data available.
    """
    import shutil, subprocess

    analysis = TrackAnalysis(
        file_path     = str(path),
        format        = path.suffix.lstrip(".").upper(),
        analysis_tier = "C",
        confidence    = 0.3,
    )

    import os
    _winget_base = os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"
    )
    _winget_vgm = None
    if os.path.isdir(_winget_base):
        for entry in os.listdir(_winget_base):
            if "vgmstream" in entry.lower():
                candidate = os.path.join(_winget_base, entry, "vgmstream-cli.exe")
                if os.path.isfile(candidate):
                    _winget_vgm = candidate
                    break

    vgmstream = (shutil.which("vgmstream-cli") or shutil.which("vgmstream_cli")
                 or _winget_vgm)
    if not vgmstream:
        analysis.error = "vgmstream-cli not found; cannot render"
        _join_library_metadata(path, analysis)
        return analysis

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        wav_path = Path(tf.name)

    try:
        subprocess.run(
            [vgmstream, "-o", str(wav_path), str(path)],
            capture_output=True, timeout=60
        )
        if wav_path.exists() and wav_path.stat().st_size > 1024:
            wf = _run_waveform(wav_path)
            if wf:
                analysis.waveform = wf
                analysis.confidence = 0.4
    except Exception as e:
        analysis.error = str(e)
    finally:
        try:
            wav_path.unlink()
        except Exception:
            pass

    _join_library_metadata(path, analysis)
    return analysis


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze(file_path: str | Path) -> TrackAnalysis:
    """
    Analyze a music file. Returns a schema-consistent TrackAnalysis.
    Dispatches to the appropriate tier based on file extension.

    Call this — NOT the individual tier functions.
    """
    path = Path(file_path)
    if not path.exists():
        return TrackAnalysis.error_record(path, f"File not found: {path}")

    ext = path.suffix.lower()

    try:
        if ext in (".vgm", ".vgz", ".gym"):
            return _analyze_vgm(path)
        elif ext == ".spc":
            return _analyze_spc(path)
        elif ext in (".nsf", ".nsfe"):
            return _analyze_nsf(path)
        elif ext in (".sid", ".psid", ".rsid"):
            return _analyze_sid(path)
        elif ext == ".s98":
            return _analyze_s98(path)    # PC-88/98 chip register log
        elif ext in (".ay", ".gbs", ".hes", ".sgc"):
            return _analyze_render(path)  # GME-family: render via emulator
        elif ext in (".mp3", ".opus", ".flac", ".ogg", ".wav", ".m4a", ".aac", ".wma"):
            return _analyze_waveform(path)
        elif ext in (".usf", ".miniusf", ".psf", ".psf2", ".minipsf",
                     ".2sf", ".mini2sf", ".ncsf", ".minincsf",
                     ".gsf", ".minigsf", ".ssf", ".dsf"):
            return _analyze_render(path)
        else:
            # Unknown: try waveform fallback
            return _analyze_waveform(path)

    except Exception as e:
        return TrackAnalysis.error_record(path, str(e))


def analyze_batch(
    paths: list[str | Path],
    progress: bool = True,
) -> list[TrackAnalysis]:
    """Analyze a list of files. Returns results in the same order."""
    results = []
    total = len(paths)
    for i, p in enumerate(paths):
        if progress:
            print(f"[{i+1}/{total}] {Path(p).name}", flush=True)
        results.append(analyze(p))
    return results

