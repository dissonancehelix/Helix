import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SMPSReconstructor:
    """
    Infers higher-level SMPS-style commands from a VGM event stream.
    Focuses on detecting patterns, loops, and rhythmic structure.
    """
    
    def __init__(self, event_stream: List[Dict[str, Any]]):
        self.events = event_stream
        self.df = pd.DataFrame(event_stream)

    def extract_structure(self) -> Dict[str, Any]:
        """
        Detects loops and repeated patterns.
        """
        if self.df.empty:
            return {}

        results = {
            "inferred_commands": [],
            "patterns": [],
            "stats": {}
        }

        # 1. Note Stream per Channel
        # Channels 1-3 (P1), 4-6 (P2)
        channel_notes = {}
        for ch in range(6):
            # SMPS uses specific mapping for Note On (reg 0x28)
            # Channel mapping: 0, 1, 2 (P1), 4, 5, 6 (P2)
            reg_val = ch if ch < 3 else ch + 1
            ch_events = self.df[self.df['reg'] == 0x28]
            ch_notes = ch_events[ch_events['val'] & 0x07 == reg_val]
            
            if not ch_notes.empty:
                # Group by timestamp and check for rhythm
                intervals = ch_notes['ts'].diff().dropna()
                channel_notes[ch] = {
                    "count": len(ch_notes),
                    "avg_interval": intervals.mean(),
                    "rhythm_entropy": self._calc_entropy(intervals)
                }

        results['stats']['channel_notes'] = channel_notes

        # 2. Pattern Detection (Hash-based)
        # We look for identical sequences of register writes
        patterns = self._detect_repeated_sequences()
        results['patterns'] = patterns

        return results

    def _calc_entropy(self, data: pd.Series) -> float:
        if data.empty: return 0.0
        counts = data.value_counts()
        probs = counts / len(data)
        return -np.sum(probs * np.log2(probs))

    def _detect_repeated_sequences(self, min_len=4, max_len=32) -> List[Dict[str, Any]]:
        """
        Detects repeating sequences of (reg, val) pairs.
        """
        # Linearize FM writes (ignoring timing for pattern matching)
        fm_writes = self.df[self.df['type'].str.contains('YM2612')]
        if len(fm_writes) < 100:
            return []
            
        sequence = list(zip(fm_writes['reg'], fm_writes['val']))
        
        # Simple sliding window hash to find repetitions
        found_patterns = []
        hashes = {}
        
        for length in [8, 16, 24, 32]:
            for i in range(0, len(sequence) - length, 4):
                chunk = tuple(sequence[i:i+length])
                h = hash(chunk)
                if h in hashes:
                    hashes[h]['count'] += 1
                    hashes[h]['positions'].append(i)
                else:
                    hashes[h] = {'chunk': chunk, 'count': 1, 'positions': [i], 'len': length}
        
        # Filter for recurring patterns
        for h, info in hashes.items():
            if info['count'] > 2:
                found_patterns.append({
                    "length": info['len'],
                    "count": info['count'],
                    "first_pos": info['positions'][0]
                })
                
        return sorted(found_patterns, key=lambda x: x['count'], reverse=True)[:10]
