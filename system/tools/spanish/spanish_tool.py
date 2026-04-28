"""
spanish_tool.py — Spanish learning utility (stub).

Wraps model/domains/language/ and Spanish construction grammar fixtures.
The underlying runtime and fixtures are available:
  - model/domains/language/pipeline.py
  - model/domains/language/research/grammar_resolution.py
  - model/domains/language/research/translation_alignment.py
  - model/domains/language/research/register_profile.py
  Fixtures: model/domains/language/data/datasets/spanish_construction_map.json

This tool surface has not yet been built. The language pipeline can be run directly:
  SUBSTRATE run name:language corpus:spanish_construction_map lang:spanish

Status: stub — see model/domains/language/tools/spanish/manifest.yaml for gaps.
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
    print("  python model/domains/language/research/grammar_resolution.py")
    print("  python model/domains/language/research/translation_alignment.py")
    print("  python model/domains/language/research/register_profile.py")
    print()
    print("See model/domains/language/tools/spanish/manifest.yaml for implementation status.")
    sys.exit(0)


if __name__ == "__main__":
    main()

