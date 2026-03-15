# HIL Grammar
# Defines the structural rules for valid Helix commands.
#
# HIL command structure:
#   VERB  TARGET  [PARAMS...]
#
# Verbs:   run | probe | sweep | observe | report | validate | reset
# Targets: engine name, experiment path, or substrate identifier
# Params:  key=value pairs

HIL_VERBS = {"run", "probe", "sweep", "observe", "report", "validate", "reset"}

HIL_SCHEMA = {
    "run":      {"required": ["target"], "optional": ["params", "mode"]},
    "probe":    {"required": ["target"], "optional": ["depth", "substrate"]},
    "sweep":    {"required": ["target", "param"], "optional": ["range", "steps"]},
    "observe":  {"required": ["target"], "optional": ["window", "metric"]},
    "report":   {"required": ["target"], "optional": ["format", "output"]},
    "validate": {"required": ["target"], "optional": ["strict"]},
    "reset":    {"required": [],         "optional": ["scope"]},
}


def parse_command(raw: str) -> dict:
    """Parse a raw string into a HIL command dict."""
    tokens = raw.strip().split()
    if not tokens:
        raise ValueError("Empty command")

    verb = tokens[0].lower()
    if verb not in HIL_VERBS:
        raise ValueError(f"Unknown verb '{verb}'. Valid verbs: {HIL_VERBS}")

    result = {"verb": verb, "target": None, "params": {}}

    if len(tokens) > 1:
        result["target"] = tokens[1]

    for token in tokens[2:]:
        if "=" in token:
            k, v = token.split("=", 1)
            result["params"][k] = v

    return result
