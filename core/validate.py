#!/usr/bin/env python3
"""Helix KB validator. Usage: python core/validate.py"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema is required. Run: pip install jsonschema")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
KB_DIR = ROOT / "kb"
SCHEMA_PATH = Path(__file__).parent / "schema.json"


def load_schema():
    with SCHEMA_PATH.open() as f:
        return json.load(f)


def load_kb_files():
    """Return {filename: parsed_object} for every .json file in kb/."""
    objects = {}
    parse_errors = []

    for path in sorted(KB_DIR.glob("*.json")):
        try:
            with path.open(encoding="utf-8") as f:
                objects[path.name] = json.load(f)
        except UnicodeDecodeError:
            parse_errors.append(f"{path.name}: file is not UTF-8 encoded")
        except json.JSONDecodeError as e:
            parse_errors.append(f"{path.name}: invalid JSON — {e}")

    return objects, parse_errors


def validate_objects(objects, schema):
    """Validate each object against the schema. Return list of error strings."""
    validator = jsonschema.Draft7Validator(schema)
    errors = []

    for filename, obj in objects.items():
        for error in sorted(validator.iter_errors(obj), key=str):
            path = " > ".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"{filename}: [{path}] {error.message}")

    return errors


def validate_references(objects):
    """Check that every reference points to a known id. Return list of error strings."""
    known_ids = {obj["id"] for obj in objects.values() if isinstance(obj.get("id"), str)}
    errors = []

    for filename, obj in objects.items():
        refs = obj.get("references", [])
        if not isinstance(refs, list):
            continue
        for ref in refs:
            if isinstance(ref, str) and ref not in known_ids:
                errors.append(f"{filename}: reference '{ref}' does not match any known id in kb/")

    return errors


def main():
    if not KB_DIR.exists():
        print(f"ERROR: kb/ directory not found at {KB_DIR}")
        sys.exit(1)

    schema = load_schema()
    objects, parse_errors = load_kb_files()

    all_errors = []
    all_errors.extend(parse_errors)
    all_errors.extend(validate_objects(objects, schema))
    all_errors.extend(validate_references(objects))

    if not objects and not parse_errors:
        print("kb/ is empty — nothing to validate.")
        sys.exit(0)

    if all_errors:
        print(f"VALIDATION FAILED — {len(all_errors)} error(s):\n")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)

    print(f"OK — {len(objects)} object(s) validated successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
