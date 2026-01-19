"""
Unit tests for Pydantic models.

Tests validation, serialization, and model behavior.
"""

import pytest
from datetime import datetime

from assured_sentinel.models import (
    VerificationStatus,
    Severity,
    VerificationResult,
    SecurityIssue,
    ScoringResult,
    CalibrationData,
    ScoringConfig,
    VerificationConfig,
    CalibrationConfig,
    AnalystConfig,
)


class TestVerificationResult:
    """Tests for VerificationResult model."""
    
    def test_creates_pass_result(self):
        """Should create PASS result."""
        result = VerificationResult(
            status=VerificationStatus.PASS,
            score=0.0,
            threshold=0.15,
            reason="Clean",
        )
        
        assert result.status == VerificationStatus.PASS
        assert result.passed is True
    
    def test_creates_reject_result(self):
        """Should create REJECT result."""
        result = VerificationResult(
            status=VerificationStatus.REJECT,
            score=0.5,
            threshold=0.15,
            reason="Too risky",
        )
        
        assert result.status == VerificationStatus.REJECT
        assert result.passed is False
    
    def test_score_validation_lower_bound(self):
        """Should reject score < 0."""
        with pytest.raises(ValueError):
            VerificationResult(
                status=VerificationStatus.PASS,
                score=-0.1,
                threshold=0.15,
            )
    
    def test_score_validation_upper_bound(self):
        """Should reject score > 1."""
        with pytest.raises(ValueError):
            VerificationResult(
                status=VerificationStatus.PASS,
                score=1.5,
                threshold=0.15,
            )
    
    def test_to_dict(self):
        """Should convert to dictionary."""
        result = VerificationResult(
            status=VerificationStatus.PASS,
            score=0.0,
            threshold=0.15,
            reason="Clean",
            latency_ms=50.0,
        )
        
        d = result.to_dict()
        
        assert d["status"] == "PASS"
        assert d["score"] == 0.0
        assert d["latency_ms"] == 50.0


class TestSecurityIssue:
    """Tests for SecurityIssue model."""
    
    def test_creates_issue(self):
        """Should create security issue."""
        issue = SecurityIssue(
            test_id="B102",
            severity=Severity.MEDIUM,
            confidence="HIGH",
            description="Use of exec detected.",
            line_number=10,
        )
        
        assert issue.test_id == "B102"
        assert issue.severity == Severity.MEDIUM


class TestScoringResult:
    """Tests for ScoringResult model."""
    
    def test_creates_clean_result(self):
        """Should create result with no issues."""
        result = ScoringResult(score=0.0)
        
        assert result.score == 0.0
        assert result.has_issues is False
        assert len(result.issues) == 0
    
    def test_creates_result_with_issues(self):
        """Should create result with issues."""
        issues = [
            SecurityIssue(test_id="B102", severity=Severity.MEDIUM),
        ]
        result = ScoringResult(score=0.5, issues=issues)
        
        assert result.has_issues is True
        assert len(result.issues) == 1


class TestCalibrationData:
    """Tests for CalibrationData model."""
    
    def test_creates_calibration_data(self):
        """Should create valid calibration data."""
        data = CalibrationData(
            q_hat=0.15,
            alpha=0.1,
            n_samples=100,
            scores=[0.0] * 100,
        )
        
        assert data.q_hat == 0.15
        assert data.alpha == 0.1
        assert data.n_samples == 100
    
    def test_validates_scores_range(self):
        """Should reject scores outside [0, 1]."""
        with pytest.raises(ValueError):
            CalibrationData(
                q_hat=0.15,
                alpha=0.1,
                n_samples=1,
                scores=[1.5],  # Invalid
            )
    
    def test_alpha_bounds(self):
        """Should reject alpha outside (0, 1)."""
        with pytest.raises(ValueError):
            CalibrationData(
                q_hat=0.15,
                alpha=0.0,  # Invalid - must be > 0
                n_samples=100,
            )
        
        with pytest.raises(ValueError):
            CalibrationData(
                q_hat=0.15,
                alpha=1.0,  # Invalid - must be < 1
                n_samples=100,
            )


class TestScoringConfig:
    """Tests for ScoringConfig model."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        config = ScoringConfig()
        
        assert config.timeout_seconds == 30
        assert config.fail_closed is True
        assert config.use_ramdisk is False


class TestVerificationConfig:
    """Tests for VerificationConfig model."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        config = VerificationConfig()
        
        assert config.default_threshold == 0.15


class TestCalibrationConfig:
    """Tests for CalibrationConfig model."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        config = CalibrationConfig()
        
        assert config.alpha == 0.1
        assert config.n_samples == 100
        assert config.injection_rate == 0.2


class TestAnalystConfig:
    """Tests for AnalystConfig model."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        config = AnalystConfig()
        
        assert config.temperature == 0.8
        assert config.top_p == 0.95
    
    def test_temperature_bounds(self):
        """Should validate temperature range."""
        # Valid
        AnalystConfig(temperature=0.0)
        AnalystConfig(temperature=2.0)
        
        # Invalid
        with pytest.raises(ValueError):
            AnalystConfig(temperature=-0.1)
        
        with pytest.raises(ValueError):
            AnalystConfig(temperature=2.1)
