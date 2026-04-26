import os
import re
from pathlib import Path
import json

TEMP_DIR = Path(r"C:\Users\dissonance\Desktop\temp")
SMPS_68K = TEMP_DIR / "SMPS-68000_source_code"
SMPS_Z80 = TEMP_DIR / "SMPS-Z80_source_code"
GEMS_DIR = TEMP_DIR / "GEMS"

def scan_smps():
    invariants = []
    signatures = {
        "Sound-Source": "SMPS_68K_OR_PICO",
        "Sound-Sorce": "SMPS_Z80",
        "Jimita": "HIROSHI_KUBOTA",
        "Bo": "TOKUHIKO_UWABO",
        "M.Nagao": "MASAYUKI_NAGAO"
    }
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            if f.endswith(('.ASM', '.S', '.INC', '.MAK')):
                path = Path(root) / f
                try:
                    content = path.read_text(encoding="latin-1") # ASM files often have non-UTF8 chars
                    for sig, label in signatures.items():
                        if sig in content:
                            invariants.append({
                                "type": "CODE_SIGNATURE",
                                "id": label,
                                "file": str(path.relative_to(TEMP_DIR)),
                                "context": f"Found signature {sig}"
                            })
                    
                    # Look for instrument definitions (e.g., FM patches)
                    # Heuristic: Find labels starting with 'Vo' or 'Patch' followed by hexadecimal/binary data
                    voice_blocks = re.findall(r'(\w+):\s+dc\.b\s+\$([0-9a-fA-F, \$]+)', content)
                    for label, data in voice_blocks[:10]: # Cap it for now
                        invariants.append({
                            "type": "VOICE_DEFINITION",
                            "name": label,
                            "data": data.strip(),
                            "source_file": str(path.relative_to(TEMP_DIR))
                        })

                except Exception as e:
                    pass
    return invariants

def scan_gems():
    invariants = []
    # GEMS patches often use a specific binary header or .PAT extension
    for root, dirs, files in os.walk(GEMS_DIR):
        for f in files:
            path = Path(root) / f
            if f.upper().endswith(('.PAT', '.INS')):
                invariants.append({
                    "type": "GEMS_PATCH",
                    "file": str(path.relative_to(GEMS_DIR)),
                    "size": path.stat().st_size
                })
    return invariants

if __name__ == "__main__":
    report = {
        "smps": scan_smps(),
        "gems": scan_gems()
    }
    
    output_path = Path(r"C:\Users\dissonance\Desktop\Helix\artifacts\source_code_invariants.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"Extracted {len(report['smps'])} SMPS and {len(report['gems'])} GEMS invariants.")
    
    # Generate HSL script for instruments
    hil_path = Path(r"C:\Users\dissonance\Desktop\Helix\artifacts\ingest_source_invariants.hsl")
    hil_cmds = []
    
    # Add Maintainers
    maintainers = {
        "HIROSHI_KUBOTA": "Hiroshi Kubota",
        "TOKUHIKO_UWABO": "Tokuhiko Uwabo",
        "MASAYUKI_NAGAO": "Masayuki Nagao"
    }
    
    seen_ids = set()
    for inv in report["smps"]:
        if inv["type"] == "CODE_SIGNATURE" and inv["id"] in maintainers:
            mid = f"music.operator:{inv['id'].lower()}"
            if mid not in seen_ids:
                hil_cmds.append(f"ENTITY add {mid} name:\"{maintainers[inv['id']]}\" type:Operator")
                seen_ids.add(mid)
                
    # Add Driver Entities
    hil_cmds.append("ENTITY add music.driver:smps_68k name:\"SMPS 68000\" type:Driver")
    hil_cmds.append("ENTITY add music.driver:smps_z80 name:\"SMPS Z80\" type:Driver")
    hil_cmds.append("ENTITY add music.driver:gems name:\"GEMS Sound Driver\" type:Driver")

    with open(hil_path, "w", encoding="utf-8") as f:
        f.write("\n".join(hil_cmds))
    print(f"HSL script written to {hil_path}")
