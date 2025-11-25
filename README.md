🛡️ Assured SentinelProbabilistic Guardrails for Generative Code🚀 The MissionThe rapid ascendancy of Large Language Models (LLMs) has introduced a profound challenge: the inherent uncertainty of probabilistic outputs. While LLMs accelerate development, they cannot inherently quantify the risk of the code they generate.Assured Sentinel bridges the gap between stochastic generation and deterministic safety. It is not merely a linter; it is a system that imposes mathematical safety guarantees on generative models using Split Conformal Prediction (SCP).ShutterstockExplore🏛️ Architectural OverviewThe system employs a Two-Agent Pattern to decouple generation from verification, preventing the self-delusion common in single-agent loops.🧠 The Analyst (Generator)Role: The stochastic motorBehavior: High-temperature (0.8), high-entropy generationObjective: Propose creative solutions to user queriesStack: Azure OpenAI (gpt-4o) via Semantic Kernel🛡️ The Commander (Guardrail)Role: The deterministic logic gateBehavior: Strictly procedural and statisticalMechanism:Calculates a Non-Conformity Score (Inverse Security Score) using static analysis (simulated or bandit).Compares against a pre-calibrated threshold ($\hat{q}$).Guarantee: Ensures accepted code meets a specific risk tolerance ($1 - \alpha$) with statistical validity.🛠️ Quick StartPrerequisitesPython 3.10+Azure OpenAI API Key1. InstallationClone the repository and install dependencies:# Clone the repository
git clone [https://github.com/your-username/assured-sentinel.git](https://github.com/your-username/assured-sentinel.git)
cd assured-sentinel

# Install dependencies
pip install -r requirements.txt
2. ConfigurationCreate a .env file in the root directory with your Azure OpenAI credentials:AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
AZURE_OPENAI_ENDPOINT="[https://your-resource.openai.azure.com/](https://your-resource.openai.azure.com/)"
AZURE_OPENAI_API_KEY="your-key-here"
3. Calibration (One-Time Setup)Before running the system, you must establish the safety threshold ($\hat{q}$). This script downloads the calibration dataset (MBPP), injects synthetic vulnerabilities, and calculates the conformal quantile.python calibration.py
Output: Generates calibration_data.pkl containing the calculated safety threshold based on an alpha of 0.1.4. Run the SentinelExecute the main event loop. The Analyst will generate code, and the Commander will accept or reject it based on the calibrated threshold.python run_day4.py
📂 Project Structureassured-sentinel/
├── analyst.py          # LLM Agent (Azure OpenAI + Semantic Kernel)
├── commander.py        # Logic Gate (Conformal Prediction Verifier)
├── calibration.py      # Calibration script (calculates q_hat from MBPP)
├── scorer.py           # Non-Conformity Measure (NCM) logic
├── run_day4.py         # Main entry point / orchestration loop
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
📐 Theoretical FrameworkWe strictly adhere to Split Conformal Prediction (SCP).Calibration Set: A "Ground Truth" dataset (e.g., MBPP) establishes a baseline distribution of code scores.Non-Conformity Measure (NCM): A scoring function where 0.0 is Secure and 1.0 is Vulnerable.The Guarantee:$$P(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$$We target $\alpha = 0.1$, providing 90% confidence that accepted code belongs to the set of secure outputs.📊 Roadmap[x] Phase 1 – Build (MVP):[x] Implement Analyst/Commander MAS pattern[x] Implement NCM scoring logic[x] Establish calibration set with MBPP[ ] Phase 2 – Validate:[ ] Benchmark SCP thresholds across diverse datasets[ ] Stress-test against adversarial prompts[ ] Phase 3 – Deploy:[ ] Package as reproducible GitHub Codespace[ ] Integrate with CI/CD pipelines📖 ReferencesPractical Applied Conformal Prediction by Valeriy ManokhinHumanEval & MBPP datasetsBandit: Python Security Linter
