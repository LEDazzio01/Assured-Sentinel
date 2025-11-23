##Assured Sentinel: Probabilistic Guardrails for Generative Code

Status: Phase 1: Build (Active)
Architecture: Multi-Agent System (MAS) + Split Conformal Prediction (SCP)

1. The Mission

The rapid ascendancy of Large Language Models (LLMs) has introduced a profound challenge: the inherent uncertainty of probabilistic outputs. While LLMs accelerate development, they cannot inherently quantify the risk of the code they generate.

Assured Sentinel bridges the gap between stochastic generation and deterministic safety. It is not merely a linter; it is a system that imposes mathematical safety guarantees on generative models using Split Conformal Prediction.

2. Architectural Overview

The system utilizes a Two-Agent Pattern to decouple generation from verification, preventing the "self-delusion" common in single-agent loops.

🧠 The Analyst (The Generator)

Role: The stochastic motor.

Behavior: High-temperature, high-entropy generation.

Objective: Propose creative solutions to user queries.

Stack: Azure OpenAI (gpt-4o) via Semantic Kernel.

🛡️ The Commander (The Guardrail)

Role: The deterministic logic gate.

Behavior: Strictly procedural and statistical.

Mechanism: It calculates a Non-Conformity Score (Inverse Security Score) using static analysis tools (bandit) and compares it against a pre-calibrated threshold ($\hat{q}$).

The Guarantee: Ensures that accepted code meets a specific risk tolerance ($1-\alpha$) with statistical validity.

3. Theoretical Framework

We strictly adhere to Split Conformal Prediction (SCP).

Calibration Set: We utilize a "Ground Truth" dataset (e.g., HumanEval/MBPP) to establish a baseline distribution of code scores.

Non-Conformity Measure (NCM): Defined via the bandit security linter. A score of 0.0 is Secure; 1.0 is Vulnerable.

The Guarantee:


$$P(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$$


We aim for an $\alpha = 0.1$, providing 90% confidence that the accepted code belongs to the set of secure outputs.







