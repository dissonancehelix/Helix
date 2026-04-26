import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from substrates.music.master_pipeline import MasterPipeline

def run(**kwargs):
    print("--- TRAIN composer_vectors ---")
    # Stage 11 is composer_fp (fingerprinting)
    pipeline = MasterPipeline(stages=[11])
    pipeline.run()
    return {"status": "ok", "message": "Composer style vectors trained"}

if __name__ == "__main__":
    run()
