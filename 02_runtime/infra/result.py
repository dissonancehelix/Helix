from typing import Any, Optional

class Result:
    def __init__(self, ok: bool, value: Any, error: Optional[str] = None):
        self.ok = ok
        self.value = value
        self.error = error

    @classmethod
    def is_ok(cls, value: Any):
        return cls(True, value)

    @classmethod
    def is_error(cls, error: str):
        return cls(False, None, error)
