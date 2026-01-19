"""
Protocol definitions for Assured Sentinel.

This module defines abstract interfaces (Protocols) following the
Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP).
All concrete implementations should implement these protocols.
"""

from typing import Protocol, runtime_checkable
from pathlib import Path

from assured_sentinel.models import VerificationResult, CalibrationData


@runtime_checkable
class IScoringService(Protocol):
    """
    Protocol for code security scoring services.
    
    Implementations should analyze code and return a risk score
    between 0.0 (safe) and 1.0 (high risk).
    
    Examples:
        - BanditScorer: Uses Python Bandit SAST tool
        - SemgrepScorer: Uses Semgrep rules
        - SnykScorer: Uses Snyk Code analysis
    """
    
    def score(self, code: str) -> float:
        """
        Calculate a security risk score for the given code.
        
        Args:
            code: Python source code to analyze.
            
        Returns:
            Float between 0.0 (no issues) and 1.0 (high severity issues).
            
        Raises:
            ScoringError: If scoring fails.
        """
        ...


@runtime_checkable
class ICodeSanitizer(Protocol):
    """
    Protocol for code sanitization/preprocessing.
    
    Implementations clean and normalize code before analysis,
    removing markdown fences, normalizing whitespace, etc.
    """
    
    def sanitize(self, code: str) -> str:
        """
        Sanitize code for analysis.
        
        Args:
            code: Raw code string, possibly with markdown fences.
            
        Returns:
            Cleaned code string ready for analysis.
        """
        ...


@runtime_checkable
class IVerifier(Protocol):
    """
    Protocol for code verification services.
    
    Verifiers combine scoring with threshold comparison to
    make accept/reject decisions with statistical guarantees.
    """
    
    def verify(self, code: str) -> VerificationResult:
        """
        Verify code against the calibrated threshold.
        
        Args:
            code: Python source code to verify.
            
        Returns:
            VerificationResult with status, score, threshold, and reason.
        """
        ...
    
    @property
    def threshold(self) -> float:
        """Current verification threshold (q̂)."""
        ...


@runtime_checkable
class ICodeGenerator(Protocol):
    """
    Protocol for LLM-based code generation.
    
    Implementations connect to various LLM providers to
    generate code based on user prompts.
    
    Examples:
        - AzureAnalyst: Uses Azure OpenAI
        - OpenAIAnalyst: Uses OpenAI directly
        - AnthropicAnalyst: Uses Claude models
    """
    
    async def generate(self, prompt: str) -> str:
        """
        Generate code based on the given prompt.
        
        Args:
            prompt: User request describing desired code.
            
        Returns:
            Generated Python code.
            
        Raises:
            AnalystError: If code generation fails.
        """
        ...


@runtime_checkable
class ICalibrationStore(Protocol):
    """
    Protocol for calibration data persistence.
    
    Implementations handle loading and saving calibration data
    to various storage backends.
    
    Examples:
        - JsonCalibrationStore: JSON file storage
        - SqliteCalibrationStore: SQLite database
        - AzureBlobCalibrationStore: Cloud storage
    """
    
    def load(self) -> CalibrationData | None:
        """
        Load calibration data from storage.
        
        Returns:
            CalibrationData if found, None otherwise.
            
        Raises:
            CalibrationError: If loading fails (not if file doesn't exist).
        """
        ...
    
    def save(self, data: CalibrationData) -> None:
        """
        Save calibration data to storage.
        
        Args:
            data: Calibration data to persist.
            
        Raises:
            CalibrationError: If saving fails.
        """
        ...
    
    def exists(self) -> bool:
        """Check if calibration data exists in storage."""
        ...


@runtime_checkable
class ICalibrator(Protocol):
    """
    Protocol for calibration services.
    
    Calibrators compute the threshold (q̂) using statistical
    methods like Conformal Prediction.
    """
    
    def calibrate(self, scores: list[float], alpha: float) -> float:
        """
        Compute calibration threshold from scores.
        
        Args:
            scores: List of non-conformity scores from calibration set.
            alpha: Risk tolerance (e.g., 0.1 for 10% error rate).
            
        Returns:
            Calibrated threshold (q̂).
        """
        ...


@runtime_checkable
class ITempFileManager(Protocol):
    """
    Protocol for temporary file management.
    
    Implementations handle creating and cleaning up temp files
    for code analysis tools that require file-based input.
    """
    
    def create(self, content: str, suffix: str = ".py") -> Path:
        """
        Create a temporary file with the given content.
        
        Args:
            content: File content.
            suffix: File extension.
            
        Returns:
            Path to the created temporary file.
        """
        ...
    
    def cleanup(self, path: Path) -> None:
        """
        Clean up a temporary file.
        
        Args:
            path: Path to the file to delete.
        """
        ...


@runtime_checkable
class IDatasetLoader(Protocol):
    """
    Protocol for loading calibration datasets.
    
    Implementations fetch code samples from various sources
    for use in calibration.
    """
    
    def load(self, n_samples: int) -> list[str]:
        """
        Load code samples for calibration.
        
        Args:
            n_samples: Number of samples to load.
            
        Returns:
            List of code strings.
            
        Raises:
            CalibrationError: If loading fails.
        """
        ...
