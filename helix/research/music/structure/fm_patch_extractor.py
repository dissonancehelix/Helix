import pandas as pd
import numpy as np
from typing import Dict, Any

class YM2612Analytic:
    """
    Analyzes YM2612 register streams to reconstruct patches and channel roles.
    """
    def __init__(self, event_df: pd.DataFrame):
        self.df = event_df
        
    def extract_synthesis_parameters(self) -> pd.DataFrame:
        """
        Derives high-level synthesis parameters from the register stream.
        Maps the 4 operators of the YM2612.
        """
        # Registers of interest:
        # 30-3F (DT/ML), 40-4F (TL), 50-5F (AR/RS), 60-6F (DR/AM), 70-7F (SR), 80-8F (RR/SL), 90-9F (SSG-EG)
        # B0 (Algo/FB), B4 (L/R/AMS/FMS)
        
        relevant_regs = self.df[self.df['reg'].notnull()]
        # 0x28 is Note On. 0x30-0x9F are Operator params. 0xA0-0xB6 are Channel params.
        # We need 0x28 to know WHEN a patch is triggered.
        relevant_regs = relevant_regs[(relevant_regs['reg'] == 0x28) | (relevant_regs['reg'].between(0x30, 0xBF))]
        
        # State tracking for patches
        # YM2612 has 6 channels (P1: 0,1,2; P2: 3,4,5)
        channel_states = {i: {} for i in range(6)}
        patch_signatures = []

        for _, row in relevant_regs.iterrows():
            reg = int(row['reg'])
            val = int(row['val'])
            part_offset = 0 if row['type'] == 'YM2612_P1' else 3
            
            # Map register to channel (0-2) within part
            ch_idx = -1
            if 0x30 <= reg <= 0x9F:
                ch_idx = (reg & 0x03) + part_offset
                if ch_idx < 6:
                    channel_states[ch_idx][reg & 0xFC] = val # Store by base register (operator group)
            elif 0xA0 <= reg <= 0xB6:
                ch_idx = (reg & 0x03) + part_offset
                if ch_idx < 6:
                    channel_states[ch_idx][reg] = val

            # When a Note On occurs (Reg 0x28), we capture the current patch state
            # Register 0x28 is always Part 1
            if reg == 0x28:
                channel = val & 0x07
                if channel in [0,1,2, 4,5,6]: # 0,1,2 and 4,5,6 are valid indices
                    mapped_ch = channel if channel < 3 else (channel - 1)
                    if mapped_ch < 6:
                        # Capture current state as a 'Patch'
                        state = channel_states[mapped_ch].copy()
                        if state:
                            state['ch'] = mapped_ch
                            state['ts'] = row['ts']
                            patch_signatures.append(state)

        return pd.DataFrame(patch_signatures)

    def channel_density(self) -> Dict[str, float]:
        """
        Activity and Role analysis.
        """
        counts = self.df['type'].value_counts().to_dict()
        total = sum(counts.values())
        
        # Estimate roles based on event frequency and register types
        # Ch 1 typically used for Bass in certain styles
        return {k: v/total for k, v in counts.items()}

def analyze_track_synthesis(event_path: str, output_path: str):
    df = pd.read_parquet(event_path)
    analytic = YM2612Analytic(df)
    patch_df = analytic.extract_patch_stats()
    patch_df.to_parquet(output_path)
    return len(patch_df)
