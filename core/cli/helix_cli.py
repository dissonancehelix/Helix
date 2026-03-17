import sys
import argparse
from pathlib import Path

# Add project root to sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.cli.command_runner import CommandRunner
from core.cli.repl import HelixREPL

def run_script(path: str, runner: CommandRunner):
    """Execute a .hil script file."""
    p = Path(path)
    if not p.exists():
        print(f"Error: Script file not found: {path}", file=sys.stderr)
        sys.exit(1)
    
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Execution
            result = runner.run(line)
            runner.print_result(result)

def main():
    parser = argparse.ArgumentParser(description="Helix Interface Language (HIL) CLI")
    parser.add_argument("command", nargs="*", help="HIL command to execute")
    parser.add_argument("--script", "-s", help="Execute a .hil script file")
    
    args = parser.parse_args()
    runner = CommandRunner()

    # 1. Direct Script Execution (via flag)
    if args.script:
        run_script(args.script, runner)
        return

    # 2. Command Execution (positional args)
    if args.command:
        # Check if the first arg is "run" and the second is a .hil file
        if len(args.command) >= 2 and args.command[0].lower() == "run" and args.command[1].endswith(".hil"):
            run_script(args.command[1], runner)
        else:
            full_cmd = " ".join(args.command)
            result = runner.run(full_cmd)
            runner.print_result(result)
        return

    # 3. Interactive REPL
    if sys.stdin.isatty():
        repl = HelixREPL(runner)
        repl.run()
    else:
        # Piped input processing?
        for line in sys.stdin:
            line = line.strip()
            if line:
                result = runner.run(line)
                runner.print_result(result)

if __name__ == "__main__":
    main()
