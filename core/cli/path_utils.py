import os
import re
from pathlib import Path

def normalize_path(path_str: str) -> str:
    """
    Convert Windows paths to MSYS2/Unix style paths.
    E.g. C:\\Users\\dissonance\\Music -> /c/Users/dissonance/Music
    """
    if not path_str:
        return path_str
    
    # Replace backslashes with forward slashes
    path_str = path_str.replace('\\', '/')
    
    # Handle drive letters: C:/... -> /c/...
    match = re.match(r'^([A-Z]):/(.*)', path_str, re.IGNORECASE)
    if match:
        drive = match.group(1).lower()
        rest = match.group(2)
        return f"/{drive}/{rest}"
    
    return path_str

def to_windows_path(msys_path: str) -> str:
    """
    Optional: Convert MSYS2 style to Windows path if needed for internal logic.
    E.g. /c/Users -> C:\\Users
    """
    match = re.match(r'^/([A-Z])/(.*)', msys_path, re.IGNORECASE)
    if match:
        drive = match.group(1).upper()
        rest = match.group(2).replace('/', '\\')
        return f"{drive}:\\{rest}"
    return msys_path.replace('/', '\\')
