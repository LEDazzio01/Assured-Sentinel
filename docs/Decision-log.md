# Decision Log

## Assured Sentinel: Key Technical & Product Decisions

**Version:** 1.0  
**Last Updated:** January 2026

---

## Purpose

This document records significant decisions made during the development of Assured Sentinel, including context, alternatives considered, and rationale. This serves as institutional memory and helps future contributors understand *why* the system is designed this way.

---

## Decision Template

```
### D-XXX: [Decision Title]
**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded
**Context:** What situation prompted this decision?
**Decision:** What was decided?
**Alternatives:** What other options were considered?
**Rationale:** Why was this option chosen?
**Consequences:** What are the implications?
```

---

## Decisions

### D-001: Use Split Conformal Prediction for Risk Bounding

**Date:** 2025-12-15  
**Status:** Accepted

**Context:**  
We needed a method to provide statistical guarantees on the safety of AI-generated code. Traditional approaches (heuristics, Bayesian methods) either lack formal guarantees or require distributional assumptions.

**Decision:**  
Implement Split Conformal Prediction (SCP) to calibrate acceptance thresholds.

**Alternatives Considered:**
| Alternative | Pros | Cons |
|-------------|------|------|
| Heuristic thresholds | Simple | No statistical validity |
| Bayesian calibration | Principled | Requires prior specification |
| Cross-conformal | More efficient | More complex implementation |
| Full conformal | Theoretically optimal | Computationally expensive |

**Rationale:**
- SCP provides **distribution-free, finite-sample guarantees**
- Simple to implement (just quantile computation)
- Matches industry-standard conformal prediction literature
- Trade-off: requires held-out calibration set (acceptable for our use case)

**Consequences:**
- Must maintain calibration dataset
- Need to recalibrate when distribution shifts
- Guarantee is marginal (across all inputs), not conditional

---

### D-002: Use Bandit as Primary Scoring Tool

**Date:** 2025-12-18  
**Status:** Accepted

**Context:**  
We needed a deterministic, reproducible way to score Python code for security risk.

**Decision:**  
Use Bandit (Python SAST tool) as the non-conformity measure.

**Alternatives Considered:**
| Alternative | Pros | Cons |
|-------------|------|------|
| **Bandit** | Fast, Python-specific, well-maintained | Limited to Python; some evasion possible |
| Semgrep | Multi-language, customizable | Heavier; rule licensing |
| CodeQL | Deep analysis, GitHub native | Requires build; slow; complex setup |
| LLM self-review | Flexible | Non-deterministic; self-delusion risk |
| pylint security | Familiar | Not security-focused |

**Rationale:**
- **Deterministic**: Same input → same output (critical for reproducibility)
- **Fast**: <500ms per scan
- **Python-specific**: Optimized for our target language
- **Well-maintained**: Active community, regular updates
- **CLI-friendly**: Easy subprocess integration

**Consequences:**
- Python-only for MVP (acceptable)
- May miss some vulnerability classes (mitigate with multi-signal in Phase 3)
- Evasion possible with obfuscation (mitigate with red teaming)

---

### D-003: Fail-Closed on All Error Paths

**Date:** 2025-12-20  
**Status:** Accepted

**Context:**  
We needed to decide what happens when the scoring system encounters errors (parse failures, tool missing, timeouts).

**Decision:**  
Return maximum risk score (1.0) on any error, causing rejection.

**Alternatives Considered:**
| Alternative | Behavior | Risk |
|-------------|----------|------|
| **Fail-closed** | Error → 1.0 → Reject | May reject valid code |
| Fail-open | Error → 0.0 → Accept | May accept malicious code |
| Fail-indeterminate | Error → special status | Complicates downstream logic |
| Retry | Error → retry N times | Adds latency; may still fail |

**Rationale:**
- **Security-first principle**: Unknown = untrusted
- Better to false-reject than false-accept in security context
- Simple mental model: "If we can't verify it, we don't trust it"
- Matches industry best practices for security controls

**Consequences:**
- Some valid code with syntax edge cases may be rejected
- Users see rejection for "unparseable" rather than "insecure"
- Need clear error messaging to distinguish failure modes

**Implementation:**
```python
# In scorer.py
if not shutil.which("bandit"):
    return 1.0  # Tool missing → reject

if errors:  # Parse errors
    return 1.0  # Can't scan → reject

except Exception:
    return 1.0  # Any failure → reject
```

