import os
from core.validation.validator import ReplicationValidator
from core.validation.perturbations import PerturbationTester
from core.validation.null_models import NullModelTester

class AdversarialRunner:
    """
    Coordinates replication, perturbation, and null model tests.
    """
    def __init__(self, runner):
        self.runner = runner
        self.replication_validator = ReplicationValidator(runner)
        self.perturbation_tester = PerturbationTester(runner)
        self.null_tester = NullModelTester(runner)

    def run_all(self, envelope: dict, artifact_dir: str) -> dict:
        print(f"[adversarial] Running validation suite for {envelope.get('target')}...")
        
        rep_results = self.replication_validator.validate(envelope)
        pert_results = self.perturbation_tester.test(envelope)
        null_results = self.null_tester.test(envelope)
        
        # Calculate overall status
        checks = [
            rep_results.get("passed", False),
            pert_results.get("passed", False),
            null_results.get("passed", False)
        ]
        
        status = "VERIFIED" if all(checks) else "UNSTABLE"
        confidence = "HIGH" if status == "VERIFIED" else "LOW"
        
        report = {
            "status": status,
            "confidence": confidence,
            "replication": rep_results,
            "perturbation": pert_results,
            "null_model": null_results
        }
        
        # Save validation report
        self._save_report(artifact_dir, report)
        
        return report

    def _save_report(self, artifact_dir: str, report: dict):
        path = os.path.join(artifact_dir, "validation_report.yaml")
        # Simple YAML dump if PyYAML not available
        try:
            with open(path, "w") as f:
                f.write(self._to_yaml(report))
        except Exception as e:
            print(f"[adversarial] Failed to save report: {e}")

    def _to_yaml(self, data: dict, indent: int = 0) -> str:
        lines = []
        spacing = "  " * indent
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f"{spacing}{k}:")
                lines.append(self._to_yaml(v, indent + 1))
            else:
                lines.append(f"{spacing}{k}: {v}")
        return "\n".join(lines)
