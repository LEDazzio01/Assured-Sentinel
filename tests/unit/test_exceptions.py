"""
Unit tests for exception classes.

Tests exception hierarchy and message formatting.
"""

import pytest

from assured_sentinel.exceptions import (
    SentinelError,
    ScoringError,
    BanditNotFoundError,
    BanditExecutionError,
    BanditParseError,
    ScoringTimeoutError,
    CodeSyntaxError,
    CalibrationError,
    CalibrationFileNotFoundError,
    CalibrationFileCorruptError,
    DatasetLoadError,
    InsufficientSamplesError,
    AnalystError,
    LLMConnectionError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    MissingCredentialsError,
    VerificationError,
    ThresholdNotCalibratedError,
    ConfigurationError,
    InvalidConfigurationError,
)


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""
    
    def test_all_inherit_from_sentinel_error(self):
        """All exceptions should inherit from SentinelError."""
        exceptions = [
            ScoringError("test"),
            BanditNotFoundError(),
            CalibrationError("test"),
            AnalystError("test"),
            VerificationError("test"),
            ConfigurationError("test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, SentinelError)
    
    def test_scoring_exceptions_inherit_from_scoring_error(self):
        """Scoring exceptions should inherit from ScoringError."""
        exceptions = [
            BanditNotFoundError(),
            BanditExecutionError("test"),
            BanditParseError("test"),
            ScoringTimeoutError(30),
            CodeSyntaxError("test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, ScoringError)
    
    def test_calibration_exceptions_inherit_from_calibration_error(self):
        """Calibration exceptions should inherit from CalibrationError."""
        exceptions = [
            CalibrationFileNotFoundError("/path"),
            CalibrationFileCorruptError("/path"),
            DatasetLoadError("mbpp"),
            InsufficientSamplesError(100, 50),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, CalibrationError)
    
    def test_analyst_exceptions_inherit_from_analyst_error(self):
        """Analyst exceptions should inherit from AnalystError."""
        exceptions = [
            LLMConnectionError("Azure"),
            LLMAuthenticationError("Azure"),
            LLMRateLimitError("Azure"),
            LLMTimeoutError(60),
            MissingCredentialsError(["KEY"]),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, AnalystError)


class TestExceptionMessages:
    """Tests for exception message formatting."""
    
    def test_bandit_not_found_error_message(self):
        """BanditNotFoundError should have helpful message."""
        exc = BanditNotFoundError()
        
        assert "Bandit" in str(exc)
        assert "pip install bandit" in str(exc)
    
    def test_bandit_execution_error_includes_stderr(self):
        """BanditExecutionError should include stderr."""
        exc = BanditExecutionError("Failed", stderr="error details", return_code=1)
        
        assert "error details" in str(exc)
        assert exc.return_code == 1
    
    def test_scoring_timeout_error_includes_timeout(self):
        """ScoringTimeoutError should include timeout value."""
        exc = ScoringTimeoutError(30)
        
        assert "30" in str(exc)
        assert exc.timeout_seconds == 30
    
    def test_calibration_file_not_found_includes_path(self):
        """CalibrationFileNotFoundError should include path."""
        exc = CalibrationFileNotFoundError("/path/to/file.json")
        
        assert "/path/to/file.json" in str(exc)
        assert exc.path == "/path/to/file.json"
    
    def test_dataset_load_error_includes_dataset_name(self):
        """DatasetLoadError should include dataset name."""
        exc = DatasetLoadError("mbpp", "network error")
        
        assert "mbpp" in str(exc)
        assert "network error" in str(exc)
    
    def test_insufficient_samples_error(self):
        """InsufficientSamplesError should show required vs available."""
        exc = InsufficientSamplesError(required=100, available=50)
        
        assert "100" in str(exc)
        assert "50" in str(exc)
        assert exc.required == 100
        assert exc.available == 50
    
    def test_llm_connection_error_includes_provider(self):
        """LLMConnectionError should include provider name."""
        exc = LLMConnectionError("Azure OpenAI", "endpoint.com", "timeout")
        
        assert "Azure OpenAI" in str(exc)
        assert "endpoint.com" in str(exc)
    
    def test_llm_rate_limit_includes_retry_after(self):
        """LLMRateLimitError should include retry after."""
        exc = LLMRateLimitError("OpenAI", retry_after=60)
        
        assert "60" in str(exc)
        assert exc.retry_after == 60
    
    def test_missing_credentials_lists_missing_vars(self):
        """MissingCredentialsError should list missing vars."""
        exc = MissingCredentialsError(["API_KEY", "ENDPOINT"])
        
        assert "API_KEY" in str(exc)
        assert "ENDPOINT" in str(exc)
        assert exc.missing_vars == ["API_KEY", "ENDPOINT"]
    
    def test_invalid_configuration_error(self):
        """InvalidConfigurationError should include field info."""
        exc = InvalidConfigurationError("alpha", "2.0", "must be < 1")
        
        assert "alpha" in str(exc)
        assert "must be < 1" in str(exc)