---

### D-004: Two-Agent Pattern (Analyst + Commander)

**Date:** 2025-12-16  
**Status:** Accepted

**Context:**  
We needed to decide the architecture for LLM code generation with security verification.

**Decision:**  
Implement a two-agent pattern where the Analyst (LLM) generates code and the Commander (deterministic) verifies it.

**Alternatives Considered:**
| Alternative | Pros | Cons |
|-------------|------|------|
| **Two-agent** | Clean separation; deterministic verification | Two components to maintain |
| Single agent self-review | Simpler | Self-delusion problem; LLMs bad at self-critique |
| Multi-agent debate | May improve quality | Complex; non-deterministic |
| Human-in-the-loop | High quality | Doesn't scale |

**Rationale:**
- **Separation of concerns**: Generation is stochastic, verification is deterministic
- **Prevents self-delusion**: LLM doesn't grade its own work
- **Auditable**: Deterministic scoring creates reproducible audit trail
- **Extensible**: Can swap Analyst or Commander independently

**Consequences:**
- Need to maintain two component interfaces
- Latency = LLM generation + local scoring
- Correction loop adds complexity but improves outcomes

---

### D-005: Default α = 0.10 (10% Risk Tolerance)

**Date:** 2025-12-22  
**Status:** Accepted

**Context:**  
We needed to choose a default risk tolerance level for the conformal prediction threshold.

**Decision:**  
Set α = 0.10 as the default, with user-configurable override.

**Alternatives Considered:**
| α Value | Acceptance Rate | Unsafe Accept Bound | Use Case |
|---------|----------------|---------------------|----------|
| 0.01 | ~50% | ≤1% | Extremely high stakes |
| 0.05 | ~70% | ≤5% | High security |
| **0.10** | ~80% | ≤10% | Balanced |
| 0.20 | ~90% | ≤20% | Productivity-focused |

**Rationale:**
- Balances productivity (80% acceptance) with safety (≤10% unsafe)
- Common choice in conformal prediction literature
- Easy to explain: "1 in 10 accepted may have issues"
- User can adjust based on their risk appetite

**Consequences:**
- ~20% of clean code is false-rejected
- Need to document that α=0.10 means 10% residual risk
- Provide slider in dashboard for experimentation

---

### D-006: MBPP Dataset for Calibration

**Date:** 2025-12-19  
**Status:** Accepted

**Context:**  
We needed a "ground truth" dataset of Python code for calibration.

**Decision:**  
Use MBPP (Mostly Basic Python Problems) test split + synthetic vulnerability injection.

**Alternatives Considered:**
| Dataset | Pros | Cons |
|---------|------|------|
| **MBPP** | Clean Python, MIT license, HuggingFace hosted | Basic problems; may not represent production code |
| HumanEval | More complex | Smaller; OpenAI license |
| SecurityEval | Security-focused | Specialized; not general purpose |
| Production logs | Most representative | Privacy; availability |
| Synthetic only | Full control | May not represent real distribution |

**Rationale:**
- MBPP provides clean baseline (mostly secure code)
- Synthetic injection (20%) ensures bad samples exist for threshold calculation
- MIT license allows unrestricted use
- Easy access via HuggingFace datasets

**Consequences:**
- Calibration may not perfectly match production distribution
- Need periodic recalibration for drift
- Synthetic injection ratio (20%) is a hyperparameter

---

### D-007: Score Mapping (LOW=0.1, MEDIUM=0.5, HIGH=1.0)

**Date:** 2025-12-21  
**Status:** Accepted

**Context:**  
We needed to map Bandit severity levels to our 0.0-1.0 non-conformity score.

**Decision:**  
Map severities as: Clean=0.0, LOW=0.1, MEDIUM=0.5, HIGH=1.0.

**Alternatives Considered:**
| Mapping | LOW | MEDIUM | HIGH | Pros | Cons |
|---------|-----|--------|------|------|------|
| **Current** | 0.1 | 0.5 | 1.0 | Intuitive; separates well | May over-penalize MEDIUM |
| Linear | 0.33 | 0.66 | 1.0 | Simple | Doesn't reflect risk distribution |
| Exponential | 0.04 | 0.2 | 1.0 | Emphasizes HIGH | May under-penalize MEDIUM |
| Binary | 0.0 | 0.0 | 1.0 | Simple | Ignores LOW/MEDIUM |

