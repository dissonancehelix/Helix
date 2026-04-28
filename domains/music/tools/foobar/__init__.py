"""
foobar — Music library maintenance tool (v0).

Provides audit, sync, diff, repair-plan, and corpus integrity
for the operator's Foobar2000/VGM library.

Two-root model:
  library root  — C:\\Users\\dissonance\\Music (corpus, files)
  runtime root  — C:\\Users\\dissonance\\AppData\\Roaming\\foobar2000-v2 (metadb, config)

Usage:
    python -m applications.tools.foobar.runner --help
    python -m applications.tools.foobar.runner --health
    python -m applications.tools.foobar.runner --report
    python -m applications.tools.foobar.runner --corpus --franchise "Sonic the Hedgehog"
    python -m applications.tools.foobar.runner --query --platform "Mega Drive" --loved
"""

from .runner import main

__all__ = ["main"]
