"""
Pydantic models for Assured Sentinel.

This module defines data transfer objects (DTOs) with validation
for all data structures used throughout the application.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    """Verification decision status."""
    
    PASS = "PASS"
    REJECT = "REJECT"


class Severity(str, Enum):
    """Security issue severity levels."""
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class VerificationResult(BaseModel):
    """
    Result of code verification.
    
    Attributes:
        status: PASS if code is accepted, REJECT otherwise.
        score: Non-conformity score from 0.0 to 1.0.
        threshold: Calibrated threshold (q̂) used for decision.
        reason: Human-readable explanation of the decision.
        latency_ms: Time taken for verification in milliseconds.
    """
    
    status: VerificationStatus
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    threshold: Annotated[float, Field(ge=0.0, le=1.0)]
    reason: str = ""
    latency_ms: float | None = None
    
    @property
    def passed(self) -> bool:
        """Returns True if verification passed."""
        return self.status == VerificationStatus.PASS
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "score": self.score,
            "threshold": self.threshold,
            "reason": self.reason,
            "latency_ms": self.latency_ms,
        }


class SecurityIssue(BaseModel):
    """
    A security issue found during code analysis.
    
    Attributes:
        test_id: Bandit test ID (e.g., B102).
        severity: Issue severity level.
        confidence: Confidence level of the finding.
        description: Human-readable description.
        line_number: Line where the issue was found.
    """
    
    test_id: str
    severity: Severity
    confidence: str = "MEDIUM"
    description: str = ""
    line_number: int | None = None


class ScoringResult(BaseModel):
    """
    Result of code scoring.
    
    Attributes:
        score: Overall risk score from 0.0 to 1.0.
        issues: List of security issues found.
        error: Error message if scoring failed.
    """
    
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    issues: list[SecurityIssue] = Field(default_factory=list)
    error: str | None = None
    
    @property
    def has_issues(self) -> bool:
        """Returns True if any security issues were found."""
        return len(self.issues) > 0


class CalibrationData(BaseModel):
    """
    Calibration data from Split Conformal Prediction.
    
    Attributes:
        q_hat: Calibrated threshold.
        alpha: Risk tolerance used during calibration.
        n_samples: Number of samples used for calibration.
        scores: Raw scores from calibration set.
        dataset: Name of the dataset used.
        dataset_hash: Hash for reproducibility tracking.
        scorer: Name of the scorer used.
        scorer_version: Version of the scorer.
        calibrated_at: Timestamp of calibration.
        notes: Additional notes about calibration.
    """
    
    q_hat: Annotated[float, Field(ge=0.0, le=1.0)]
    alpha: Annotated[float, Field(gt=0.0, lt=1.0)]
    n_samples: Annotated[int, Field(gt=0)]
    scores: list[float] = Field(default_factory=list)
    dataset: str = "unknown"
    dataset_hash: str = ""
    scorer: str = "bandit"
    scorer_version: str = "1.7+"
    calibrated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str = ""
    
    @field_validator("scores")
    @classmethod
    def validate_scores(cls, v: list[float]) -> list[float]:
        """Ensure all scores are in valid range."""
        for score in v:
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Score {score} not in range [0.0, 1.0]")
        return v


class ScoringConfig(BaseModel):
    """
    Configuration for scoring services.
    
    Attributes:
        timeout_seconds: Maximum time for scoring operation.
        fail_closed: If True, return 1.0 on any error.
        use_ramdisk: If True, use ramdisk for temp files.
        ramdisk_path: Path to ramdisk mount.
    """
    
    timeout_seconds: int = 30
    fail_closed: bool = True
    use_ramdisk: bool = False
    ramdisk_path: Path = Path("/dev/shm/sentinel")


class VerificationConfig(BaseModel):
    """
    Configuration for verification services.
    
    Attributes:
        default_threshold: Fallback threshold if calibration not found.
        calibration_path: Path to calibration data file.
    """
    
    default_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.15
    calibration_path: Path = Path("calibration_data.json")


class CalibrationConfig(BaseModel):
    """
    Configuration for calibration.
    
    Attributes:
        alpha: Risk tolerance (e.g., 0.1 for 10% error rate).
        n_samples: Number of samples to use for calibration.
        injection_rate: Rate of synthetic vulnerability injection.
        output_path: Path to save calibration results.
    """
    
    alpha: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.1
    n_samples: Annotated[int, Field(gt=0)] = 100
    injection_rate: Annotated[float, Field(ge=0.0, le=1.0)] = 0.2
    output_path: Path = Path("calibration_data.json")


class AnalystConfig(BaseModel):
    """
    Configuration for code generation agents.
    
    Attributes:
        temperature: LLM temperature for generation.
        top_p: Top-p sampling parameter.
        max_tokens: Maximum tokens in response.
        timeout_seconds: Request timeout.
    """
    
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.8
    top_p: Annotated[float, Field(gt=0.0, le=1.0)] = 0.95
    max_tokens: int = 2048
    timeout_seconds: int = 60
