import os
import json
from pathlib import Path
from sklearn.base import clone

# Must not import core bases or metaphysical classes. Strict industry focus.
from engines.hostility_engine import HostilityEngine
from engines.registry_writer import append_to_registry

class MLInstabilityAuditor:
    def __init__(self, model, X, y, run_id="default_run", random_state=42):
        self.model = clone(model)
        self.X = X
        self.y = y
        self.run_id = run_id
        self.engine = HostilityEngine(random_state=random_state)
        
        # Ensure base directories exist
        from engines.helix import ARTIFACTS_DIR
        self.audit_dir = ARTIFACTS_DIR / "ml_instability_audit" / self.run_id
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
    def execute_audit(self):
        # 1. Train baseline model
        self.model.fit(self.X, self.y)
        base_pred = self.model.predict(self.X)
        from sklearn.metrics import accuracy_score
        baseline_acc = accuracy_score(self.y, base_pred)
        
        with open(self.audit_dir / "baseline_accuracy.json", "w") as f:
            json.dump({"baseline_accuracy": baseline_acc}, f, indent=4)
            
        # 2. Run hostility engine
        metrics = self.engine.testModelStability(self.model, self.X, self.y)
        self.engine.generate_report(self.audit_dir, metrics)
        
        # 3. Compute fragility curve / specific dropoffs
        fragility_gradient = metrics.get("fragility_gradient", 0.0)
        with open(self.audit_dir / "fragility_curve.json", "w") as f:
            json.dump({
                "fragility_gradient": fragility_gradient,
                "null_delta": metrics.get("null_delta", 0.0)
            }, f, indent=4)
            
        # 4. Classify
        # If PSS is highly stable (> 0.95), CSI is good -> Stable (BIC-equivalent)
        # If PSS is poor but better than null -> Representation-Dependent (RDC-equivalent)
        # If PSS drops to null -> Collapse-Risk
        
        pss = metrics.get("PSS", 0)
        null_delta = metrics.get("null_delta", 0)
        classification = "Stable"
        atlas_class = "BIC"
        
        if pss < 0.85 and null_delta > 0.1:
            classification = "Representation-Dependent"
            atlas_class = "RDC"
        elif pss < 0.5 or null_delta <= 0.05:
            classification = "Collapse-Risk"
            atlas_class = "HYBRID"
            
        # Write summary
        summary = f"""# ML Instability Audit Summary : {self.run_id}

## Baseline
- Accuracy: {baseline_acc:.4f}

## Hostility Report
- Projection Stability Score (PSS): {pss:.4f}
- Bound Adversarial Survival (BAS): {metrics.get('BAS', 0):.4f}
- Fragility Gradient: {fragility_gradient:.4f}
- Null Delta: {null_delta:.4f}

## Verdict
**Classification:** {classification}
"""
        with open(self.audit_dir / "audit_summary.md", "w") as f:
            f.write(summary)
            
        # 5. Append to cross-project registry
        append_to_registry(
            domain=f"ml_instability_{self.run_id}",
            artifact_path=str(self.audit_dir.relative_to(Path(__file__).resolve().parent.parent.parent)),
            pss=pss,
            bas=metrics.get('BAS', 0),
            csi=metrics.get('CSI', 0),
            fragility_gradient=fragility_gradient,
            classification=atlas_class
        )
        
        return classification

if __name__ == '__main__':
    assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\', '/'), 'Output path contains nested artifacts directory.'
    # Simple isolated test
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression
    
    X, y = make_classification(n_samples=100, n_features=20, random_state=42)
    clf = LogisticRegression()
    
    auditor = MLInstabilityAuditor(clf, X, y, run_id="test_run")
    res = auditor.execute_audit()
    print(f"Audit completed. Decision: {res}")
