# Architecture Document

## Assured Sentinel: System Design

**Version:** 1.0  
**Last Updated:** January 2026

---

## 1. System Overview

Assured Sentinel implements a **two-agent pattern** with deterministic verification to provide bounded-risk guarantees for AI-generated code.

```
                                    ┌─────────────────────────────┐
                                    │      ASSURED SENTINEL       │
                                    │         SYSTEM              │
┌─────────┐                         │  ┌─────────────────────┐   │
│  User   │─── Query ──────────────▶│  │      Analyst        │   │
│         │                         │  │  (Code Generator)   │   │
└─────────┘                         │  │                     │   │
     ▲                              │  │  • Azure OpenAI     │   │
     │                              │  │  • High Temp (0.8)  │   │
     │                              │  │  • Semantic Kernel  │   │
     │                              │  └──────────┬──────────┘   │
     │                              │             │              │
     │                              │             ▼ Code         │
     │                              │  ┌─────────────────────┐   │
     │                              │  │     Commander       │   │
     │                              │  │   (Verification)    │   │
     │                              │  │                     │   │
     │                              │  │  • Scorer (Bandit)  │   │
     │                              │  │  • Threshold (q̂)    │   │
     │                              │  │  • Accept/Reject    │   │
     │                              │  └──────────┬──────────┘   │
     │                              │             │              │
     │                              └─────────────┼──────────────┘
     │                                            │
     │                                            ▼
     │                              ┌─────────────────────────┐
     └────── Accept/Reject ─────────│        Decision         │
                                    │  • status: PASS/REJECT  │
                                    │  • score: 0.0-1.0       │
                                    │  • threshold: q̂         │
                                    │  • reason: string       │
                                    └─────────────────────────┘
```

---

## 2. Component Details

### 2.1 Analyst (`analyst.py`)

**Purpose:** Generate candidate code solutions using LLM

| Attribute | Value |
|-----------|-------|
| LLM Provider | Azure OpenAI |
| Model | gpt-4o |
| Temperature | 0.8 (high entropy) |
| Framework | Semantic Kernel |

**Behavior:**
- Receives user query
- Generates creative, functional Python code
- Does NOT self-verify (that's Commander's job)

**Interface:**
```python
class Analyst:
    async def generate(self, user_request: str) -> str:
        """Returns generated Python code"""
```

---

### 2.2 Commander (`commander.py`)

**Purpose:** Verify code against calibrated safety threshold

| Attribute | Value |
|-----------|-------|
| Threshold Source | `calibration_data.pkl` |
| Default Threshold | 0.15 |
| Scoring Method | Bandit (deterministic) |

**Behavior:**
- Loads calibrated threshold (q̂) from pickle file
- Invokes Scorer to get non-conformity score
- Compares score ≤ threshold → PASS, else REJECT

**Interface:**
```python
class Commander:
    def __init__(self, calibration_file: str, default_threshold: float)
    def verify(self, code_snippet: str) -> dict:
        """Returns {status, score, threshold, reason}"""
```

**Decision Logic:**
```
IF score > threshold:
    REJECT (code is too "weird" relative to safe distribution)
ELSE:
    PASS (code conforms to safe distribution)
```

---

### 2.3 Scorer (`scorer.py`)

**Purpose:** Compute deterministic non-conformity score using Bandit

| Attribute | Value |
|-----------|-------|
| Tool | Bandit (Python SAST) |
| Score Range | 0.0 (secure) to 1.0 (high risk) |
| Fail Mode | Fail-closed (return 1.0 on errors) |

**Score Mapping:**
| Bandit Finding | Score |
|----------------|-------|
| No issues | 0.0 |
| LOW severity | 0.1 |
| MEDIUM severity | 0.5 |
| HIGH severity | 1.0 |
| Parse error | 1.0 (fail-closed) |
| Bandit not found | 1.0 (fail-closed) |

**Interface:**
```python
def calculate_score(code_snippet: str) -> float:
    """Returns 0.0-1.0 risk score"""
```

**Security Design:**
```python
# Fail-closed examples
if not shutil.which("bandit"):
    return 1.0  # Tool missing → reject

if errors:  # Parse errors
    return 1.0  # Can't scan → reject
    
except Exception:
    return 1.0  # Any failure → reject
```

---

### 2.4 Calibration (`calibration.py`)

**Purpose:** Establish threshold (q̂) from labeled dataset

**Algorithm:** Split Conformal Prediction
```
1. Load n samples from MBPP dataset
2. Score each sample with Scorer
3. Inject 20% synthetic vulnerabilities
4. Compute q̂ = quantile(scores, ⌈(n+1)(1-α)⌉/n)
5. Save q̂ to calibration_data.pkl
```

