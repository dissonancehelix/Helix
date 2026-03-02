import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class GovernanceException(Exception):
    pass

def load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)

def enforce_schema_version(current_schema_hash: str, prior_schema_hash: str, 
                           current_manifest_version: str, prior_manifest_version: str):
    """Schema modification requires manifest version bump."""
    if current_schema_hash != prior_schema_hash:
        if current_manifest_version == prior_manifest_version:
            raise GovernanceException(
                "GOVERNANCE VIOLATION: Schema modified without manifest version bump."
            )

def enforce_enum_test_coverage(enum_files_modified: bool, tests_modified: bool):
    """Enum modification requires test suite update."""
    if enum_files_modified and not tests_modified:
        raise GovernanceException(
            "GOVERNANCE VIOLATION: Enum modified without corresponding test suite update."
        )

def enforce_collapse_class_falsifier(collapse_classes_added: set, falsifier_updated: bool):
    """Collapse class addition requires falsifier update."""
    if collapse_classes_added and not falsifier_updated:
        raise GovernanceException(
            f"GOVERNANCE VIOLATION: Added collapse classes {collapse_classes_added} without updating falsifiers."
        )

def enforce_obstruction_entropy(obstruction_primitives_added: set, entropy_reduced: bool):
    """New obstruction primitive requires entropy test."""
    if obstruction_primitives_added and not entropy_reduced:
        raise GovernanceException(
            f"GOVERNANCE VIOLATION: Added obstructions {obstruction_primitives_added} but did not demonstrate entropy reduction."
        )

def run_governance_checks(context: dict):
    """Runs all structural governance checks based on a provided state differential context."""
    enforce_schema_version(
        context.get("current_schema_hash"),
        context.get("prior_schema_hash"),
        context.get("current_manifest_version"),
        context.get("prior_manifest_version")
    )
    enforce_enum_test_coverage(
        context.get("enum_files_modified", False),
        context.get("tests_modified", False)
    )
    enforce_collapse_class_falsifier(
        context.get("collapse_classes_added", set()),
        context.get("falsifier_updated", False)
    )
    enforce_obstruction_entropy(
        context.get("obstruction_primitives_added", set()),
        context.get("entropy_reduced", False)
    )
    return True
