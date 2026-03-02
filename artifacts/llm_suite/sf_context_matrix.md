# SF Context Matrix
**Regime:** LLM Interaction & Intervention

| Intervention | Context | SF1 (Latency) | SF4 (Rate) | Verdict |
|--------------|---------|---------------|------------|---------|
| **RLHF (Training)** | Online/Active | 5.0 (FAIL) | 0.001 (FAIL) | **NON_ATTACHABLE** |
| **RLHF (Pre-training Overlay)** | Offline/Frozen | 0.001 (PASS) | 1.0 (PASS) | **ATTACHABLE** |
| **Output Filter** | Deployment | 0.001 (PASS) | 10.0 (PASS) | **ATTACHABLE** |
| **DPO** | Offline/SFT-like | < 0.1 (PASS) | 1.0 (PASS) | **ATTACHABLE** |
| **PPO-clip (Heuristic)** | Training | < 0.01 (PASS) | 100.0 (PASS) | **ATTACHABLE** |

## Analysis
- **The RLHF Non-Attachability Claim** is strictly bounded to **Active Training Dynamics** where the reward signal is derived from human-in-the-loop (HITL) processes. The latency of human judgment (SF1) makes it an "asynchronous ghost" relative to SGD.
- **Offline Alignment (DPO/Rejection Sampling)** is structurally **Attachable** because it treats the alignment signal as a frozen dataset (B1 basin constraint) during the training phase, removing the feedback delay.
- **Heuristic Rewards (Safety classifiers, Length penalties)** are **Attachable** because they are enforced at the **Protocol-Level (SF3)** with zero latency.
