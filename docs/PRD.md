# Product Requirements Document (PRD)

## Assured Sentinel: Probabilistic Guardrails for AI-Generated Code

**Version:** 1.0  
**Author:** LEDazzio01  
**Last Updated:** January 2026  

---

## 1. Problem Statement

### The Challenge
Large Language Models (LLMs) are increasingly used to generate code, but their outputs are inherently stochastic and cannot self-assess their own security posture. This creates a critical gap:

- **Developers** want to ship LLM-generated code quickly
- **Security teams** need provable bounds on risk exposure
- **Static analysis** alone is brittle (false positives frustrate developers; false negatives expose vulnerabilities)

### The Gap
There is no production-ready system that provides **mathematically-bounded risk guarantees** for AI-generated code acceptance decisions.

---

## 2. Target Users

| Persona | Need | Current Workaround |
|---------|------|-------------------|
| **Platform Engineers** | Integrate AI coding assistants safely | Manual review (doesn't scale) |
| **Security Teams** | Bound risk exposure quantifiably | Block all AI-generated code (hurts productivity) |
| **DevOps/SRE** | Automate secure code deployment | Trust and pray |
| **Compliance Officers** | Audit trail for code acceptance | None |

### Primary User Story
> *"As a Security Engineer, I want to deploy an AI coding assistant with a guarantee that no more than 10% of accepted code will have HIGH severity vulnerabilities, so I can enable developer productivity without unquantified risk."*

---

## 3. Solution Overview

### Core Mechanism
**Split Conformal Prediction (SCP)** applied to code security scoring:

1. **Calibrate** a threshold (q̂) from a labeled dataset of code samples
2. **Score** incoming code with deterministic static analysis (Bandit)
3. **Decide** accept/reject based on score vs. threshold
4. **Guarantee** that the false acceptance rate is bounded by α

### Key Insight
Unlike traditional ML, SCP provides **finite-sample, distribution-free guarantees**. This means we can make statistically valid claims without requiring:
- Large datasets
- Distributional assumptions
- Bayesian priors

---

## 4. Product Requirements

### 4.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-1 | Score Python code snippets deterministically (0.0-1.0) | P0 | ✅ Done |
| FR-2 | Calibrate threshold from labeled dataset | P0 | ✅ Done |
| FR-3 | Accept/reject decision with confidence bound | P0 | ✅ Done |
| FR-4 | Fail-closed on unparseable/un-scannable code | P0 | ✅ Done |
| FR-5 | Interactive dashboard for visualization | P1 | ✅ Done |
| FR-6 | Correction loop (retry on rejection) | P1 | ✅ Done |
| FR-7 | Multi-signal scoring (Semgrep, secrets) | P2 | ⏳ Planned |
| FR-8 | API endpoint for CI/CD integration | P2 | ⏳ Planned |
| FR-9 | Drift detection and auto-recalibration | P3 | ⏳ Planned |

### 4.2 Non-Functional Requirements

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-1 | Latency per verification | <500ms | ✅ Met |
| NFR-2 | False acceptance rate | ≤α (configurable) | ✅ Met |
| NFR-3 | Reproducibility | Same input → same score | ✅ Met |
| NFR-4 | Offline operation | No external API for scoring | ✅ Met |

---

## 5. Non-Goals

The following are explicitly **out of scope** for v1.0:

| Non-Goal | Rationale |
|----------|-----------|
| Fixing generated code | We verify, not repair (separation of concerns) |
| Multi-language support | Python-only for MVP; extensible architecture |
| Real-time training | Calibration is batch; recalibrate periodically |
| Vulnerability classification | We score risk, not categorize CWEs |
| Replacing human review | Augments, not replaces security review |

---

## 6. Success Metrics

### Primary KPIs

| Metric | Definition | Target | Measurement |
|--------|------------|--------|-------------|
| **Unsafe Accept Rate** | % of accepted code with HIGH severity issues | ≤α | Benchmark on held-out set |
| **Acceptance Rate** | % of clean code that is accepted | ≥80% at α=0.10 | Benchmark on MBPP |
| **Latency** | P50 verification time | <500ms | Instrumentation |
| **Adoption** | Teams using the guardrail | N/A (portfolio project) | - |

### Secondary KPIs

| Metric | Definition | Target |
|--------|------------|--------|
| False Reject Rate | Clean code incorrectly rejected | <20% |
| Calibration Stability | q̂ variance across recalibrations | <0.05 |
| Developer NPS | Satisfaction with guardrail | >0 (not blocking) |

---

## 7. Competitive Analysis

| Solution | Approach | Limitation |
|----------|----------|------------|
| **Bandit alone** | Static rules | No risk quantification |
| **Semgrep** | Pattern matching | No probabilistic bounds |
| **CodeQL** | Dataflow analysis | Requires build; slow |
| **LLM self-review** | Ask model to check itself | Self-delusion problem |
| **Human review** | Manual inspection | Doesn't scale |
| **Assured Sentinel** | Conformal Prediction | ✅ Bounded risk guarantees |

---

## 8. Risks & Mitigations

See [Risks.md](Risks.md) for the full risk register.

---

## 9. Roadmap

See [Roadmap.md](Roadmap.md) for detailed phased milestones.

---

## 10. Open Questions

| Question | Status | Notes |
|----------|--------|-------|
| What α should be the default? | Resolved | 0.10 (balances safety vs. productivity) |
| Should we support multi-file analysis? | Open | Complexity vs. accuracy tradeoff |
| How often should we recalibrate? | Open | Depends on drift detection |
| Should we weight Bandit severities differently? | Open | Current: HIGH=1.0, MED=0.5, LOW=0.1 |

---

## Appendix: User Flows

### Flow 1: One-Shot Verification
```
User → Code Snippet → Scorer → Score → Commander → Accept/Reject
```

### Flow 2: Correction Loop
```
User → Query → Analyst → Code → Commander → Reject → Feedback → Analyst → ...
                                    ↓
                                  Accept → User
```

### Flow 3: Calibration
```
Dataset → Scorer → Scores[] → Quantile(1-α) → q̂ → Save to PKL
```
