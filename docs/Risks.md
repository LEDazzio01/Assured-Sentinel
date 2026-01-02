# Risk Register

## Assured Sentinel: Risk Analysis & Mitigations

**Version:** 1.0  
**Last Updated:** January 2026

---

## 1. Risk Matrix Overview

| Severity | Likelihood | Risk Level |
|----------|------------|------------|
| High | High | 🔴 Critical |
| High | Medium | 🟠 High |
| Medium | High | 🟠 High |
| Medium | Medium | 🟡 Medium |
| Low | Any | 🟢 Low |
| Any | Low | 🟢 Low |

---

## 2. Security Risks

### R-SEC-1: Evasion via Syntax Obfuscation
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟠 High |
| **Description** | Attacker crafts code that passes Bandit but contains vulnerabilities |
| **Example** | Using `__import__('os').system()` instead of direct `os.system()` |
| **Likelihood** | Medium |
| **Impact** | High (bypasses guardrail) |
| **Mitigation** | Multi-signal scoring (add Semgrep, CodeQL); red team testing |
| **Status** | ⏳ Planned for Phase 2 |

### R-SEC-2: Prompt Injection via Feedback Loop
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | Malicious code in rejection feedback could influence next generation |
| **Example** | Feedback contains "ignore previous instructions" |
| **Likelihood** | Low |
| **Impact** | Medium |
| **Mitigation** | Feedback is structured; LLM receives only sanitized context |
| **Status** | ✅ Addressed in design |

### R-SEC-3: Bandit Tool Unavailable
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟠 High |
| **Description** | If Bandit is not installed, scoring fails |
| **Likelihood** | Low (in deployed env) |
| **Impact** | Critical (no security scanning) |
| **Mitigation** | **Fail-closed**: Return score=1.0 if Bandit missing |
| **Status** | ✅ Implemented |

### R-SEC-4: Unparseable Code Bypasses Scanning
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🔴 Critical |
| **Description** | Malformed code that Bandit can't parse might get through |
| **Likelihood** | Medium |
| **Impact** | Critical |
| **Mitigation** | **Fail-closed**: Parse errors return score=1.0 |
| **Status** | ✅ Implemented |

---

## 3. Operational Risks

### R-OPS-1: Calibration Data Drift
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | MBPP calibration may not represent production code distribution |
| **Likelihood** | Medium |
| **Impact** | Medium (suboptimal threshold) |
| **Mitigation** | Periodic recalibration; drift monitoring |
| **Status** | ⏳ Planned for Phase 3 |

### R-OPS-2: Threshold Too Restrictive
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | High false reject rate frustrates developers |
| **Likelihood** | Medium |
| **Impact** | Low (productivity impact, not security) |
| **Mitigation** | Adjustable α; correction loop allows retries |
| **Status** | ✅ Addressed |

### R-OPS-3: Azure OpenAI Service Outage
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | LLM generation fails if Azure is unavailable |
| **Likelihood** | Low |
| **Impact** | Medium (feature unavailable) |
| **Mitigation** | Graceful error handling; offline demo mode |
| **Status** | ✅ Implemented |

### R-OPS-4: Pickle File Corruption
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟢 Low |
| **Description** | calibration_data.pkl corrupted or missing |
| **Likelihood** | Low |
| **Impact** | Low (falls back to default threshold) |
| **Mitigation** | Default threshold = 0.15; warning logged |
| **Status** | ✅ Implemented |

---

## 4. Technical Risks

### R-TECH-1: Single Scoring Signal Limitation
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | Bandit alone may miss certain vulnerability classes |
| **Likelihood** | High |
| **Impact** | Medium |
| **Mitigation** | Extensible scorer architecture; add Semgrep/secrets |
| **Status** | ⏳ Planned |

### R-TECH-2: Temp File Race Condition
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟢 Low |
| **Description** | Concurrent scoring could conflict on temp files |
| **Likelihood** | Low (unique temp names) |
| **Impact** | Low |
| **Mitigation** | Using tempfile.NamedTemporaryFile with unique names |
| **Status** | ✅ Addressed |

### R-TECH-3: Python-Only Limitation
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | System only scores Python code |
| **Likelihood** | N/A (by design for MVP) |
| **Impact** | Limited applicability |
| **Mitigation** | Extensible architecture for multi-language support |
| **Status** | ⏳ Planned for future |

---

## 5. Compliance Risks

### R-COMP-1: Audit Trail Requirements
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | Enterprise may require logs of all accept/reject decisions |
| **Likelihood** | High (enterprise use case) |
| **Impact** | Medium (compliance blocker) |
| **Mitigation** | Logging infrastructure; decision archival |
| **Status** | ⏳ Planned |

### R-COMP-2: Data Retention for Calibration
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟢 Low |
| **Description** | MBPP dataset usage may have licensing implications |
| **Likelihood** | Low (MIT licensed) |
| **Impact** | Low |
| **Mitigation** | Attribution in README; license compliance |
| **Status** | ✅ Addressed |

---

## 6. Business Risks

### R-BIZ-1: Over-Reliance on Guardrail
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟡 Medium |
| **Description** | Users may treat PASS as "guaranteed secure" |
| **Likelihood** | Medium |
| **Impact** | Medium |
| **Mitigation** | Clear documentation that this bounds risk, not eliminates it |
| **Status** | ✅ Addressed in docs |

### R-BIZ-2: False Sense of Security
| Attribute | Value |
|-----------|-------|
| **Risk Level** | 🟠 High |
| **Description** | α=10% means 1 in 10 accepted code may be unsafe |
| **Likelihood** | High (by design) |
| **Impact** | Depends on downstream use |
| **Mitigation** | Education; lower α for high-stakes environments |
| **Status** | ✅ Configurable α |

---

## 7. Mitigation Summary

| Category | Key Mitigations |
|----------|----------------|
| **Security** | Fail-closed on all errors; multi-signal roadmap |
| **Operational** | Default thresholds; graceful degradation |
| **Technical** | Extensible architecture; unique temp files |
| **Compliance** | Logging; attribution |
| **Business** | Clear documentation; adjustable α |

---

## 8. Risk Monitoring

### Metrics to Track
| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| False accept rate | >α | Investigate calibration drift |
| Parse error rate | >5% | Check input sanitization |
| Bandit timeout rate | >1% | Increase timeout; check code size |
| Scorer exceptions | Any | Investigate immediately |

### Review Cadence
- **Weekly**: Exception rates, scorer health
- **Monthly**: False accept/reject rates
- **Quarterly**: Full calibration review; threshold adjustment

---

## 9. Design Decisions Driven by Risk

| Risk | Decision |
|------|----------|
| R-SEC-3, R-SEC-4 | **Fail-closed** on all error paths |
| R-OPS-2 | **Correction loop** allows retries on rejection |
| R-TECH-1 | **Extensible scorer** architecture |
| R-BIZ-2 | **Configurable α** via slider/parameter |
