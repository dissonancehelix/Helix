import sys
from pathlib import Path
import json
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from substrates.music.analysis.composer_reports import generate_composer_reports
from substrates.music.config import COMPOSER_PROFILES_PATH

def run(**kwargs):
    print("--- EXPORT composer_report ---")
    p = Path(COMPOSER_PROFILES_PATH)
    if p.exists():
        with open(p) as f:
            data = json.load(f)
            generate_composer_reports(data)
            return {"status": "ok", "message": "Composer report generated"}
    return {"status": "error", "message": "Composer profiles not found at " + str(p)}

if __name__ == "__main__":
    run()
