from __future__ import annotations
import sys
import json
from typing import Any, Dict
from core.hil.interpreter import run_command
from core.hil.context import CommandContext

class CommandRunner:
    """
    Executes HIL commands and formats output for the CLI.
    Supports pretty-printing and JSON output for piping.
    """
    
    def __init__(self, context: CommandContext | None = None) -> None:
        self.context = context or CommandContext.default()

    def run(self, raw_command: str) -> Dict[str, Any]:
        """Execute a HIL command and return the result dict."""
        return run_command(raw_command, self.context)

    def print_result(self, result: Dict[str, Any], is_interactive: bool = False) -> None:
        """Format and print result to stdout."""
        from core.cli.path_utils import normalize_path
        
        status = result.get("status", "error")
        data = result.get("data")
        
        # Recursive path normalization in data
        def _norm_data(obj):
            if isinstance(obj, dict):
                return {k: _norm_data(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_norm_data(x) for x in obj]
            elif isinstance(obj, str) and (":\\" in obj or (obj.startswith("/") and "/" in obj[2:])):
                 # Heuristic for Windows paths (C:\ or /c/)
                 return normalize_path(obj)
            return obj

        if data:
            data = _norm_data(data)

        # If piping, output raw JSON or data
        if not sys.stdout.isatty():
            if status == "ok":
                print(json.dumps(data if data is not None else {}, indent=2))
            else:
                print(json.dumps(result, indent=2), file=sys.stderr)
            return

        # Interactive / Human-readable output with ANSI colors
        RESET = "\033[0m"
        BLUE = "\033[94m"
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"

        if status == "ok":
            print(f"{GREEN}OK{RESET} — {result.get('command')}")
            if data:
                print(json.dumps(data, indent=2))
        elif status == "not_found":
            print(f"{YELLOW}NOT FOUND{RESET} — {result.get('error')}")
        else:
            print(f"{RED}ERROR{RESET} — {result.get('error')}", file=sys.stderr)
