import pandas as pd
import numpy as np
from typing import Dict, Any, List

class ChannelProfiler:
    """
    Models Genesis channel roles (FM1-6, PSG1-3, DAC).
    Computes statistics on usage patterns to determine musical roles.
    """
    
    def __init__(self, event_stream: List[Dict[str, Any]]):
        self.events = event_stream
        self.df = pd.DataFrame(event_stream)
        self.duration = self.df['ts'].max() if not self.df.empty else 1

    def profile(self) -> Dict[str, Any]:
        if self.df.empty:
            return {}

        profiles = {}
        
        # 1. DAC/PCM Activity (Channel 6 usually if used as DAC)
        dac_writes = self.df[self.df['reg'] == 0x2A]
        profiles['DAC'] = {
            "activity_ratio": len(dac_writes) / self.duration,
            "role": "Percussion/Voice" if len(dac_writes) > 500 else "None",
            "is_active": len(dac_writes) > 0
        }

        # 2. FM Channels 1-6
        for ch in range(1, 7):
            # Identifying writes for this channel
            # SMPS/GEMS mapping:
            # P1: 0x30..0xAF (Part 1) mapping to channels 1-3
            # P2: 0x30..0xAF (Part 2) mapping to channels 4-6
            part = "YM2612_P1" if ch <= 3 else "YM2612_P2"
            ch_idx = (ch - 1) % 3
            
            # Registers for specific channel are offset by ch_idx
            # e.g. 0x30 (CH1), 0x31 (CH2), 0x32 (CH3)
            # 0x40, 0x41, 0x42...
            # We filter registers: (reg & 0x03) == ch_idx but also avoiding system regs (0x20..0x2F)
            ch_writes = self.df[(self.df['type'] == part) & 
                                (self.df['reg'] >= 0x30) & 
                                (self.df['reg'] <= 0xAF) & 
                                ((self.df['reg'] & 0x03) == ch_idx)]
            
            # Note On events for this channel
            p_val = ch - 1 if ch <= 3 else ch # SMPS standard 0,1,2, x, 4,5,6
            note_ons = self.df[(self.df['reg'] == 0x28) & ((self.df['val'] & 0x07) == (ch-1 if ch <=3 else ch))]

            # Role Heuristics
            role = self._infer_role(ch_writes, note_ons)
            
            profiles[f"FM{ch}"] = {
                "activity_ratio": len(ch_writes) / self.duration,
                "note_count": len(note_ons),
                "role": role,
                "is_active": len(ch_writes) > 0 or len(note_ons) > 0
            }

        # 3. PSG Channels 1-3
        # PSG is one sequential stream of data
        # Bit 7=1: Address, bits 6-5: Channel, bit 4: Type (Freq/Atten)
        psg_writes = self.df[self.df['type'] == "PSG"]
        for ch in range(1, 4):
            # Very simplified PSG filter (last addressed channel)
            # Real parsing would track state, here we just look for signature bit patterns
            # Note: This is a rough estimation
            ch_tag = (ch-1) << 5
            psg_ch_writes = psg_writes[psg_writes['val'] & 0x60 == ch_tag]
            
            profiles[f"PSG{ch}"] = {
                "activity_ratio": len(psg_ch_writes) / self.duration,
                "role": "Percussion" if ch == 3 else "Melody/Harmony",
                "is_active": len(psg_ch_writes) > 0
            }

        return profiles

    def _infer_role(self, writes, notes) -> str:
        if notes.empty: return "Silence"
        
        # Check algorithm (0xB0..0xB2)
        # Low algorithms (0, 1, 2) are often bass-y (4 operators in series)
        # Note: We'd need to track the last written algo value
        
        # For now, use simple density
        if len(notes) > 500: return "Fast Melody/Arp"
        if len(notes) < 50: return "Atmospheric/SFX"
        
        return "Melody/Accompaniment"
