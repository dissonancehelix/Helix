from typing import List
from core.hil.command_registry import list_verbs, get_spec
from core.hil.ontology import OBJECT_TYPES

class HILCompleter:
    """Tab completion engine for HIL verbs, subcommands, and types."""
    
    def __init__(self):
        self.verbs = list_verbs()
        self.types = list(OBJECT_TYPES.keys())

    def complete(self, text: str, state: int) -> str | None:
        """Readline completer function."""
        import readline
        buffer = readline.get_line_buffer()
        tokens = buffer.split()
        
        # Determine what we are completing
        # 1. Verb completion
        if not tokens or (len(tokens) == 1 and not buffer.endswith(' ')):
            options = [v for v in self.verbs if v.startswith(text.upper())]
        
        # 2. Subcommand completion
        elif len(tokens) == 1 or (len(tokens) == 2 and not buffer.endswith(' ')):
            verb = tokens[0].upper()
            spec = get_spec(verb)
            if spec and spec.subcommands:
                options = [s.lower() for s in spec.subcommands if s.lower().startswith(text.lower())]
            else:
                options = []
        
        # 3. Type/Param completion (basic)
        else:
            options = [t for t in self.types if t.startswith(text.lower())]
            # Add some common params
            options += [p for p in ["engine:", "namespace:", "limit:", "offset:"] if p.startswith(text.lower())]

        if state < len(options):
            return options[state]
        return None
