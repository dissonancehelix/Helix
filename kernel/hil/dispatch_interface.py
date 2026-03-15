# HIL Dispatch Interface
# Bridge between normalized HIL commands and the kernel dispatcher.
# All execution requests flow through this interface.

from .normalizer import normalize_command


def dispatch(raw_command: str, dispatcher) -> dict:
    """
    Normalize a raw HIL command and route it to the dispatcher.

    Args:
        raw_command: A raw string HIL command (e.g. "run python.oscillator")
        dispatcher:  The kernel dispatcher instance

    Returns:
        Execution result dict from the dispatcher
    """
    envelope = normalize_command(raw_command)
    return dispatcher.route(envelope)
