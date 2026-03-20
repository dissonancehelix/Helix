import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from domains.music.master_pipeline import MasterPipeline

def run(**kwargs):
    print("--- INGEST composer_dataset (Training Sets) ---")
    # Stage 17 is training_sets in the new pipeline
    pipeline = MasterPipeline(stages=[17])
    pipeline.run()
    return {"status": "ok", "message": "Composer training sets prepared"}

if __name__ == "__main__":
    run()
