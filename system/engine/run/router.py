import sys
import os
from pathlib import Path

# Add repo root to path
ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

def print_help():
    print("Usage: ./helix <command> [options]")
    print("\nCommands:")
    print("  run [--domain <name>]    Run falsifier probes against Atlas memory")
    print("  verify                   Validate the workspace structure and boundaries")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print_help()

    cmd = sys.argv[1]
    
    if cmd == "run":
        from system.engine.run.falsifier_runner import run_falsifiers
        
        domain = None
        quiet = False
        
        args = sys.argv[2:]
        if "--domain" in args:
            idx = args.index("--domain")
            if idx + 1 < len(args):
                domain = args[idx + 1]
        if "--quiet" in args:
            quiet = True
            
        if domain:
            # Monkeypatch discover_probes
            from system.engine.run import falsifier_runner
            orig_discover = falsifier_runner.discover_probes
            def discover_domain():
                return [p for p in orig_discover() if p["domain"] == domain]
            falsifier_runner.discover_probes = discover_domain
            
        run_falsifiers(verbose=not quiet)
        
    elif cmd == "verify":
        script_path = ROOT / "helix" / "engine" / "agent_harness" / "check_workspace.py"
        os.execv(sys.executable, [sys.executable, str(script_path)] + sys.argv[2:])
        
    else:
        print(f"Unknown command: {cmd}\n")
        print_help()

if __name__ == "__main__":
    main()

