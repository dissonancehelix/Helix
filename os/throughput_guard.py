import time
from pathlib import Path
from infra.os.panic_handler import emit_panic

class ThroughputGuard:
    def __init__(self, max_runtime=300):
        self.max_runtime = max_runtime
        self.start_time = time.time()
        
    def check(self, attempt_dir: Path, dataset_hash: str):
        if time.time() - self.start_time > self.max_runtime:
            emit_panic(attempt_dir, "EXECUTION_OVERFLOW", "ThroughputGuard", "Time Budget Exceeded", dataset_hash)
            return False
        return True
