"""
Custom exceptions for Assured Sentinel.

This module defines a hierarchy of exceptions for proper error handling
throughout the application. All exceptions inherit from SentinelError.
"""


class SentinelError(Exception):
    """
    Base exception for all Assured Sentinel errors.
    
    All custom exceptions in this package inherit from this class,
    allowing users to catch all Sentinel-related errors with a single
    except clause if desired.
    """
    
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


# =============================================================================
# Scoring Exceptions
# =============================================================================

class ScoringError(SentinelError):
    """
    Base exception for scoring-related errors.
    
    Raised when code scoring fails for any reason.
    """
    pass


class BanditNotFoundError(ScoringError):
    """
    Raised when the Bandit executable is not found in PATH.
    
    This typically means Bandit is not installed or not accessible.
    Install with: pip install bandit
    """
    
    def __init__(self):
        super().__init__(
            "Bandit executable not found in PATH. "
            "Install with: pip install bandit"
        )


class BanditExecutionError(ScoringError):
    """
    Raised when Bandit fails to execute.
    
    Attributes:
        stderr: Error output from Bandit.
        return_code: Process return code.
    """
    
    def __init__(self, message: str, stderr: str = "", return_code: int = -1):
        self.stderr = stderr
        self.return_code = return_code
        super().__init__(f"{message}. stderr: {stderr}")


class BanditParseError(ScoringError):
    """
    Raised when Bandit output cannot be parsed.
    
    This can happen if the code has syntax errors or if
    Bandit's JSON output format changes.
    
    Attributes:
        raw_output: The unparseable output from Bandit.
    """
    
    def __init__(self, message: str, raw_output: str = ""):
        self.raw_output = raw_output
        super().__init__(f"{message}. Output: {raw_output[:200]}...")


class ScoringTimeoutError(ScoringError):
    """
    Raised when scoring operation exceeds timeout.
    
    Attributes:
        timeout_seconds: The timeout that was exceeded.
    """
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Scoring timed out after {timeout_seconds} seconds")


class CodeSyntaxError(ScoringError):
    """
    Raised when the code being analyzed has syntax errors.
    
    Note: In fail-closed mode, syntax errors result in score 1.0
    rather than raising this exception.
    
    Attributes:
        line_number: Line where syntax error occurred.
        details: Parser error details.
    """
    
    def __init__(self, message: str, line_number: int | None = None, details: str = ""):
        self.line_number = line_number
        self.details = details
        super().__init__(f"Syntax error: {message}")


# =============================================================================
# Calibration Exceptions
# =============================================================================

class CalibrationError(SentinelError):
    """
    Base exception for calibration-related errors.
    
    Raised when calibration operations fail.
    """
    pass


class CalibrationFileNotFoundError(CalibrationError):
    """
    Raised when calibration file is not found.
    
    This is informational - the application should fall back
    to the default threshold when this occurs.
    
    Attributes:
        path: Path that was not found.
    """
    
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Calibration file not found: {path}")


class CalibrationFileCorruptError(CalibrationError):
    """
    Raised when calibration file exists but cannot be parsed.
    
    Attributes:
        path: Path to the corrupt file.
        details: Parse error details.
    """
    
    def __init__(self, path: str, details: str = ""):
        self.path = path
        self.details = details
        super().__init__(f"Calibration file corrupt: {path}. {details}")


class DatasetLoadError(CalibrationError):
    """
    Raised when calibration dataset cannot be loaded.
    
    Attributes:
        dataset_name: Name of the dataset that failed to load.
    """
    
    def __init__(self, dataset_name: str, details: str = ""):
        self.dataset_name = dataset_name
        super().__init__(f"Failed to load dataset '{dataset_name}': {details}")


class InsufficientSamplesError(CalibrationError):
    """
    Raised when not enough samples are available for calibration.
    
    Attributes:
        required: Number of samples required.
        available: Number of samples available.
    """
    
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient samples for calibration. "
            f"Required: {required}, Available: {available}"
        )


# =============================================================================
# Analyst/LLM Exceptions
# =============================================================================

class AnalystError(SentinelError):
    """
    Base exception for analyst/LLM-related errors.
    
    Raised when code generation fails.
    """
    pass


class LLMConnectionError(AnalystError):
    """
    Raised when connection to LLM service fails.
    
    Attributes:
        provider: Name of the LLM provider.
        endpoint: Endpoint that failed.
    """
    
    def __init__(self, provider: str, endpoint: str = "", details: str = ""):
        self.provider = provider
        self.endpoint = endpoint
        super().__init__(
            f"Failed to connect to {provider}"
            f"{f' at {endpoint}' if endpoint else ''}: {details}"
        )


class LLMAuthenticationError(AnalystError):
    """
    Raised when LLM authentication fails.
    
    Attributes:
        provider: Name of the LLM provider.
    """
    
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(
            f"Authentication failed for {provider}. "
            "Check your API key configuration."
        )


class LLMRateLimitError(AnalystError):
    """
    Raised when LLM rate limit is exceeded.
    
    Attributes:
        provider: Name of the LLM provider.
        retry_after: Seconds to wait before retry.
    """
    
    def __init__(self, provider: str, retry_after: int | None = None):
        self.provider = provider
        self.retry_after = retry_after
        msg = f"Rate limit exceeded for {provider}"
        if retry_after:
            msg += f". Retry after {retry_after} seconds"
        super().__init__(msg)


class LLMTimeoutError(AnalystError):
    """
    Raised when LLM request times out.
    
    Attributes:
        timeout_seconds: The timeout that was exceeded.
    """
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"LLM request timed out after {timeout_seconds} seconds")


class MissingCredentialsError(AnalystError):
    """
    Raised when required LLM credentials are not configured.
    
    Attributes:
        missing_vars: List of missing environment variables.
    """
    
    def __init__(self, missing_vars: list[str]):
        self.missing_vars = missing_vars
        super().__init__(
            f"Missing required credentials: {', '.join(missing_vars)}. "
            "Set these as environment variables or in .env file."
        )


# =============================================================================
# Verification Exceptions
# =============================================================================

class VerificationError(SentinelError):
    """
    Base exception for verification-related errors.
    
    Raised when the verification process fails.
    """
    pass


class ThresholdNotCalibratedError(VerificationError):
    """
    Raised when verification is attempted without calibration.
    
    This is a warning - verification can proceed with default threshold.
    """
    
    def __init__(self, default_threshold: float):
        self.default_threshold = default_threshold
        super().__init__(
            f"No calibration data found. Using default threshold: {default_threshold}"
        )


# =============================================================================
# Configuration Exceptions
# =============================================================================

class ConfigurationError(SentinelError):
    """
    Base exception for configuration-related errors.
    
    Raised when configuration is invalid or missing.
    """
    pass


class InvalidConfigurationError(ConfigurationError):
    """
    Raised when configuration values are invalid.
    
    Attributes:
        field: Name of the invalid field.
        value: The invalid value.
        reason: Why the value is invalid.
    """
    
    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid configuration for '{field}': {reason}")
