"""
spanish_tool.py — Spanish learning utility (stub).

Wraps domains/language/model/ and Spanish construction grammar fixtures.
The underlying runtime and fixtures are available:
  - domains/language/model/pipeline.py
  - domains/language/model/research/grammar_resolution.py
  - domains/language/model/research/translation_alignment.py
  - domains/language/model/research/register_profile.py
  Fixtures: domains/language/model/data/datasets/spanish_construction_map.json

This tool surface has not yet been built. The language pipeline can be run directly:
  SUBSTRATE run name:language corpus:spanish_construction_map lang:spanish

Status: stub — see domains/language/model/tools/spanish/manifest.yaml for gaps.
"""

import sys


def main() -> None:
    print("[spanish] Spanish tool is not yet implemented.")
    print()
    print("The underlying domain runtime is available:")
    print("  # Via HSL:")
    print("  SUBSTRATE run name:language corpus:spanish_construction_map lang:spanish")
    print()
    print("  # Via domain research scripts:")
    print("  python domains/language/model/research/grammar_resolution.py")
    print("  python domains/language/model/research/translation_alignment.py")
    print("  python domains/language/model/research/register_profile.py")
    print()
    print("See domains/language/model/tools/spanish/manifest.yaml for implementation status.")
    sys.exit(0)


if __name__ == "__main__":
    main()

