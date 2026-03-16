import sys
from pathlib import Path

# Add REPO_ROOT to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.hil import dispatch
from core.kernel.dispatcher.router import Dispatcher

def main():
    if len(sys.argv) < 2:
        print("Usage: python hil_dispatch.py \"HIL COMMAND\"")
        sys.exit(1)

    raw_command = " ".join(sys.argv[1:])
    dispatcher = Dispatcher()
    
    print(f"[hil_dispatch] Executing: {raw_command}")
    try:
        result = dispatch(raw_command, dispatcher=dispatcher)
    except Exception as e:
        import traceback
        print(f"[hil_dispatch] CRITICAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    import json
    # Print the result summary
    print("\n--- HIL EXECUTION RESULT ---")
    if result.get("status") == "ok":
        print(f"Status: SUCCESS")
        print(f"Artifact: {result.get('artifact_dir')}")
        if result.get("validation"):
            print(f"Validation: {result['validation'].get('status')} ({result['validation'].get('confidence')})")
    else:
        print(f"Status: {result.get('status')}")
        print(f"Error: {result.get('message') or result.get('error')}")
    
    # Save the full result for verification in artifacts/
    log_dir = REPO_ROOT / "artifacts"
    log_dir.mkdir(exist_ok=True)
    with open(log_dir / "last_hil_run.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
