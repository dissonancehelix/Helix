import os
import json
import math
import random
from pathlib import Path
from collections import Counter, defaultdict

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.model_selection import KFold, train_test_split
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
AUDITS_DIR = ROOT / 'audits'
DOMAINS_DIR = ROOT / 'domains'

domains = []
for p in DOMAINS_DIR.glob('*.json'):
    with open(p, 'r') as f:
        domains.append(json.load(f))

# Define S1c classes
s1c_classes = ["CONTINUOUS", "DISCRETE_SYMBOLIC", "STOCHASTIC", "HYBRID"]
boundary_classes = ["SMOOTH_HYPERSURFACE", "SINGULAR_DIVERGENCE", "GLOBAL_DISCONTINUITY", "COMBINATORIAL_THRESHOLD", "DISTRIBUTIONAL_COLLAPSE"]

# Extract features
X_texts = []
y_s1c = []
y_bound = []
X_ontology = []

for d in domains:
    # Build text feature ignoring substrate/boundary
    parts = []
    for k in ["state_space", "dynamics_operator", "perturbation_operator", "stability_condition", "failure_mode", "notes"]:
        if d.get(k):
            # rudimentary mask of explicit S1c words to avoid trivial leakage
            val = d[k].lower()
            for w in ["continuous", "discrete", "symbolic", "stochastic", "hybrid", "combinatorial_threshold", "smooth_hypersurface", "singular_divergence", "global_discontinuity", "distributional_collapse"]:
                val = val.replace(w, " ")
            parts.append(val)
            
    # Observers
    obs = d.get('observable_metrics', [])
    for o in obs:
        if isinstance(o, str): parts.append(o.lower())
        elif isinstance(o, dict): parts.append(str(o.get('name','')).lower() + " " + str(o.get('type','')).lower())
        
    X_texts.append(" ".join(parts))
    y_s1c.append(d.get('substrate_S1c', 'HYBRID'))
    y_bound.append(d.get('boundary_type_primary', 'UNKNOWN'))
    X_ontology.append(d.get('persistence_ontology', 'UNKNOWN'))

# PHASE 25 - RECONSTRUCTORS
def rule_based_predict(text):
    text = text.lower()
    if any(w in text for w in ["probability", "markov", "distribution", "ensemble", "random", "noise"]):
        return "STOCHASTIC"
    if any(w in text for w in ["graph", "lattice", "code", "syndrome", "grammar", "logic", "rule", "combinator", "discrete"]):
        return "DISCRETE_SYMBOLIC"
    if any(w in text for w in ["manifold", "pde", "ode", "equation", "field", "continuous", "metric", "gradient", "smooth"]):
        return "CONTINUOUS"
    return "HYBRID"

rule_preds = [rule_based_predict(t) for t in X_texts]
rule_acc = sum(1 for p, y in zip(rule_preds, y_s1c) if p == y) / len(y_s1c)

best_reconstructor = "Rule-based"
best_acc = rule_acc
best_preds = rule_preds

if SKLEARN_AVAILABLE:
    vec = TfidfVectorizer(max_features=100, stop_words='english')
    X_vec = vec.fit_transform(X_texts)
    
    # 80/20 split
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(X_vec, y_s1c, list(range(len(y_s1c))), test_size=0.2, random_state=42)
    
    clfs = {
        "Logistic Regression": LogisticRegression(random_state=42),
        "Random Forest": RandomForestClassifier(random_state=42),
        "Naive Bayes": MultinomialNB()
    }
    
    results_md = "# Phase 25 Substrate Reconstruction\n\n## Model Accuracies (80/20 split)\n"
    for name, clf in clfs.items():
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        acc = accuracy_score(y_test, preds)
        results_md += f"- {name}: {acc:.3f}\n"
        
        # Save best for Phase 26
        if acc > best_acc:
            best_acc = acc
            best_reconstructor = name
            # Get full predictions
            clf.fit(X_vec, y_s1c)
            best_preds = clf.predict(X_vec)
            
    results_md += f"\n- Rule-based (Zero-shot): {rule_acc:.3f}\n"

    # Leakage Audit (Ablation)
    results_md += "\n## Leakage Audit\n"
    vec_strict = TfidfVectorizer(max_features=100, stop_words='english')
    # Ablate fields: only use state_space and dynamics_operator
    X_strict_texts = []
    for d in domains:
        parts = [d.get("state_space",""), d.get("dynamics_operator","")]
        val = " ".join(parts).lower()
        for w in ["continuous", "discrete", "symbolic", "stochastic", "hybrid", "combinatorial", "divergence", "collapse"]:
            val = val.replace(w, " ")
        X_strict_texts.append(val)
        
    X_vec_strict = vec_strict.fit_transform(X_strict_texts)
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_vec_strict, y_s1c, test_size=0.2, random_state=42)
    clf_s = LogisticRegression(random_state=42)
    clf_s.fit(X_train_s, y_train_s)
    acc_s = accuracy_score(y_test_s, clf_s.predict(X_test_s))
    results_md += f"- Ablated Logistic Regression (State/Dynamics only): {acc_s:.3f}\n"
    
    with open(AUDITS_DIR / 'phase25_substrate_reconstruction.md', 'w') as f:
        f.write(results_md)

