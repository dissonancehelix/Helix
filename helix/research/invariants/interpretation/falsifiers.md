# Intervention Falsifiers
**Helix CE-OS Falsification Suite**

## 1. Kessler-AIMD Falsifiers
The transfer of TCP AIMD logic to LEO satellite management is invalidated if:
- **F1 (Signal Delay):** The orbital decay rate (delta) is so slow that even a zero-launch policy (L=0) fails to stop a cascade already in progress (λ*D^2 > δ*D).
- **F2 (Byzantine Action):** Multiplicative decrease is ignored by > 30% of agents, leading to the "Tragedy of the Common" where managed agents lose market share while unmanaged agents saturate the orbital buffer.
- **F3 (Threshold Lag):** The "Conjunction Frequency" signal is too noisy to distinguish from random vibration, leading to unnecessary launch throttling (false positive).

## 2. Babel-ECC Falsifiers
The transfer of ECC logic to Semantic Drift stabilization (Babel) is invalidated if:
- **F1 (Abstraction Saturation):** The additional B4 symbolic overhead required for parity checksums consumes 100% of the agent's processing window, causing a "Metabolic Collapse" independent of the drift.
- **F2 (Basis Corruption):** The B1-B4 bases themselves are subjected to semantic drift (Bases become Metaphors), rendering the "checksum" as noisy as the message.
- **F3 (Low IG Delta):** Redundancy injection fails to improve coordination accuracy by > 5% in a double-blind communication trial.
