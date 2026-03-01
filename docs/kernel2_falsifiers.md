Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/kernels/kernel2_report.json

# Kernel-2 Falsification Hooks (EIP Independence)

To structurally falsify the hypothesis that the Epistemic Irreversibility Principle (EIP) acts as an independent Kernel-2, the following counterexamples or tests must be successfully demonstrated:

1. **Independence Claim Falsification:**
   Demonstrate that `KERNEL2_CANDIDATE` conditional mutual information `IG(EIP → BoundaryType | Substrate, Ontology)` approaches the null model mean after a sufficient dataset expansion (N > 5000), meaning the irreversibility metric possesses no unique structural variance not already contained within the primary Kernel-1 structural projection.

2. **Residual Reduction Violation:**
   Identify a set of domains where predicting `BoundaryType` solely from `(Substrate, Ontology)` yields a specific residual classification error, and prove that feeding the `EIP_class` overlay into the predictor fails to partition this residual entropy at a statistically significant level. 

3. **Stability Claim Violation (Catastrophic Interference):**
   Execute a 10% dropout test or synthetic structural injection where removing domains from a specific `Substrate` class causes `IG(EIP → Ontology)` and structural drift to jump above the measured 0.02 bounds, demonstrating that Kernel-2 is highly fragile and overfitted to specific topological classes.

4. **Direct Reconstructability Falsification:**
   Build a shallow classification tree targeting `EIP_class` using solely `[SubstrateRefined, Ontology, BoundaryType, Locality]`. Determine that the model can reconstruct the exact mapping of `EIP_class` with > 95% accuracy. If the labels are trivially derivable from Kernel-1 primitives, EIP is a derivative calculation, not an independent kernel mechanism.