**Rationale:**
- LOW issues (e.g., weak random) are typically acceptable → 0.1 (below default threshold)
- MEDIUM issues (e.g., hardcoded passwords) warrant attention → 0.5 (above threshold)
- HIGH issues (e.g., code injection) must reject → 1.0 (always rejected)
- Clean code should pass → 0.0

**Consequences:**
- With default q̂ ≈ 0.15, LOW passes and MEDIUM/HIGH reject
- May need to revisit if MEDIUM severity false-positives are high
- Consider weighted combination if multiple findings exist

---

### D-008: Pickle for Threshold Persistence

**Date:** 2025-12-22  
**Status:** Accepted (with caveats)

**Context:**  
We needed a simple way to persist the calibrated threshold between runs.

**Decision:**  
Use Python pickle for `calibration_data.pkl`.

**Alternatives Considered:**
| Format | Pros | Cons |
|--------|------|------|
| **Pickle** | Simple, native, preserves types | Security risk if untrusted; Python-only |
| JSON | Human-readable, portable | Need serialization logic |
| YAML | Human-readable, nice syntax | Extra dependency |
| SQLite | Queryable, robust | Overkill for single value |
| Environment variable | Simple | Ephemeral; not persistent |

**Rationale:**
- Single-machine, single-user use case for MVP
- Pickle is simple and works for our data structure
- Security: file is locally generated, not from untrusted source

**Consequences:**
- Not portable across Python versions (acceptable for MVP)
- Consider JSON for Phase 3 API integration
- Document that pickle file should not be from untrusted source

---

### D-009: Correction Loop with Max Retries

**Date:** 2025-12-23  
**Status:** Accepted

**Context:**  
When code is rejected, should we give the LLM another chance?

**Decision:**  
Implement a correction loop with MAX_RETRIES=3, passing rejection feedback to the Analyst.

**Alternatives Considered:**
| Approach | Behavior | Pros | Cons |
|----------|----------|------|------|
| **Correction loop** | Retry with feedback | Improves success rate | More API calls; latency |
| Single shot | No retry | Simple; fast | May reject fixable code |
| Infinite retry | Keep trying | Eventually succeeds | Resource exhaustion |
| Human escalation | Ask user to fix | High quality | Doesn't scale |

**Rationale:**
- Many rejections are due to stylistic issues that LLM can fix
- Feedback helps LLM understand what's wrong
- 3 retries balances success rate with cost/latency
- After 3 failures, likely a fundamental issue

**Consequences:**
- Up to 3x API calls on rejection
- Need clear feedback format for LLM
- Abort after max retries with clear message

---

### D-010: Streamlit for Dashboard

**Date:** 2025-12-24  
**Status:** Accepted

**Context:**  
We needed a quick way to visualize the system for demos and debugging.

**Decision:**  
Use Streamlit for the interactive dashboard.

**Alternatives Considered:**
| Framework | Pros | Cons |
|-----------|------|------|
| **Streamlit** | Rapid dev, Python-native, widgets | Not production-grade UI |
| Gradio | ML-focused, simple | Less flexible layout |
| Flask + React | Production-ready | More dev effort |
| Jupyter | Interactive, familiar | Not a "dashboard" |
| CLI only | Simple | Not visual |

**Rationale:**
- MVP priority: speed of development
- Streamlit allows rapid iteration
- Good enough for demos and portfolio
- Can replace with production UI in Phase 3

**Consequences:**
- Dashboard is prototype-quality
- May need rewrite for production use
- Acceptable for portfolio/demo purposes

---

## Pending Decisions

### D-011: Multi-Signal Scoring Weights (Phase 3)
**Status:** Proposed

**Question:** How should we combine Bandit, Semgrep, and secret scanning scores?

**Options:**
1. Equal weights (0.33, 0.33, 0.33)
2. Learned weights from calibration
3. Max of all signals (conservative)
4. Weighted by false positive rate

---

### D-012: API Authentication Method (Phase 3)
**Status:** Proposed

**Question:** How should the REST API authenticate requests?

**Options:**
1. API keys
2. JWT tokens
3. OAuth2 / OIDC
4. mTLS

---

## Decision Review Process

1. **Propose**: Document decision in this log with "Proposed" status
2. **Discuss**: Review with stakeholders
3. **Decide**: Mark as "Accepted" or "Rejected"
4. **Implement**: Build the chosen approach
5. **Review**: Revisit if circumstances change
