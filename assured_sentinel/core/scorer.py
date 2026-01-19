"""
Scorer Module: Deterministic Security Scoring.

This module provides code security scoring implementations following the
IScoringService protocol. The primary implementation uses Bandit (Python SAST)
to analyze code and return a normalized risk score.

Architecture Notes:
------------------
The scorer follows Single Responsibility Principle by separating concerns:
- CodeSanitizer: Cleans/normalizes code before analysis
- TempFileManager: Handles temporary file lifecycle
- BanditScorer: Orchestrates Bandit execution and score calculation

For production optimization options, see docs/Decision-log.md D-011.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from assured_sentinel.exceptions import (
    BanditExecutionError,
    BanditNotFoundError,
    BanditParseError,
    ScoringError,
    ScoringTimeoutError,
)
from assured_sentinel.models import (
    ScoringConfig,
    ScoringResult,
    SecurityIssue,
    Severity,
)

if TYPE_CHECKING:
    from assured_sentinel.protocols import ICodeSanitizer, IScoringService, ITempFileManager

logger = logging.getLogger(__name__)


# =============================================================================
# Code Sanitizer
# =============================================================================

class MarkdownCodeSanitizer:
    """
    Sanitizes code by removing markdown fences and normalizing whitespace.
    
    Implements ICodeSanitizer protocol.
    """
    
    # Patterns for markdown code fences
    _START_FENCE_PATTERN = re.compile(r"^```[a-zA-Z]*\n", re.MULTILINE)
    _END_FENCE_PATTERN = re.compile(r"\n```$", re.MULTILINE)
    
    def sanitize(self, code: str) -> str:
        """
        Remove markdown code fences and normalize whitespace.
        
        Args:
            code: Raw code string, possibly with markdown fences.
            
        Returns:
            Cleaned code string ready for analysis.
        """
        if not code:
            return ""
            
        cleaned = code.strip()
        
        # Remove starting ```python or ```
        cleaned = self._START_FENCE_PATTERN.sub("", cleaned)
        
        # Remove ending ```
        cleaned = self._END_FENCE_PATTERN.sub("", cleaned)
        
        return cleaned.strip()


# =============================================================================
# Temp File Manager
# =============================================================================

class StandardTempFileManager:
    """
    Manages temporary files using the system temp directory.
    
    Implements ITempFileManager protocol.
    """
    
    def __init__(self, base_dir: Path | None = None):
        """
        Initialize temp file manager.
        
        Args:
            base_dir: Optional custom temp directory. Uses system default if None.
        """
        self._base_dir = base_dir
    
    def create(self, content: str, suffix: str = ".py") -> Path:
        """
        Create a temporary file with the given content.
        
        Args:
            content: File content.
            suffix: File extension.
            
        Returns:
            Path to the created temporary file.
        """
        kwargs = {"mode": "w", "suffix": suffix, "delete": False, "encoding": "utf-8"}
        if self._base_dir:
            kwargs["dir"] = str(self._base_dir)
            
        with tempfile.NamedTemporaryFile(**kwargs) as f:
            f.write(content)
            return Path(f.name)
    
    def cleanup(self, path: Path) -> None:
        """
        Clean up a temporary file.
        
        Args:
            path: Path to the file to delete.
        """
        try:
            if path.exists():
                path.unlink()
        except OSError as e:
            logger.warning(f"Failed to cleanup temp file {path}: {e}")


class RamdiskTempFileManager(StandardTempFileManager):
    """
    Manages temporary files using a ramdisk for improved performance.
    
    Uses /dev/shm on Linux for in-memory file operations,
    significantly reducing I/O latency for high-throughput scenarios.
    """
    
    def __init__(self, ramdisk_path: Path = Path("/dev/shm/sentinel")):
        """
        Initialize ramdisk temp file manager.
        
        Args:
            ramdisk_path: Path to ramdisk mount point.
        """
        # Ensure ramdisk directory exists
        ramdisk_path.mkdir(parents=True, exist_ok=True)
        super().__init__(base_dir=ramdisk_path)


# =============================================================================
# Abstract Scorer Base
# =============================================================================

class BaseScoringService(ABC):
    """
    Abstract base class for scoring services.
    
    Provides common functionality for all scoring implementations.
    """
    
    def __init__(
        self,
        sanitizer: ICodeSanitizer | None = None,
        config: ScoringConfig | None = None,
    ):
        """
        Initialize scoring service.
        
        Args:
            sanitizer: Code sanitizer. Uses MarkdownCodeSanitizer if None.
            config: Scoring configuration. Uses defaults if None.
        """
        self._sanitizer = sanitizer or MarkdownCodeSanitizer()
        self._config = config or ScoringConfig()
    
    @abstractmethod
    def _calculate_score(self, code: str) -> ScoringResult:
        """
        Calculate score for sanitized code.
        
        Args:
            code: Sanitized code to analyze.
            
        Returns:
            ScoringResult with score and any issues found.
        """
        ...
    
    def score(self, code: str) -> float:
        """
        Calculate a security risk score for the given code.
        
        Args:
            code: Python source code to analyze.
            
        Returns:
            Float between 0.0 (no issues) and 1.0 (high severity issues).
        """
        try:
            sanitized = self._sanitizer.sanitize(code)
            result = self._calculate_score(sanitized)
            return result.score
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Unexpected scoring error: {e}")
            if self._config.fail_closed:
                return 1.0
            raise ScoringError(f"Scoring failed: {e}") from e


# =============================================================================
# Bandit Scorer
# =============================================================================

class BanditScorer(BaseScoringService):
    """
    Scores code using Bandit Python SAST tool.
    
    This is the primary scoring implementation for Assured Sentinel.
    It runs Bandit as a subprocess and parses the JSON output to
    calculate a normalized risk score.
    
    Score Mapping:
        - No issues: 0.0
        - LOW severity: 0.1
        - MEDIUM severity: 0.5
        - HIGH severity: 1.0
    
    Fail-Closed Behavior:
        - Bandit not found: 1.0
        - Syntax errors: 1.0
        - Parse errors: 1.0
        - Timeout: 1.0
    
    Example:
        >>> scorer = BanditScorer()
        >>> scorer.score("print('hello')")
        0.0
        >>> scorer.score("exec(user_input)")
        0.5
    """
    
    SEVERITY_SCORES = {
        Severity.LOW: 0.1,
        Severity.MEDIUM: 0.5,
        Severity.HIGH: 1.0,
    }
    
    def __init__(
        self,
        sanitizer: ICodeSanitizer | None = None,
        temp_file_manager: ITempFileManager | None = None,
        config: ScoringConfig | None = None,
    ):
        """
        Initialize Bandit scorer.
        
        Args:
            sanitizer: Code sanitizer. Uses MarkdownCodeSanitizer if None.
            temp_file_manager: Temp file manager. Uses StandardTempFileManager if None.
            config: Scoring configuration.
        """
        super().__init__(sanitizer=sanitizer, config=config)
        
        if config and config.use_ramdisk:
            self._temp_manager = temp_file_manager or RamdiskTempFileManager(
                config.ramdisk_path
            )
        else:
            self._temp_manager = temp_file_manager or StandardTempFileManager()
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _find_bandit() -> str | None:
        """Find Bandit executable path (cached)."""
        return shutil.which("bandit")
    
    def _calculate_score(self, code: str) -> ScoringResult:
        """
        Calculate score using Bandit.
        
        Args:
            code: Sanitized code to analyze.
            
        Returns:
            ScoringResult with score and issues.
        """
        # Check Bandit availability
        bandit_path = self._find_bandit()
        if not bandit_path:
            logger.error("Bandit executable not found in PATH")
            if self._config.fail_closed:
                return ScoringResult(score=1.0, error="Bandit not found")
            raise BanditNotFoundError()
        
        # Create temp file
        temp_path = self._temp_manager.create(code)
        
        try:
            # Run Bandit
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", "--exit-zero", str(temp_path)],
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
            )
            
            return self._parse_bandit_output(result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Bandit timed out after {self._config.timeout_seconds}s")
            if self._config.fail_closed:
                return ScoringResult(score=1.0, error="Timeout")
            raise ScoringTimeoutError(self._config.timeout_seconds)
            
        except Exception as e:
            logger.error(f"Bandit execution failed: {e}")
            if self._config.fail_closed:
                return ScoringResult(score=1.0, error=str(e))
            raise BanditExecutionError(str(e)) from e
            
        finally:
            self._temp_manager.cleanup(temp_path)
    
    def _parse_bandit_output(self, stdout: str, stderr: str) -> ScoringResult:
        """
        Parse Bandit JSON output into ScoringResult.
        
        Args:
            stdout: Bandit stdout (JSON).
            stderr: Bandit stderr (errors/warnings).
            
        Returns:
            ScoringResult with score and issues.
        """
        try:
            report = json.loads(stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit JSON: {e}")
            if self._config.fail_closed:
                return ScoringResult(score=1.0, error=f"JSON parse error: {stderr}")
            raise BanditParseError("Invalid JSON output", stdout[:200])
        
        # Check for parsing errors (syntax errors in analyzed code)
        errors = report.get("errors", [])
        if errors:
            logger.warning(f"Bandit reported errors (syntax?): {errors}")
            return ScoringResult(
                score=1.0,
                error=f"Code parse error: {errors[0].get('reason', 'unknown')}",
            )
        
        # Extract security issues
        results = report.get("results", [])
        
        if not results:
            return ScoringResult(score=0.0)
        
        # Convert to SecurityIssue models and calculate max score
        issues: list[SecurityIssue] = []
        max_score = 0.0
        
        for item in results:
            severity_str = item.get("issue_severity", "LOW").upper()
            try:
                severity = Severity(severity_str)
            except ValueError:
                severity = Severity.LOW
            
            issue = SecurityIssue(
                test_id=item.get("test_id", "UNKNOWN"),
                severity=severity,
                confidence=item.get("issue_confidence", "MEDIUM"),
                description=item.get("issue_text", ""),
                line_number=item.get("line_number"),
            )
            issues.append(issue)
            
            severity_score = self.SEVERITY_SCORES.get(severity, 0.1)
            logger.warning(f"Issue: {issue.test_id} ({severity.value})")
            
            # HIGH severity returns immediately
            if severity == Severity.HIGH:
                return ScoringResult(score=1.0, issues=issues)
            
            max_score = max(max_score, severity_score)
        
        return ScoringResult(score=max_score, issues=issues)


# =============================================================================
# Factory Function
# =============================================================================

def create_scorer(
    use_ramdisk: bool = False,
    ramdisk_path: Path | None = None,
    timeout_seconds: int = 30,
    fail_closed: bool = True,
) -> BanditScorer:
    """
    Factory function to create a configured BanditScorer.
    
    Args:
        use_ramdisk: Use ramdisk for temp files (performance optimization).
        ramdisk_path: Custom ramdisk path. Uses /dev/shm/sentinel if None.
        timeout_seconds: Timeout for Bandit execution.
        fail_closed: Return 1.0 on any error if True.
        
    Returns:
        Configured BanditScorer instance.
    """
    config = ScoringConfig(
        timeout_seconds=timeout_seconds,
        fail_closed=fail_closed,
        use_ramdisk=use_ramdisk,
        ramdisk_path=ramdisk_path or Path("/dev/shm/sentinel"),
    )
    return BanditScorer(config=config)


# =============================================================================
# Backward Compatibility
# =============================================================================

# Module-level scorer instance for backward compatibility
_default_scorer: BanditScorer | None = None


def calculate_score(code_snippet: str) -> float:
    """
    Calculate security score for code (backward compatibility function).
    
    This function maintains backward compatibility with the original API.
    For new code, prefer using BanditScorer class directly.
    
    Args:
        code_snippet: Python code to analyze.
        
    Returns:
        Float between 0.0 and 1.0.
    """
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = BanditScorer()
    return _default_scorer.score(code_snippet)


def _clean_code(code: str) -> str:
    """
    Clean code by removing markdown fences (backward compatibility).
    
    Deprecated: Use MarkdownCodeSanitizer instead.
    """
    return MarkdownCodeSanitizer().sanitize(code)
