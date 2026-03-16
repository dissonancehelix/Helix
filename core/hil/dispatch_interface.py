"""
HIL Dispatch Interface
======================
Routes a validated HILCommand AST to the kernel dispatcher.

Separation of concerns:
  - Parser:   raw string   -> HILCommand AST
  - Validator: HILCommand  -> validated HILCommand (or error)
  - Logger:   HILCommand   -> artifact record
  - Dispatch: HILCommand   -> dispatcher envelope -> engine.run()

No execution logic belongs here.
No dispatch logic belongs in the parser or validator.
"""
from __future__ import annotations

from core.hil.parser import parse
from core.hil.validator import validate
from core.hil.errors import HILError


def dispatch(raw_command: str, dispatcher=None, log: bool = True) -> dict:
    """
    Full HIL pipeline: parse -> validate -> log -> dispatch.

    If dispatcher is None, returns validated AST info without executing.
    """
    from core.hil.command_logger import CommandLogger

    try:
        cmd = parse(raw_command)
        cmd = validate(cmd)
    except HILError as e:
        return {"status": "hil_error", "error": e.to_dict()}

    if log:
        CommandLogger.log(cmd)

    if dispatcher is None:
        return {
            "status":    "validated",
            "canonical": cmd.canonical(),
            "ast":       cmd.to_dict(),
        }

    # Build dispatcher envelope
    primary = cmd.primary_target()
    envelope = cmd.to_dict()
    envelope["target"]  = primary.name if primary else (cmd.subcommand or "")
    envelope["engine"]  = cmd.get_engine()

    return dispatcher.route(envelope)
