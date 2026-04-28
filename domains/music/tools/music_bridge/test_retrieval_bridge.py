"""
test_retrieval_bridge.py — Operator-Centric Retrieval Diagnostics

Tests for the Helix Music Bridge aligned with the operator's actual foobar setup:
- Differentiated contexts (Now-Playing vs Selection vs Playlist)
- Partition-aware retrieval (VGM vs all-library)
- Composer semantics (Artist override logic)
- Identity alignment diagnostics (Art-panel risk)
"""
from pathlib import Path
import sys

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
sys.path.insert(0, str(HELIX_ROOT))

from domains.music.tools.music_bridge.bridge import HelixBridge

def test():
    print("=== Helix Music: Operator-Centric Retrieval Test ===")
    bridge = HelixBridge()
    
    # 1. Status with Phase 13 Metrics
    status = bridge.status()
    print("\n[ 1. Bridge Status ]")
    print(status.describe())
    
    # 2. Alignment Diagnostics (Playing vs Browsed)
    print("\n[ 2. Identity Alignment (Playing vs Browsed) ]")
    diag = bridge.diagnose()
    print(f"Status: {diag['status']}")
    if diag['mismatch_warning']:
        print(f"!! Warning: {diag['mismatch_warning']}")
    
    if diag['now_playing']['resolved']:
        print(f"  Now Playing: {diag['now_playing']['album']} ({diag['now_playing']['id']})")
    if diag['selection']['resolved']:
        print(f"  Selection:   {diag['selection']['album']} ({diag['selection']['id']})")
        
    # 3. Context-Aware Explanations
    print("\n[ 3. Contextual Explanations ]")
    np_exp = bridge.explain(context="playing")
    if np_exp:
        print(f"  Playing Track: {np_exp['summary']}")
        print(f"  Explanation:   {np_exp['explanation']}")
    
    sel_exp = bridge.explain(context="selection")
    if sel_exp:
        print(f"  Selected Track: {sel_exp['summary']}")
        print(f"  Explanation:    {sel_exp['explanation']}")
    else:
        print("  Selection: No track currently selected in browse playlist.")

    # 4. Partition-Aware Retrieval
    print("\n[ 4. Partition-Aware Retrieval (VGM Focus) ]")
    # All library neighbors
    print("  Neighbors (All Library):")
    neighbors_all = bridge.nearest(limit=3, context="playing")
    for i, n in enumerate(neighbors_all):
        print(f"    {i+1}. {n['meta'].get('title')} [{n['id']}]")
        
    # VGM-only neighbors
    print("  Neighbors (VGM Partition Only):")
    neighbors_vgm = bridge.nearest(limit=3, partition="VGM", context="playing")
    for i, n in enumerate(neighbors_vgm):
        print(f"    {i+1}. {n['meta'].get('title')} [{n['id']}]")

    # 5. Canon Extraction
    print("\n[ 5. Canon Contexts ]")
    # Canon for current playing track's primary tag
    print("  Canon for Now-Playing structural role:")
    canon_np = bridge.canon(context="playing", limit=3)
    for i, c in enumerate(canon_np):
        print(f"    {i+1}. {c.get('title')} by {c.get('artist')}")

    # Canon for current selection's primary tag
    print("  Canon for Selected structural role:")
    canon_sel = bridge.canon(context="selection", limit=3)
    if canon_sel:
        for i, c in enumerate(canon_sel):
            print(f"    {i+1}. {c.get('title')} by {c.get('artist')}")
    else:
        print("    No selection to derive canon from.")

if __name__ == "__main__":
    test()

