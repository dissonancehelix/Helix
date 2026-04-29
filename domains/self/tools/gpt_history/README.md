# GPT History Tools

Local-only tools for analyzing ChatGPT export evidence as self-domain derived artifacts.

## Pass 1

`pass_01_interaction_fingerprint.py` parses restored ChatGPT export files from the substantial chat archive, writes a normalized local message index, and produces compact marker reports for interaction style, request types, domain mentions, correction moments, and candidate profile sharpenings.

Raw exports remain in `archive/chat_exports/`. The message index is derived evidence, not canon, and should not be treated as a replacement for the raw export.
