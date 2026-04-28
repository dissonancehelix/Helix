"""
core/operators/base.py — Helix Base Operator
=============================================
Defines the functional base class for all Helix operators.
Follows the execute() -> validate() -> Adapter().execute() pattern.
"""
from __future__ import annotations

from typing import Any
from abc import ABC, abstractmethod

from core.engine.operators.operator_spec import OperatorSpec

class BaseOperator(ABC):
    """
    Functional base class for Helix operators.
    Each operator must define its Spec and implement execute().
    """
    name: str = ""
    substrate: str = ""
    
    @classmethod
    def get_spec(cls) -> OperatorSpec:
        """Return the OperatorSpec for this operator."""
        # This will be overridden or implemented by pulling from builtin_operators
        from core.engine.operators.operator_registry import get_registry
        return get_registry().require(cls.name)

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the operator pipeline.
        
        Args:
            payload: Input dictionary containing parameters and entity references.
            
        Returns:
            Result dictionary following the operator's output schema.
        """
        pass

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Standard validation logic for operator inputs.
        Can be overridden for custom validation.
        """
        return payload