**Configuration:**
| Parameter | Default |
|-----------|---------|
| α (risk tolerance) | 0.10 |
| Calibration size | 100 samples |
| Synthetic injection | 20% |

---

## 3. Data Flow

### 3.1 Verification Flow (Runtime)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Code Snippet │────▶│    Scorer    │────▶│   Commander  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Temp File   │     │  Threshold   │
                     │   (*.py)     │     │    (q̂)       │
                     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     │
                     ┌──────────────┐             │
                     │   Bandit     │             │
                     │  Subprocess  │             │
                     └──────────────┘             │
                            │                     │
                            ▼                     │
                     ┌──────────────┐             │
                     │    Score     │─────────────┘
                     │  (0.0-1.0)   │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Decision   │
                     │ PASS/REJECT  │
                     └──────────────┘
```

### 3.2 Calibration Flow (One-Time)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  MBPP Data   │────▶│    Scorer    │────▶│   Scores[]   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  + Synthetic │
                                          │  Injection   │
                                          └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  Quantile    │
                                          │  Calculation │
                                          └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  q̂ → PKL    │
                                          └──────────────┘
```

### 3.3 Correction Loop (run_day5.py)

```
                    ┌─────────────────────────────────────┐
                    │          Correction Loop            │
                    │                                     │
                    │  ┌─────────┐                        │
 User Query ───────▶│  │ Attempt │                        │
                    │  │   1..N  │                        │
                    │  └────┬────┘                        │
                    │       │                             │
                    │       ▼                             │
                    │  ┌─────────┐     ┌─────────┐        │
                    │  │ Analyst │────▶│Commander│        │
                    │  └─────────┘     └────┬────┘        │
                    │                       │             │
                    │           ┌───────────┴──────────┐  │
                    │           ▼                      ▼  │
                    │      ┌────────┐            ┌───────┐│
                    │      │  PASS  │            │REJECT ││
                    │      └────┬───┘            └───┬───┘│
                    │           │                    │    │
                    │           ▼                    ▼    │
                    │      ┌────────┐         ┌─────────┐ │
                    │      │ Return │         │Feedback │ │
                    │      │  Code  │         │ Prompt  │ │
                    │      └────────┘         └────┬────┘ │
                    │                              │      │
                    │                              ▼      │
                    │                         [Next Loop] │
                    └─────────────────────────────────────┘
```

---

## 4. Sequence Diagram

```
┌──────┐          ┌────────┐          ┌─────────┐          ┌────────┐
│ User │          │Analyst │          │Commander│          │ Scorer │
└──┬───┘          └───┬────┘          └────┬────┘          └───┬────┘
   │                  │                    │                   │
   │  Query           │                    │                   │
   │─────────────────▶│                    │                   │
   │                  │                    │                   │
   │                  │ generate()         │                   │
   │                  │───────────┐        │                   │
   │                  │           │        │                   │
   │                  │◀──────────┘        │                   │
   │                  │ code               │                   │
   │                  │───────────────────▶│                   │
   │                  │                    │                   │
   │                  │                    │ calculate_score() │
   │                  │                    │──────────────────▶│
   │                  │                    │                   │
   │                  │                    │   score (0.0-1.0) │
   │                  │                    │◀──────────────────│
   │                  │                    │                   │
   │                  │                    │ compare(score, q̂) │
   │                  │                    │───────────┐       │
   │                  │                    │           │       │
   │                  │                    │◀──────────┘       │
   │                  │                    │                   │
   │                  │    decision        │                   │
   │                  │◀───────────────────│                   │
   │                  │                    │                   │
   │   PASS/REJECT    │                    │                   │
   │◀─────────────────│                    │                   │
   │                  │                    │                   │
```

---

## 5. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| LLM | Azure OpenAI (gpt-4o) | Enterprise-ready, consistent API |
| LLM Framework | Semantic Kernel | Async-first, prompt templating |
| Static Analysis | Bandit | Python-specific, deterministic, fast |
| Calibration | NumPy | Quantile computation |
| Dataset | HuggingFace Datasets | Easy access to MBPP |
| Dashboard | Streamlit | Rapid prototyping |
| Persistence | Pickle | Simple threshold storage |

---

## 6. Security Considerations

### 6.1 Fail-Closed Design
Every error path returns maximum risk score (1.0):
- Bandit not installed → 1.0
- Parse error → 1.0
- Subprocess failure → 1.0
- JSON decode error → 1.0

### 6.2 Input Sanitization
Code snippets are sanitized before scanning:
- Markdown code blocks stripped
- Written to temp file with `.py` extension
- Temp files deleted after scanning

### 6.3 No Remote Execution
Scoring is fully local:
- No code is sent to external APIs for security evaluation
- Only the LLM generation uses Azure OpenAI

---

## 7. Extensibility

