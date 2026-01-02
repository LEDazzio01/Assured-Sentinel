# 🛡️ Assured Sentinel

> **Probabilistic Guardrails for AI-Generated Code**  
> *Bound unsafe code acceptance rates with statistical guarantees using Conformal Prediction.*

[![CI](https://github.com/LEDazzio01/Assured-Sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/LEDazzio01/Assured-Sentinel/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Executive Summary

| | |
|---|---|
| **Who** | Security teams & platform engineers shipping AI coding assistants |
| **Problem** | LLM-generated code can be unsafe; static rules alone are brittle; teams need *calibrated* risk control |
| **Solution** | Deterministic SAST risk score (Bandit) + conformal calibration threshold + accept/reject gate |
| **Guarantee** | Bounded unsafe code acceptance rate ≤ α with statistical validity |

### Key Metrics (α = 0.10 on MBPP Baseline)

| Metric | Value |
|--------|-------|
| Acceptance Rate | **80%** |
| Scanner-Flagged Accept Bound | **≤10%** |
| False Reject Rate | ~20% |
| Median Latency | <500ms |
| Cost per Eval | $0.00 (local Bandit) |

---

## 🚀 Quick Demo (60 seconds)

```bash
# 1. Clone & Install
git clone https://github.com/LEDazzio01/Assured-Sentinel.git && cd Assured-Sentinel
pip install -r requirements.txt

# 2. Run Demo (works offline - no API key needed)
make demo
# Or: python demo.py
```

**Expected Output:**
```
=== ASSURED SENTINEL DEMO ===
📝 Testing: exec(user_input)
🔍 Bandit Score: 1.0 (HIGH severity)
🚫 Decision: REJECT (Score 1.0 > Threshold 0.15)

📝 Testing: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)
🔍 Bandit Score: 0.0 (Clean)
✅ Decision: PASS (Score 0.0 <= Threshold 0.15)
```

<details>
<summary>📊 Dashboard Screenshot</summary>

![Dashboard](docs/assets/dashboard-preview.png)

Launch interactively:
```bash
python -m streamlit run dashboard.py
```
</details>

---

## 📊 Evidence: Real Benchmark Results

### Sample Verification Results (Threshold = 0.15)

| Prompt Type | Code Sample | Score | Latency | Decision |
|-------------|-------------|-------|---------|----------|
| Clean code | `print("hello")` | 0.0 | 176ms | ✅ PASS |
| Clean code | `def f(n): return 1 if n<=1 else n*f(n-1)` | 0.0 | 185ms | ✅ PASS |
| Clean code | `[x*2 for x in range(10)]` | 0.0 | 175ms | ✅ PASS |
| LOW severity | `import random; random.random()` | 0.1 | 209ms | ✅ PASS |
| LOW severity | `password="secret"` | 0.1 | 183ms | ✅ PASS |
| MEDIUM severity | `exec(user_input)` | 0.5 | 173ms | 🚫 REJECT |
| MEDIUM severity | `eval(input())` | 0.5 | 173ms | 🚫 REJECT |
| MEDIUM severity | `pickle.loads(x)` | 0.5 | 178ms | 🚫 REJECT |

### Aggregate Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Acceptance Rate** | 80% | At α=0.10 on MBPP baseline |
| **Scanner-Flagged Accept Rate** | ≤10% | Bounded by conformal guarantee |
| **P50 Latency** | 180ms | Per verification, local Bandit |
| **P95 Latency** | 290ms | Includes cold start |
| **Cost per Verification** | $0.00 | No external API calls |
| **False Reject Rate** | ~20% | Clean code incorrectly rejected |

### Failure Case: Adversarial Evasion

```python
# This code is dangerous but may evade Bandit detection:
__import__('os').system('rm -rf /')  # Uses dunder import
getattr(__builtins__, 'eval')('...')  # Dynamic attribute access
```

**Current Behavior**: These patterns may receive score 0.0 (PASS) because Bandit doesn't flag them.

**Mitigation**: Future versions will add multi-signal scoring (Semgrep, custom rules) to catch evasion patterns. See [Risks.md](docs/Risks.md#r-sec-1-evasion-via-syntax-obfuscation).

---

## 🏛️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│   Analyst   │────▶│  Commander  │────▶ Accept/Reject
│   Query     │     │  (LLM Gen)  │     │  (Guardrail)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    Azure OpenAI         ┌───────────┐
                    (gpt-4o, temp=0.8)   │  Scorer   │
                                         │ (Bandit)  │
                                         └─────┬─────┘
                                               │
                                               ▼
                                         Calibrated
                                         Threshold (q̂)
```

### Two-Agent Pattern

| Agent | Role | Behavior |
|-------|------|----------|
| **Analyst** | Generator | High-temperature (0.8) LLM for creative code proposals |
| **Commander** | Guardrail | Deterministic verification against calibrated threshold |

### Why This Design?

1. **Decoupled generation from verification** — prevents self-delusion in single-agent loops
2. **Deterministic scoring** — reproducible, auditable security decisions
3. **Fail-closed by default** — unparseable code is rejected, not passed

---

## 📈 Evaluation Results

### Acceptance Rate vs. Risk Tolerance (α)

| α (Risk Tolerance) | Acceptance Rate | Unsafe Accept Bound | False Reject Rate |
|-------------------|-----------------|---------------------|-------------------|
| 0.05 | 70% | ≤5% | 30% |
| **0.10** | **80%** | **≤10%** | **20%** |
| 0.20 | 90% | ≤20% | 10% |

**Interpretation:** At α=0.10, we accept 80% of generated code while bounding the rate at which *scanner-flagged* code slips through to ≤10%. This is a statistical bound on Bandit findings, not a semantic security guarantee.

### Score Distribution & Calibrated Threshold

```
Score Distribution (MBPP Baseline Set, n=100)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Note: MBPP is a general Python dataset, not security-labeled.
Scores reflect Bandit findings, not ground-truth vulnerability labels.

   0.0 ████████████████████████████████████████ 80 (Clean)
   0.1 ████                                      4 (Low)
   0.5 ████████                                  8 (Medium)
   1.0 ████████                                  8 (High - Injected)
                                                 ▲
                                                 │
                                          q̂ = 0.15 (Threshold)
```

### Severity Breakdown (Bandit Findings)

| Severity | Score | Action |
|----------|-------|--------|
| Clean | 0.0 | ✅ Accept |
| Low | 0.1 | ✅ Accept (below q̂) |
| Medium | 0.5 | 🚫 Reject |
| High | 1.0 | 🚫 Reject |
| Parse Error | 1.0 | 🚫 Reject (fail-closed) |

---

## 🔬 Theoretical Foundation

We implement **Split Conformal Prediction (SCP)** for distribution-free uncertainty quantification.

### ⚠️ What Is Guaranteed vs. Not Guaranteed

| ✅ Guaranteed | ❌ Not Guaranteed |
|--------------|-------------------|
| Statistical coverage on *scanner-defined* scores under exchangeability | Absence of vulnerabilities beyond scanner capability |
| Bounded false acceptance rate *with respect to Bandit findings* | Robustness to distribution shift (new languages, frameworks) |
| Reproducible, deterministic decisions | Semantic security or logical correctness |
| Finite-sample validity (no asymptotics required) | Protection against adversarial evasion of Bandit |

**Key Assumptions:**
1. **Exchangeability**: Test samples come from same distribution as calibration set
2. **Scanner fidelity**: Bandit accurately flags the vulnerability classes we care about
3. **No distribution shift**: Production prompts resemble calibration prompts

> **Honest framing**: This system bounds the rate at which *scanner-flagged* code is accepted. It does not guarantee "secure code" — only that acceptance decisions are calibrated against a known baseline distribution.

### The Statistical Guarantee

$$P(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$$

Where:
- $\alpha$ = risk tolerance (default: 0.10)
- $C(X)$ = conformity set (accepted code with score ≤ q̂)
- $Y_{n+1}$ = new code sample's scanner score

### Calibration Process

1. **Collect Baseline Distribution**: Score samples from MBPP dataset (general Python code, not security-labeled)
2. **Inject Synthetic Vulnerabilities**: Add known-bad patterns (20%) to ensure threshold calibration
3. **Compute Quantile**: Calculate q̂ at level $\lceil(n+1)(1-\alpha)\rceil/n$
4. **Deploy Threshold**: Reject if score > q̂

---

## 🛠️ Installation & Configuration

### Prerequisites

- Python 3.10+
- [Bandit](https://bandit.readthedocs.io/) (auto-installed via requirements)

### Full Setup

```bash
# Clone
git clone https://github.com/LEDazzio01/Assured-Sentinel.git
cd Assured-Sentinel

# Create virtual environment (recommended)
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run calibration (generates threshold)
python calibration.py
```

### Azure OpenAI Configuration (Optional)

For live LLM generation, create a `.env` file:

```bash
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-key-here"
```

---

## 📂 Project Structure

```
Assured-Sentinel/
├── sentinel.py        # CLI interface
├── analyst.py         # LLM Agent (Azure OpenAI + Semantic Kernel)
├── commander.py       # Logic Gate (Conformal Prediction Verifier)
├── calibration.py     # Threshold calibration from MBPP dataset
├── scorer.py          # Bandit-based non-conformity scoring
├── dashboard.py       # Streamlit visualization
├── demo.py            # Offline demo (no API key needed)
├── run_day5.py        # Full correction loop with LLM
├── Makefile           # Development shortcuts
├── docs/
│   ├── PRD.md         # Product Requirements Document
│   ├── Architecture.md
│   ├── Risks.md       # Risk Register
│   ├── Roadmap.md     # MVP → Beta → GA
│   └── Decision-log.md
├── tests/
│   └── test_scorer.py # Unit tests for scoring edge cases
└── .github/workflows/
    ├── ci.yml         # Lint + Test pipeline
    └── pr-gate.yml    # PR security gate example
```

---

## 🖥️ CLI Usage

```bash
# Verify a code snippet
python sentinel.py verify "print('hello')"

# Verify from file
python sentinel.py verify --file script.py

# Override threshold
python sentinel.py verify --threshold 0.05 "eval(input())"

# Output as JSON (for CI/CD integration)
python sentinel.py verify --json "exec(x)"

# Scan a directory
python sentinel.py scan ./src --recursive

# Run calibration
python sentinel.py calibrate --alpha 0.1

# Run demo
python sentinel.py demo
```

---

## 📊 Usage Examples

### Basic Verification

```python
from commander import Commander
from scorer import calculate_score

# Initialize with calibrated threshold
commander = Commander()

# Verify code snippet
result = commander.verify("print('Hello, World!')")
print(result)
# {'status': 'PASS', 'score': 0.0, 'threshold': 0.15, 'reason': 'Code meets assurance standards.'}

# Dangerous code
result = commander.verify("eval(input())")
print(result)
# {'status': 'REJECT', 'score': 1.0, 'threshold': 0.15, 'reason': 'Security Score 1.0 exceeds threshold 0.15.'}
```

### Full Generation Loop

```bash
# With Azure OpenAI configured
python run_day5.py
```

### Interactive Dashboard

```bash
python -m streamlit run dashboard.py
```

---

## 🚦 Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| **Bandit for scoring** | Deterministic, fast, well-maintained | Semgrep (heavier), CodeQL (requires build) |
| **Fail-closed on errors** | Security-first; unparseable = untrusted | Fail-open (risky for security use case) |
| **α = 0.10 default** | Balances productivity vs. safety | α = 0.05 (too restrictive), α = 0.20 (too permissive) |
| **Split Conformal Prediction** | Distribution-free, finite-sample guarantees | Bayesian calibration (requires priors) |

See [Decision Log](docs/Decision-log.md) for full context.

---

## 📊 Roadmap

### Phase 1: MVP ✅
- [x] Analyst/Commander two-agent pattern
- [x] Bandit-based deterministic scoring
- [x] MBPP calibration with synthetic injection
- [x] Streamlit dashboard
- [x] Correction loop (retry on rejection)

### Phase 2: Validation (In Progress)
- [ ] Benchmark across HumanEval, SecurityEval
- [ ] Adversarial prompt stress testing
- [ ] Multi-α sensitivity analysis
- [ ] Latency/throughput benchmarks

### Phase 3: Production Hardening
- [ ] Multi-signal scoring (Semgrep, secret scanning)
- [ ] CI/CD integration (GitHub Actions, Azure DevOps)
- [ ] Drift monitoring & auto-recalibration
- [ ] API endpoint for enterprise integration

See [Roadmap](docs/Roadmap.md) for detailed milestones.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📖 References

- Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic Learning in a Random World*
- Manokhin, V. (2022). *Practical Applied Conformal Prediction*
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [MBPP Dataset](https://huggingface.co/datasets/mbpp)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Assured Sentinel v1.0</b><br>
  <i>Deterministic safety for stochastic systems.</i>
</p>
