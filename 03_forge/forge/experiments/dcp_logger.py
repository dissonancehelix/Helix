import json
import csv
from pathlib import Path
from datetime import datetime

class DcpLogger:
    """
    Structured row-based logging for Helix experiments.
    Inspired by Sbox/dcplab/DcpLogger.cs.
    """
    def __init__(self, suite_name, artifact_dir="06_artifacts/artifacts"):
        self.suite_name = suite_name
        self.out_dir = Path(artifact_dir) / suite_name
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.out_dir / f"{suite_name}_trace.csv"
        self.json_file = self.out_dir / f"{suite_name}_report.json"
        self._rows = []
        self._report = {
            "suite": suite_name,
            "timestamp": datetime.now().isoformat(),
            "runs": []
        }

    def log_row(self, **kwargs):
        """Append a flat row of metrics to the trace."""
        row = {"timestamp": datetime.now().isoformat(), **kwargs}
        self._rows.append(row)
        
        # Write to CSV in real-time
        file_exists = self.csv_file.exists()
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def save_report(self, summary_metrics=None, config=None):
        """Save final JSON artifact with summary and config."""
        self._report["summary"] = summary_metrics or {}
        self._report["config"] = config or {}
        self._report["traces_count"] = len(self._rows)
        
        with open(self.json_file, "w") as f:
            json.dump(self._report, f, indent=4)
        
        print(f"Log generated: {self.csv_file}")
        print(f"Report generated: {self.json_file}")

if __name__ == "__main__":
    # Self-test
    logger = DcpLogger("logger_test")
    logger.log_row(n=64, l=1.0, k_eff=47.7, eps=0.01)
    logger.save_report(summary_metrics={"min_k": 47.7})
