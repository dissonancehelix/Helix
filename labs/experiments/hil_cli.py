import sys
import json
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.hil.interpreter import run_command

def main():
    if len(sys.argv) < 2:
        print("Usage: python hil_cli.py \"HIL_COMMAND\"")
        sys.exit(1)
    
    cmd_string = sys.argv[1]
    result = run_command(cmd_string)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