### Adding New Scoring Signals
```python
# Future: Multi-signal scorer
def calculate_score(code: str) -> float:
    bandit_score = run_bandit(code)
    semgrep_score = run_semgrep(code)
    secret_score = run_secret_scan(code)
    
    # Weighted combination (weights calibrated separately)
    return 0.6 * bandit_score + 0.3 * semgrep_score + 0.1 * secret_score
```

### Adding New Languages
```python
# Future: Language-agnostic scorer
def calculate_score(code: str, language: str) -> float:
    if language == "python":
        return run_bandit(code)
    elif language == "javascript":
        return run_eslint_security(code)
    elif language == "go":
        return run_gosec(code)
```

---

## 8. Scalability Constraints

This section documents the throughput limits of the current architecture and defines trigger points for architectural evolution.

### 8.1 Current Architecture Limits

| Constraint | Current Limit | Bottleneck | Mitigation |
|------------|---------------|------------|------------|
| **Scoring Throughput** | ~100-200 req/s | Temp file I/O + subprocess spawn | Ramdisk or in-memory AST |
| **LLM Generation** | ~10-50 req/s | Azure OpenAI rate limits | Request pooling, caching |
| **Memory per Request** | ~50MB peak | Bandit AST parsing | Worker pool with limits |
| **Concurrent Sessions** | ~10-20 | Python GIL, single process | Multi-process workers |

### 8.2 Latency Breakdown (P50)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VERIFICATION LATENCY (~500ms)                     │
├──────────────────┬──────────────────┬──────────────────┬────────────┤
│ Code Sanitization│  Temp File I/O   │ Bandit Subprocess│   Cleanup  │
│      ~5ms        │     ~10ms        │     ~480ms       │    ~5ms    │
└──────────────────┴──────────────────┴──────────────────┴────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   Bandit Internal       │
                    ├─────────────────────────┤
                    │ Process spawn: ~50ms    │
                    │ File read:     ~5ms     │
                    │ AST parse:     ~100ms   │
                    │ Security scan: ~300ms   │
                    │ JSON output:   ~25ms    │
                    └─────────────────────────┘
```

### 8.3 Scale Trigger Points

| Threshold | Trigger | Recommended Action |
|-----------|---------|-------------------|
| **>100 req/s** | Temp file I/O saturation | Move to ramdisk (`/dev/shm`) |
| **>500 req/s** | Subprocess overhead | Migrate to in-memory Bandit API |
| **>1000 req/s** | Single-process limit | Deploy as microservice with worker pool |
| **>5000 req/s** | Single-node limit | Horizontal scaling + load balancer |
| **>10000 req/s** | Database/state bottleneck | Distributed calibration cache |

### 8.4 Production Architecture (Phase 3+)

```
                            ┌─────────────────────────────────────────┐
                            │           LOAD BALANCER                 │
                            │         (nginx / AWS ALB)               │
                            └───────────────┬─────────────────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────┐
              │                             │                         │
              ▼                             ▼                         ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│    Scorer Worker 1      │   │    Scorer Worker 2      │   │    Scorer Worker N      │
│  ┌───────────────────┐  │   │  ┌───────────────────┐  │   │  ┌───────────────────┐  │
│  │ In-Memory Bandit  │  │   │  │ In-Memory Bandit  │  │   │  │ In-Memory Bandit  │  │
│  │ + AST Cache       │  │   │  │ + AST Cache       │  │   │  │ + AST Cache       │  │
│  └───────────────────┘  │   │  └───────────────────┘  │   │  └───────────────────┘  │
└─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
              │                             │                         │
              └─────────────────────────────┼─────────────────────────┘
                                            │
                                            ▼
                            ┌─────────────────────────────────────────┐
                            │         REDIS CACHE                     │
                            │   (Calibration thresholds, metrics)     │
                            └─────────────────────────────────────────┘
```

### 8.5 Cost-Performance Trade-offs

| Architecture | Throughput | Latency (P50) | Monthly Cost (Est.) | Complexity |
|--------------|------------|---------------|---------------------|------------|
| Current (subprocess) | 100 req/s | 500ms | $0 (local) | Low |
| Ramdisk optimization | 500 req/s | 100ms | $0 (local) | Low |
| In-memory workers | 2000 req/s | 20ms | $50/mo (1 VM) | Medium |
| Microservice cluster | 10000 req/s | 50ms | $500/mo (3 VMs) | High |
| Serverless (Lambda) | Burst to 50k | 200ms | Pay-per-use | Medium |

---

## 9. Deployment Options

| Mode | Description | Use Case |
|------|-------------|----------|
| **CLI** | `python run_day5.py` | Development, testing |
| **Dashboard** | `streamlit run dashboard.py` | Interactive demos |
| **API** | FastAPI endpoint (planned) | CI/CD integration |
| **Container** | Docker image (planned) | Production deployment |
