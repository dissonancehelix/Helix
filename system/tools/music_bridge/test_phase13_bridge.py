"""
test_phase13_bridge.py — Phase 13: Verify Taste-Space retrieval in the bridge.
"""
from pathlib import Path
import sys

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
sys.path.insert(0, str(HELIX_ROOT))

from system.tools.music_bridge.bridge import HelixBridge

def test():
    print("=== Helix Music Bridge Phase 13 Test ===")
    bridge = HelixBridge()
    
    # 1. Check Status
    status = bridge.status()
    print("\n[ Bridge Status ]")
    print(status.describe())
    
    # 2. Try Explanation (Requires foobar to be playing a known track)
    print("\n[ Current Track Explanation ]")
    explanation = bridge.explain()
    if explanation:
        print(f"Track: {explanation['summary']}")
        print(f"Helix ID: {explanation['track_id']}")
        print(f"Explanation: {explanation['explanation']}")
        print(f"Shared Traits: {', '.join(explanation['traits'])}")
    else:
        print("No live track found or foobar offline.")
        
    # 3. Try Nearest Neighbors
    print("\n[ Neighbor Analysis ]")
    neighbors = bridge.nearest(limit=5)
    if neighbors:
        for i, n in enumerate(neighbors):
            m = n['meta']
            print(f"  {i+1}. {m.get('title')} ({m.get('artist')}) [w={n['weight']:.2f}]")
    else:
        print("No neighbors found for current track.")

    # 4. Try Canon Extraction
    print("\n[ Canon Extraction: 'crooked_coherence' ]")
    try:
        canon_results = bridge.canon("crooked_coherence", limit=3)
        if canon_results:
            for i, c in enumerate(canon_results):
                print(f"  {i+1}. {c.get('title')} ({c.get('artist')})")
        else:
            print("No canon found for tag.")
    except Exception as e:
         print(f"Error extracting canon: {e}")

if __name__ == "__main__":
    test()

