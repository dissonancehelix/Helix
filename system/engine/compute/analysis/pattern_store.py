import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

class PatternStore:
    """
    Manages the storage and retrieval of discovered invariants in Atlas.
    All writes go through codex/atlas/invariants/.
    """
    
    INVARIANTS_DIR = ROOT / "codex" / "atlas" / "invariants"

    @classmethod
    def save_invariant(cls, name: str, data: dict):
        if not cls.INVARIANTS_DIR.exists():
            cls.INVARIANTS_DIR.mkdir(parents=True, exist_ok=True)
            
        file_path = cls.INVARIANTS_DIR / f"{name}.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"[pattern_store] Registered invariant: {name}")

    @classmethod
    def list_invariants(cls):
        if not cls.INVARIANTS_DIR.exists():
            return []
        return [f.stem for f in cls.INVARIANTS_DIR.glob("*.json")]

    @classmethod
    def load_invariant(cls, name: str):
        file_path = cls.INVARIANTS_DIR / f"{name}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r") as f:
            return json.load(f)
