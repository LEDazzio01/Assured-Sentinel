# Assured Sentinel: Probabilistic Guardrails for Generative Code

**Status:** Phase 1 – Build (Active)  
**Architecture:** Multi-Agent System (MAS) + Split Conformal Prediction (SCP)

---

## 🚀 The Mission
The rapid ascendancy of **Large Language Models (LLMs)** has introduced a profound challenge: the inherent uncertainty of probabilistic outputs.  
While LLMs accelerate development, they cannot inherently quantify the risk of the code they generate.

**Assured Sentinel** bridges the gap between stochastic generation and deterministic safety.  
It is not merely a linter; it is a system that imposes **mathematical safety guarantees** on generative models using **Split Conformal Prediction (SCP).**

---

## 🏛️ Architectural Overview
The system employs a **Two-Agent Pattern** to decouple generation from verification, preventing the *self-delusion* common in single-agent loops.

### 🧠 The Analyst (Generator)
- **Role:** The stochastic motor  
- **Behavior:** High-temperature, high-entropy generation  
- **Objective:** Propose creative solutions to user queries  
- **Stack:** Azure OpenAI (gpt-4o) via Semantic Kernel  

### 🛡️ The Commander (Guardrail)
- **Role:** The deterministic logic gate  
- **Behavior:** Strictly procedural and statistical  
- **Mechanism:**  
  - Calculates a **Non-Conformity Score (Inverse Security Score)** using static analysis tools (e.g., `bandit`)  
  - Compares against a pre-calibrated threshold \(\hat{q}\)  
- **Guarantee:** Ensures accepted code meets a specific risk tolerance \((1 - \alpha)\) with statistical validity  

---

## 📐 Theoretical Framework
We strictly adhere to **Split Conformal Prediction (SCP).**

- **Calibration Set:**  
  A "Ground Truth" dataset (e.g., *HumanEval*, *MBPP*) establishes a baseline distribution of code scores.  

- **Non-Conformity Measure (NCM):**  
  Defined via the `bandit` security linter.  
  - **0.0 → Secure**  
  - **1.0 → Vulnerable**  

- **The Guarantee:**  
  

  \[
    P\big(Y_{n+1} \in C(X_{n+1})\big) \geq 1 - \alpha
    \]



  We target \(\alpha = 0.1\), providing **90% confidence** that accepted code belongs to the set of secure outputs.

---

## 📊 Roadmap
- **Phase 1 – Build (Active):**  
  - Implement Analyst/Commander MAS pattern  
  - Integrate `bandit` for NCM scoring  
  - Establish calibration set with HumanEval/MBPP  

- **Phase 2 – Validate:**  
  - Benchmark SCP thresholds across diverse datasets  
  - Stress-test against adversarial prompts  

- **Phase 3 – Deploy:**  
  - Package as reproducible GitHub Codespace  
  - Integrate with CI/CD pipelines for enterprise reliability  

---

## 🔑 Why It Matters
- **Beyond Linters:** Provides *probabilistic safety guarantees* instead of heuristic checks.  
- **Enterprise Relevance:** Aligns with Responsible AI and cloud infrastructure reliability themes.  

---

## 📖 References
- Vovk, V., Gammerman, A., & Shafer, G. *Algorithmic Learning in a Random World* (2005)  
- HumanEval & MBPP datasets for calibration baselines  
- Bandit: Python Security Linter  

---






