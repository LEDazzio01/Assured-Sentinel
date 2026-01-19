# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Multi-signal scoring (Semgrep, secret scanning)
- CI/CD integration templates
- Drift monitoring & auto-recalibration
- REST API endpoint

---

## [2.0.0] - 2024-01-XX

### 🚀 Major Refactoring Release

Complete architectural overhaul following SOLID principles and enterprise Python best practices.

### Added

#### Package Structure
- New `assured_sentinel/` package with proper module organization
- `assured_sentinel.core` - Core business logic (scorer, commander, calibrator)
- `assured_sentinel.agents` - LLM integration (analyst)
- `assured_sentinel.cli` - Command-line interface
- `assured_sentinel.dashboard` - Streamlit UI

#### Protocol Interfaces (ISP/DIP)
- `IScoringService` - Abstract interface for security scoring
- `ICodeSanitizer` - Interface for code preprocessing
- `IVerifier` - Interface for verification gate
- `ICodeGenerator` - Interface for LLM code generation
- `ICalibrationStore` - Interface for calibration data persistence
- `ICalibrator` - Interface for calibration computation
- `ITempFileManager` - Interface for temporary file handling
- `IDatasetLoader` - Interface for dataset loading

#### Pydantic Models
- `VerificationResult` - Strongly-typed verification output
- `VerificationStatus` - Enum for PASS/REJECT/ERROR
- `Severity` - Enum for CLEAN/LOW/MEDIUM/HIGH
- `SecurityIssue` - Structured security finding
- `ScoringResult` - Scoring output with issues
- `CalibrationData` - Calibration state model
- `ScoringConfig` - Scorer configuration
- `VerificationConfig` - Commander configuration
- `CalibrationConfig` - Calibrator configuration
- `AnalystConfig` - Analyst configuration

#### Pydantic Settings
- `Settings` class with `SENTINEL_` prefix for environment variables
- Centralized configuration management
- Default values with environment override
- Azure OpenAI credentials handling

#### Custom Exceptions
- `SentinelError` - Base exception class
- `ScoringError` hierarchy:
  - `BanditNotFoundError` - Bandit not installed
  - `BanditParseError` - Invalid Bandit output
  - `ScoringTimeoutError` - Scoring timeout exceeded
- `CalibrationError` hierarchy:
  - `CalibrationFileNotFoundError` - Missing calibration file
  - `DatasetLoadError` - Dataset loading failed
  - `InsufficientSamplesError` - Not enough calibration samples
- `AnalystError` hierarchy:
  - `LLMConnectionError` - Azure OpenAI connection failed
  - `MissingCredentialsError` - Missing API credentials
- `VerificationError` - Verification process failed
- `ConfigurationError` - Invalid configuration

#### CLI Improvements
- `sentinel verify` - Verify code snippets or files
- `sentinel calibrate` - Run calibration process
- `sentinel demo` - Run offline demonstration
- `sentinel scan` - Scan directories recursively
- `sentinel run` - Run LLM correction loop
- JSON output mode for CI/CD integration
- Threshold override option

#### Testing Infrastructure
- `tests/conftest.py` - Shared pytest fixtures
- `tests/unit/` - Comprehensive unit tests
- `tests/integration/` - End-to-end tests
- Mock fixtures for Bandit output
- Temporary file fixtures for integration tests
- Target: 90%+ code coverage

#### Documentation
- Updated README with new architecture
- CHANGELOG following Keep a Changelog format
- CLI usage documentation
- Configuration documentation

### Changed

#### Dependency Injection
- `Commander` now accepts `IScoringService` via constructor
- `Commander` accepts `ICalibrationStore` for calibration persistence
- `BanditScorer` accepts `ICodeSanitizer` and `ITempFileManager`
- `CalibrationRunner` accepts `IDatasetLoader` and `IScoringService`

#### Type Safety
- Full type annotations throughout codebase
- Pydantic validation for all data transfer objects
- Runtime-checkable protocols for interface verification
- `VerificationResult` replaces tuple returns

#### Error Handling
- Custom exception hierarchy replaces generic exceptions
- Structured error messages with context
- Fail-closed behavior on parse errors (score = 1.0)
- Graceful degradation with meaningful error messages

#### Code Organization
- Single Responsibility: Separate classes for each concern
- Open/Closed: New scorers via protocol implementation
- Liskov Substitution: All implementations are substitutable
- Interface Segregation: Small, focused protocols
- Dependency Inversion: High-level modules depend on abstractions

### Deprecated

#### Legacy Files (will be removed in 3.0)
- `scorer.py` - Use `assured_sentinel.core.scorer`
- `commander.py` - Use `assured_sentinel.core.commander`
- `calibration.py` - Use `assured_sentinel.core.calibrator`
- `analyst.py` - Use `assured_sentinel.agents.analyst`
- `dashboard.py` - Use `assured_sentinel.dashboard.app`
- `demo.py` - Use `sentinel demo` CLI command
- `run_day4.py` - Use `sentinel run` CLI command
- `run_day5.py` - Use `sentinel run` CLI command

### Removed

- Pickle support for calibration data (security concern)
- Global mutable state
- Implicit dependencies

### Security

- Removed pickle deserialization (CWE-502 mitigation)
- Added input validation on all public APIs
- Fail-closed on unparseable code
- Secure temporary file handling with cleanup

### Migration Guide

#### From 1.x to 2.0

**Imports:**
```python
# Before (1.x)
from commander import Commander
from scorer import calculate_score

# After (2.0)
from assured_sentinel import Commander
from assured_sentinel.core.scorer import BanditScorer
```

**Verification:**
```python
# Before (1.x)
commander = Commander()
accept, score = commander.verify(code)

# After (2.0)
commander = Commander()
result = commander.verify(code)
accept = result.status == VerificationStatus.PASS
score = result.score
```

**Configuration:**
```python
# Before (1.x)
commander.threshold = 0.2

# After (2.0)
from assured_sentinel.config import Settings
settings = Settings(default_threshold=0.2)
# Or via environment: SENTINEL_DEFAULT_THRESHOLD=0.2
```

**Custom Scorer:**
```python
# Before (1.x) - Not possible

# After (2.0)
from assured_sentinel.protocols import IScoringService
from assured_sentinel.models import ScoringResult

class CustomScorer(IScoringService):
    def score(self, code: str) -> ScoringResult:
        # Your implementation
        return ScoringResult(score=0.0, issues=[])

commander = Commander(scorer=CustomScorer())
```

---

## [1.0.0] - 2024-01-XX

### Added

- Initial release
- Two-agent pattern (Analyst + Commander)
- Bandit-based security scoring
- Split Conformal Prediction calibration
- MBPP dataset calibration with synthetic vulnerability injection
- Streamlit dashboard
- LLM correction loop (retry on rejection)
- Azure OpenAI integration via Semantic Kernel
- Basic configuration via environment variables
- Demo mode for offline testing

### Technical Details

- Python 3.10+ required
- Semantic Kernel for LLM integration
- Bandit for SAST scoring
- MBPP dataset for calibration (200 samples)
- 20% synthetic vulnerability injection rate
- Default α = 0.10 (10% risk tolerance)

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 2.0.0 | TBD | SOLID refactoring, Pydantic models, comprehensive tests |
| 1.0.0 | TBD | Initial MVP with two-agent pattern |

---

[Unreleased]: https://github.com/LEDazzio01/Assured-Sentinel/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/LEDazzio01/Assured-Sentinel/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/LEDazzio01/Assured-Sentinel/releases/tag/v1.0.0
