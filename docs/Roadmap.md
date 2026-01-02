# Roadmap

## Assured Sentinel: Development Phases

**Version:** 1.0  
**Last Updated:** January 2026

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ASSURED SENTINEL ROADMAP                        │
├───────────────┬───────────────────┬───────────────────┬─────────────────┤
│    Phase 1    │      Phase 2      │      Phase 3      │    Phase 4      │
│     MVP       │    Validation     │    Production     │   Enterprise    │
│   (COMPLETE)  │   (IN PROGRESS)   │    (PLANNED)      │    (FUTURE)     │
├───────────────┼───────────────────┼───────────────────┼─────────────────┤
│ • Core arch   │ • Benchmarks      │ • Multi-signal    │ • Multi-tenant  │
│ • Bandit NCM  │ • Adversarial     │ • CI/CD API       │ • SaaS offering │
│ • SCP calib   │ • Multi-α test    │ • Drift detect    │ • Custom rules  │
│ • Dashboard   │ • Documentation   │ • Containers      │ • Analytics     │
└───────────────┴───────────────────┴───────────────────┴─────────────────┘
```

---

## Phase 1: MVP ✅ COMPLETE

**Goal:** Demonstrate core conformal prediction architecture with working prototype

### Deliverables

| Feature | Status | Description |
|---------|--------|-------------|
| Two-Agent Pattern | ✅ Done | Analyst (generator) + Commander (verifier) |
| Deterministic Scorer | ✅ Done | Bandit-based NCM scoring (0.0-1.0) |
| SCP Calibration | ✅ Done | MBPP dataset + synthetic injection |
| Fail-Closed Logic | ✅ Done | Errors return max risk score |
| Threshold Loading | ✅ Done | PKL persistence with fallback |
| Correction Loop | ✅ Done | Retry on rejection with feedback |
| Streamlit Dashboard | ✅ Done | Interactive visualization |
| Basic Documentation | ✅ Done | README with architecture overview |

### Exit Criteria
- [x] End-to-end verification works
- [x] Calibration produces valid threshold
- [x] Dashboard visualizes score distribution
- [x] Fail-closed behavior verified

---

## Phase 2: Validation 🔄 IN PROGRESS

**Goal:** Establish quantitative credibility with benchmarks and stress testing

### Deliverables

| Feature | Status | Description |
|---------|--------|-------------|
| Multi-Dataset Benchmark | ⏳ Planned | MBPP, HumanEval, SecurityEval |
| Adversarial Testing | ⏳ Planned | Evasion prompts, obfuscation |
| Multi-α Analysis | ⏳ Planned | α ∈ {0.01, 0.05, 0.10, 0.20} |
| Latency Profiling | ⏳ Planned | P50/P95/P99 measurements |
| **Real-World Vulnerability Calibration** | ⏳ Planned | Replace synthetic injection with CVE-based ground truth (see below) |
| Offline Demo | ✅ Done | Works without API key |
| Principal Docs | ✅ Done | PRD, Architecture, Risks, Roadmap |
| CI Pipeline | ✅ Done | Lint + test on PR |
| Unit Tests | ✅ Done | Scorer edge cases covered |

### Real-World Vulnerability Calibration Strategy

The current synthetic vulnerability injection (20% of calibration samples) provides a controlled baseline but does not represent real-world vulnerability distributions. Phase 2 will implement a more rigorous calibration data strategy:

**Approach: GitHub CVE Commit Mining**
```
1. Query GitHub Advisory Database for Python CVEs (2020-2025)
2. Extract commit SHAs that fixed each CVE
3. Use git diff to isolate vulnerable code (pre-fix) vs. patched code
4. Label: pre-fix = vulnerable (true positive), post-fix = clean
5. Score both versions with Bandit to validate detection capability
```

**Target Dataset:**
| Source | Expected Samples | Label |
|--------|------------------|-------|
| MBPP (clean) | 500 | Safe |
| CVE fixes (pre-patch) | 200 | Vulnerable (true positive) |
| CVE fixes (post-patch) | 200 | Safe (verified fix) |
| SecurityEval | 100 | Mixed (ground truth labels) |

**Benefits:**
- Real vulnerabilities, not synthetic patterns
- Ground truth labels from CVE database
- Measures actual Bandit detection capability (not circular reasoning)
- Enables precision/recall reporting, not just acceptance rate

**Risks:**
- CVE dataset may be biased toward detectable vulnerabilities
- Commit context may be incomplete
- Mitigation: Supplement with manual security review on sample

### Exit Criteria
- [ ] Benchmark table with ≥3 α values
- [ ] Adversarial prompt success rate documented
- [x] Demo runs in <60 seconds
- [x] Documentation passes Principal-level review

### Metrics to Report
| Metric | Target |
|--------|--------|
| Acceptance rate @ α=0.10 | ≥80% |
| Unsafe accept rate | ≤α |
| False reject rate | <25% |
| P50 latency | <500ms |

---

## Phase 3: Production Hardening 📋 PLANNED

**Goal:** Make system production-ready for enterprise CI/CD integration

### Deliverables

| Feature | Priority | Description |
|---------|----------|-------------|
| Multi-Signal Scoring | P0 | Add Semgrep, secret scanning |
| REST API | P0 | FastAPI endpoint for verification |
| Docker Container | P0 | Reproducible deployment |
| Drift Detection | P1 | Monitor calibration validity |
| Auto-Recalibration | P1 | Scheduled threshold updates |
| Structured Logging | P1 | JSON logs for SIEM integration |
| Rate Limiting | P2 | Protect API from abuse |
| Webhook Integration | P2 | GitHub/GitLab PR comments |

### Exit Criteria
- [ ] API handles 100 req/s
- [ ] Multi-signal improves detection by >20%
- [ ] Drift detected within 1 hour
- [ ] Container passes security scan

### Architecture Updates
```
Phase 3 Architecture:

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CI/CD      │────▶│  REST API   │────▶│  Commander  │
│  Pipeline   │     │  (FastAPI)  │     │  (Verify)   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │Multi-Signal │
                                        │   Scorer    │
                                        ├─────────────┤
                                        │ • Bandit    │
                                        │ • Semgrep   │
                                        │ • Secrets   │
                                        └─────────────┘
