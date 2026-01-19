# 🛡️ Assured Sentinel

> **Probabilistic Guardrails for AI-Generated Code**  
> *Bound unsafe code acceptance rates with statistical guarantees using Conformal Prediction.*

[![CI](https://github.com/LEDazzio01/Assured-Sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/LEDazzio01/Assured-Sentinel/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

---

## 📚 Strategic Context

> **For reviewers evaluating architectural decision-making and research depth:**

| Document | Description |
|----------|-------------|
| **[Decision Log](docs/Decision-log.md)** | Comprehensive record of technical and product decisions with alternatives considered, rationale, and trade-offs |
| **[Deep Research Analysis](20251123_Assured_Sentinel_Deep_Research.pdf)** | Foundational research on Conformal Prediction, SAST tools, and statistical guarantees for AI safety |
| **[Architecture](docs/Architecture.md)** | System design, component interactions, scalability constraints, and extensibility patterns |
| **[Risk Register](docs/Risks.md)** | Security, operational, and theoretical risks with mitigations |
| **[Product Roadmap](docs/Roadmap.md)** | Phased development plan from MVP through enterprise scale |
| **[CHANGELOG](CHANGELOG.md)** | Version history and migration guides |

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

## 🚀 Quick Start

### Installation

```bash
# Clone & Install
git clone https://github.com/LEDazzio01/Assured-Sentinel.git && cd Assured-Sentinel
pip install -e ".[dev]"

# Run Demo (works offline - no API key needed)
sentinel demo
```

### As a Library

```python
from assured_sentinel import Commander, BanditScorer

# Initialize with calibrated threshold
commander = Commander()

# Verify code snippet
result = commander.verify("print('Hello, World!')")
print(f"Status: {result.status}, Score: {result.score}")
# Status: PASS, Score: 0.0

# Dangerous code
result = commander.verify("exec(user_input)")
print(f"Status: {result.status}, Score: {result.score}")
# Status: REJECT, Score: 0.5
```

### Expected Demo Output

```
=== ASSURED SENTINEL - OFFLINE DEMO ===
📝 Testing: exec(user_input)
🔍 Bandit Score: 0.5 (MEDIUM severity)
🚫 Decision: REJECT (Score 0.5 > Threshold 0.15)

📝 Testing: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)
🔍 Bandit Score: 0.0 (Clean)
✅ Decision: PASS (Score 0.0 <= Threshold 0.15)
```

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
4. **SOLID principles** — extensible, testable, maintainable

---

## 📂 Project Structure

```
Assured-Sentinel/
├── assured_sentinel/           # Main package
│   ├── __init__.py            # Package exports
│   ├── config.py              # Pydantic Settings (centralized config)
│   ├── models.py              # Pydantic models (DTOs)
│   ├── protocols.py           # Protocol interfaces (ISP/DIP)
│   ├── exceptions.py          # Custom exception hierarchy
│   ├── core/                  # Core business logic
│   │   ├── scorer.py          # BanditScorer (IScoringService)
│   │   ├── commander.py       # Commander (IVerifier)
│   │   └── calibrator.py      # ConformalCalibrator
│   ├── agents/                # LLM integration
│   │   └── analyst.py         # AzureAnalyst (ICodeGenerator)
│   ├── cli/                   # Command-line interface
│   │   └── main.py            # CLI entry points
│   └── dashboard/             # Streamlit UI
│       └── app.py             # Dashboard application
├── tests/                     # Comprehensive test suite
│   ├── conftest.py            # Shared fixtures
│   ├── unit/                  # Unit tests
│   │   ├── test_scorer.py
│   │   ├── test_commander.py
│   │   ├── test_calibrator.py
│   │   ├── test_analyst.py
│   │   ├── test_models.py
│   │   └── test_exceptions.py
│   └── integration/           # Integration tests
│       └── test_full_flow.py
├── docs/                      # Documentation
│   ├── Architecture.md
│   ├── Decision-log.md
│   ├── PRD.md
│   ├── Risks.md
│   └── Roadmap.md
├── pyproject.toml             # Project configuration
├── requirements.txt           # Dependencies
├── Makefile                   # Development shortcuts
├── CHANGELOG.md               # Version history
└── README.md                  # This file
```

---

## 🖥️ CLI Usage

```bash
# Verify a code snippet
sentinel verify "print('hello')"

# Verify from file
sentinel verify --file script.py

# Override threshold
sentinel verify --threshold 0.05 "eval(input())"

# Output as JSON (for CI/CD integration)
sentinel verify --json "exec(x)"

# Scan a directory
sentinel scan ./src --recursive

# Run calibration
sentinel calibrate --alpha 0.1 --samples 100

# Run demo
sentinel demo

# Run LLM correction loop (requires Azure OpenAI)
sentinel run "Write a function to calculate factorial"
```

---

## ⚙️ Configuration

### Environment Variables

All settings can be configured via environment variables with the `SENTINEL_` prefix:

```bash
# Core settings
SENTINEL_ALPHA=0.1                    # Risk tolerance
SENTINEL_DEFAULT_THRESHOLD=0.15       # Fallback threshold
SENTINEL_LOG_LEVEL=INFO               # Logging level

# Azure OpenAI (optional - for Analyst)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### Programmatic Configuration

```python
from assured_sentinel import Settings, Commander
from assured_sentinel.core.scorer import BanditScorer
from assured_sentinel.models import ScoringConfig

# Custom scoring configuration
scoring_config = ScoringConfig(
    timeout_seconds=60,
    fail_closed=True,
    use_ramdisk=True,  # Performance optimization
)
scorer = BanditScorer(config=scoring_config)

# Custom commander
commander = Commander(scorer=scorer)
commander.threshold = 0.2  # Override threshold
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=assured_sentinel --cov-report=term-missing --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Type checking
mypy assured_sentinel/

# Linting
ruff check assured_sentinel/ tests/
```

---

## 📈 Evaluation Results

### Acceptance Rate vs. Risk Tolerance (α)

| α (Risk Tolerance) | Acceptance Rate | Unsafe Accept Bound | False Reject Rate |
|-------------------|-----------------|---------------------|-------------------|
| 0.05 | 70% | ≤5% | 30% |
| **0.10** | **80%** | **≤10%** | **20%** |
| 0.20 | 90% | ≤20% | 10% |

### Severity Breakdown

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

### The Statistical Guarantee

$$P(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$$

Where:
- $\alpha$ = risk tolerance (default: 0.10)
- $C(X)$ = conformity set (accepted code with score ≤ q̂)
- $Y_{n+1}$ = new code sample's scanner score

### ⚠️ What Is Guaranteed vs. Not Guaranteed

| ✅ Guaranteed | ❌ Not Guaranteed |
|--------------|-------------------|
| Statistical coverage on *scanner-defined* scores | Absence of all vulnerabilities |
| Bounded false acceptance rate *w.r.t. Bandit findings* | Robustness to distribution shift |
| Reproducible, deterministic decisions | Semantic security or logical correctness |
| Finite-sample validity | Protection against adversarial evasion |

---

## 🚦 Design Principles

This project follows **SOLID principles**:

| Principle | Implementation |
|-----------|----------------|
| **S**ingle Responsibility | Separate classes for scoring, verification, calibration |
| **O**pen/Closed | Protocols allow new scorers without modifying Commander |
| **L**iskov Substitution | All scorers implement `IScoringService` protocol |
| **I**nterface Segregation | Small, focused protocols (`IScoringService`, `IVerifier`, etc.) |
| **D**ependency Inversion | Commander depends on abstractions, not concrete scorers |

---

## 📊 Roadmap

### Phase 1: MVP ✅
- [x] Analyst/Commander two-agent pattern
- [x] Bandit-based deterministic scoring
- [x] MBPP calibration with synthetic injection
- [x] Streamlit dashboard
- [x] Correction loop (retry on rejection)

### Phase 2: Refactoring ✅ (v2.0)
- [x] SOLID principles implementation
- [x] Protocol-based interfaces
- [x] Pydantic models and settings
- [x] Custom exception hierarchy
- [x] Comprehensive test suite (90%+ coverage target)
- [x] Dependency injection

### Phase 3: Production Hardening (Planned)
- [ ] Multi-signal scoring (Semgrep, secret scanning)
- [ ] CI/CD integration (GitHub Actions, Azure DevOps)
- [ ] Drift monitoring & auto-recalibration
- [ ] API endpoint for enterprise integration

See [Roadmap](docs/Roadmap.md) for detailed milestones.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/ -v`)
4. Run type checks (`mypy assured_sentinel/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pre-commit install
```

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
  <b>Assured Sentinel v2.0</b><br>
  <i>Deterministic safety for stochastic systems.</i>
</p>
