import sys
import os
try:
    import readline
except ImportError:
    # Windows fallback
    try:
        from pyreadline import Readline
        readline = Readline()
    except ImportError:
        readline = None

from core.cli.command_runner import CommandRunner
from core.cli.path_utils import normalize_path
from core.cli.completion import HILCompleter

class HelixREPL:
    """
    Helix Research Console (REPL).
    Features: History, Tab-completion, ANSI Colors.
    """
    
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner
        self.history_file = os.path.expanduser("~/.helix_history")
        self.completer = HILCompleter()
        self._setup_readline()

    def _setup_readline(self):
        if not readline:
            return
        
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        
        readline.set_completer(self.completer.complete)
        readline.set_completer_delims(' \t\n=')
        readline.parse_and_bind("tab: complete")

    def run(self):
        """Main REPL loop."""
        RESET = "\033[0m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        
        print(f"{BOLD}{CYAN}HELIX Research Console{RESET}")
        print("Type 'exit' to quit.\n")

        while True:
            try:
                raw_input = input("helix> ").strip()
                if not raw_input:
                    continue
                if raw_input.lower() in ["exit", "quit"]:
                    break
                
                # Execute
                result = self.runner.run(raw_input)
                self.runner.print_result(result, is_interactive=True)
                
            except (KeyboardInterrupt, EOFError):
                print("\nInterrupted.")
                break
            except Exception as e:
                print(f"REPL Error: {e}", file=sys.stderr)

        if readline:
            readline.write_history_file(self.history_file)
        print("\nGoodbye.")
