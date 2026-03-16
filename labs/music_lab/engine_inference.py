import pandas as pd
import numpy as np
from typing import Dict, Any, List

class EngineInferenceEngine:
    """
    Infers the sound engine (SMPS, GEMS, etc.) used in a VGM track.
    """
    
    def __init__(self, event_stream: List[Dict[str, Any]]):
        self.events = event_stream
        self.df = pd.DataFrame(event_stream)
        
    def infer(self) -> Dict[str, Any]:
        scores = {
            "SMPS": 0,
            "GEMS": 0,
            "Custom": 0
        }
        
        evidence = []
        
        if self.df.empty:
            return {"engine": "Unknown", "confidence": 0, "evidence": []}

        # 1. Check for SMPS "Opcode" patterns in YM2612 writes
        # SMPS often writes to 0x28 (Note On) with specific channel masks
        note_ons = self.df[self.df['reg'] == 0x28]
        if not note_ons.empty:
            # SMPS usually uses channel bits 0-2 (0x00-0x02 for P1, 0x04-0x06 for P2)
            # and a 'Note On' nibble 0xF0 or similar
            smps_note_ons = note_ons[note_ons['val'].isin([0x00, 0x01, 0x02, 0x04, 0x05, 0x06, 0xF0, 0xF1, 0xF2, 0xF4, 0xF5, 0xF6])]
            if len(smps_note_ons) / len(note_ons) > 0.8:
                scores["SMPS"] += 10
                evidence.append("Consistent SMPS-style 0x28 Note On values")

        # 2. Check for GEMS DAC behavior
        # GEMS samples are often 8-bit, 10.4kHz or similar
        # In VGM, PCM writes are often cmd 0x80..0x8F (Wait + write to 0x2A)
        pcm_writes = self.events # Need to check raw commands if possible, or just YM2612 reg 0x2A
        reg_2a = self.df[self.df['reg'] == 0x2A]
        if not reg_2a.empty:
            # Check timing intervals for reg 0x2A writes
            intervals = reg_2a['ts'].diff().dropna()
            if not intervals.empty:
                avg_int = intervals.median()
                # 44100 / 10400 = ~4.24. VGM samples are 44100Hz.
                # 44100 / 4000 = ~11.
                if 4.0 <= avg_int <= 4.5:
                    scores["GEMS"] += 15
                    evidence.append("Detected GEMS-typical 10.4kHz PCM playback frequency")
                elif 5.5 <= avg_int <= 6.5: # ~7kHz
                    scores["GEMS"] += 5
                    evidence.append("Detected Western-style low-sample-rate PCM")

        # 3. SMPS Modulation/Pitch Patterns
        # SMPS often does 'Software LFO' by writing to frequency registers (0xA0-0xA6) frequently
        freq_writes = self.df[self.df['reg'].between(0xA0, 0xA6)]
        if not freq_writes.empty:
            write_density = len(freq_writes) / (self.events[-1]['ts'] / 44100) if self.events else 0
            if write_density > 50: # High frequency updates
                scores["SMPS"] += 5
                evidence.append("High-density frequency modulation detected (SMPS signature)")

        # 4. Patch update sequence
        # SMPS: Patch update -> Note On
        # Let's check for clusters of register writes before 0x28
        # (Simplified check: are 0x30-0xAF writes common before 0x28?)
        
        # 5. GEMS Voice Allocation
        # GEMS cycles through channels more aggressively than SMPS
        if not note_ons.empty:
            channels_used = note_ons['val'] & 0x07
            diversity = len(channels_used.unique())
            if diversity == 6:
                scores["GEMS"] += 5
                evidence.append("Full 6-channel FM cycling detected (GEMS allocation behavior)")

        # Final decision
        max_score = max(scores.values())
        if max_score < 5:
            winning_engine = "Other"
        else:
            winning_engine = [k for k, v in scores.items() if v == max_score][0]

        return {
            "engine": winning_engine,
            "confidence": min(max_score / 30, 1.0),
            "evidence": evidence,
            "scores": scores
        }
