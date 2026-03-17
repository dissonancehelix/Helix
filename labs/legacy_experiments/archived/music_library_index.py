import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from substrates.music.master_pipeline import MasterPipeline

def run(**kwargs):
    print("--- INDEX music_library ---")
    pipeline = MasterPipeline(stages=[1])
    pipeline.run()
    return {"status": "ok", "message": "Music library indexed"}

if __name__ == "__main__":
    run()
