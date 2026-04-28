"""
test_action_layer.py — Verification for Phase 15.
"""
import sys
from pathlib import Path

# Add Helix root to path
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
sys.path.insert(0, str(HELIX_ROOT))

from system.tools.music_bridge.bridge import HelixBridge

def test_actions():
    print("--- Helix Action Layer Test ---")
    bridge = HelixBridge()
    
    # Force a mock context if stopped
    np = bridge.get_now_playing()
    if not np or not np.resolved:
        print("[!] No 'Now Playing' found. Forcing mock context...")
        # Get a real track from DB for consistent testing
        with bridge.db._conn() as conn:
            row = conn.execute("SELECT file_path FROM tracks LIMIT 1").fetchone()
            if row:
                mock_path = row[0]
                from system.tools.music_bridge.metadata_adapter import _path_to_uri
                mock_uri = _path_to_uri(mock_path)
                mock_track = bridge.resolve(mock_uri)
                if mock_track:
                    from model.domains.music.operator.context import NowPlayingContext, get_partition_from_path
                    mock_ctx = NowPlayingContext(track=mock_track, partition=get_partition_from_path(mock_path))
                    # Inject mock into operator for testing
                    bridge.operator.get_current_context = lambda source: mock_ctx
                    print(f"    Mock track: {mock_track.title}")
                else:
                    print(f"    [FAIL] Could not resolve mock track: {mock_uri}")

    print("\n1. Fetching Contextual Actions...")
    actions = bridge.get_actions(context="playing")
    print(f"Found {len(actions)} actions.")
    for a in actions:
        print(f" - [{a['category']}] {a['description']}")
        print(f"   Rationale: {a['rationale']}")

    if actions:
        action_id = actions[0]["id"]
        print(f"\n2. Staging Action: {action_id}")
        success = bridge.stage_action(action_id)
        print(f"Success: {success}")
        
        # Verify in DB
        staged = bridge.operator.staging.get_staged()
        print(f"Staged actions in DB: {len(staged)}")
        for s in staged:
            print(f" - {s['description']} (Staged at: {s['staged_ts']})")

    print("\n3. Session Summary (Flight Deck)...")
    summary = bridge.get_session_summary()
    import json
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    test_actions()