```

---

## Phase 4: Enterprise 🔮 FUTURE

**Goal:** Scale to multi-tenant SaaS offering with advanced features

### Potential Features

| Feature | Description |
|---------|-------------|
| Multi-Tenant | Isolated calibrations per org |
| Custom Rules | User-defined scoring patterns |
| Analytics Dashboard | Historical trends, anomaly detection |
| SSO Integration | SAML/OIDC for enterprise auth |
| Compliance Reports | SOC2, HIPAA audit artifacts |
| Multi-Language | JavaScript, Go, Java support |
| Model Fine-Tuning | Custom LLM for domain-specific code |

### Business Model Considerations
| Tier | Features |
|------|----------|
| Free | Open source, self-hosted |
| Team | Managed API, 10k verifications/month |
| Enterprise | Unlimited, custom calibration, SLA |

---

## Timeline (Estimated)

```
Q1 2026                Q2 2026                Q3 2026                Q4 2026
├──────────────────────┼──────────────────────┼──────────────────────┤
│                      │                      │                      │
│  Phase 1 ✅          │  Phase 2 ────────────│                      │
│  (Complete)          │  (Validation)        │  Phase 3 ────────────│
│                      │                      │  (Production)        │
│                      │                      │                      │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## Success Metrics by Phase

| Phase | Primary KPI | Target |
|-------|-------------|--------|
| 1 (MVP) | Working prototype | ✅ Achieved |
| 2 (Validation) | Benchmark credibility | Tables + plots |
| 3 (Production) | Enterprise readiness | 100 req/s API |
| 4 (Enterprise) | Revenue/adoption | N/A (future) |

---

## Dependencies & Risks by Phase

### Phase 2 Dependencies
- Access to HumanEval, SecurityEval datasets
- Adversarial prompt corpus

### Phase 3 Dependencies
- Semgrep rule licensing
- Container registry access
- Cloud infrastructure for API hosting

### Phase 4 Dependencies
- Business development
- Legal review for SaaS terms
- Security audit

---

## How to Contribute

### Phase 2 Contributions Welcome
- [ ] Add HumanEval benchmark script
- [ ] Create adversarial prompt test cases
- [ ] Improve documentation with examples

### Phase 3 Contributions Welcome
- [ ] FastAPI endpoint implementation
- [ ] Dockerfile creation
- [ ] Semgrep integration

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
