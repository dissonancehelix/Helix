import re

_BLOCKED_RAW = (
    "rm ", "rm\t", "mkfs", "dd ", "dd\t", "sudo ",
    "DROP ", "DELETE FROM", "> /dev/",
    "chmod ", "chown ", "wget ", "curl ",
    "exec(", "__import__", "os.system", "subprocess",
    "eval(", "fork()", ">>",
)

# Use the exact string from the error message
text_lower = 'system sync message:" add internal management commands and quoted string support to hil\\'

for pat in _BLOCKED_RAW:
    stripped = pat.strip()
    if stripped.isalpha() and len(stripped) <= 5:
        match = re.search(rf"\b{re.escape(stripped)}\b", text_lower)
        if match:
            print(f"MATCHED WORD BOUNDARY: '{stripped}' at {match.start()}")
    elif pat.lower() in text_lower:
        print(f"MATCHED SUBSTRING: '{pat.lower()}'")