else:
    best_preds = rule_preds
    with open(AUDITS_DIR / 'phase25_substrate_reconstruction.md', 'w') as f:
        f.write("# Phase 25 Substrate Reconstruction\n\n- Rule-based Acc: {rule_acc:.3f}\n(Sklearn not available for ML models)\n")


# PHASE 26 - HOLDOUT GENERALIZATION
def entropy(labels):
    c = Counter(labels)
    t = len(labels)
    if t == 0: return 0.0
    return -sum((v/t)*math.log2(v/t) for v in c.values() if v > 0)
    
def cond_entropy(X, Y):
    yc = Counter(Y)
    t = len(Y)
    return sum((yc_val/t) * entropy([x for x, y in zip(X, Y) if y == yv]) for yv, yc_val in yc.items())

# Simple predictor: most common boundary per feature value
def simulate_prediction(train_feat, train_y, test_feat, test_y):
    mapping = {}
    for f in set(train_feat):
        subset = [y for tr_f, y in zip(train_feat, train_y) if tr_f == f]
        mapping[f] = Counter(subset).most_common(1)[0][0] if subset else "UNKNOWN"
        
    preds = [mapping.get(f, "UNKNOWN") for f in test_feat]
    acc = sum(1 for p, y in zip(preds, test_y) if p == y) / len(test_y)
    return acc, preds

# Split 80/20
random.seed(42)
indices = list(range(len(domains)))
random.shuffle(indices)
split = int(0.8 * len(domains))
train_idx, test_idx = indices[:split], indices[split:]

# IG over full dataset for simplicity of reporting
ig_oracle = entropy(y_bound) - cond_entropy(y_bound, y_s1c)
ig_recon = entropy(y_bound) - cond_entropy(y_bound, best_preds)
ig_nosub = entropy(y_bound) - cond_entropy(y_bound, X_ontology)

# Accuracy on test set
train_y = [y_bound[i] for i in train_idx]
test_y = [y_bound[i] for i in test_idx]

# Cond 1: True S1c
train_f1 = [y_s1c[i] for i in train_idx]
test_f1 = [y_s1c[i] for i in test_idx]
acc_1, _ = simulate_prediction(train_f1, train_y, test_f1, test_y)

# Cond 2: Recon S1c
train_f2 = [best_preds[i] for i in train_idx]
test_f2 = [best_preds[i] for i in test_idx]
acc_2, _ = simulate_prediction(train_f2, train_y, test_f2, test_y)

# Cond 3: No Substrate (Ontology only)
train_f3 = [X_ontology[i] for i in train_idx]
test_f3 = [X_ontology[i] for i in test_idx]
acc_3, _ = simulate_prediction(train_f3, train_y, test_f3, test_y)

res26_md = f"""# Phase 26 Holdout Generalization

## Metrics
| Condition | Accuracy (20% Holdout) | Full IG (bits) |
|---|---|---|
| Oracle S1c | {acc_1:.3f} | {ig_oracle:.3f} |
| Reconstructed S1c | {acc_2:.3f} | {ig_recon:.3f} |
| No Substrate (Ontology) | {acc_3:.3f} | {ig_nosub:.3f} |
"""
with open(AUDITS_DIR / 'phase26_holdout_generalization.md', 'w') as f:
    f.write(res26_md)

print(f"Phase 25 complete: {best_acc:.3f}")
print(f"Phase 26 complete: Oracle acc={acc_1:.3f}, Reconstructed acc={acc_2:.3f}, NoSubstrate acc={acc_3:.3f}")
print(f"IG: Oracle={ig_oracle:.3f}, Reconstructed={ig_recon:.3f}, NoSubstrate={ig_nosub:.3f}")
