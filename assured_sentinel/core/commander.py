"""
Commander Module: Code Verification Gate.

This module implements the verification logic that compares code scores
against calibrated thresholds to make accept/reject decisions.

The Commander follows the Dependency Inversion Principle by accepting
an IScoringService implementation, allowing different scoring backends.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from assured_sentinel.config import Settings, get_settings
from assured_sentinel.exceptions import (
    CalibrationFileCorruptError,
    CalibrationFileNotFoundError,
)
from assured_sentinel.models import (
    CalibrationData,
    VerificationConfig,
    VerificationResult,
    VerificationStatus,
)

if TYPE_CHECKING:
    from assured_sentinel.protocols import ICalibrationStore, IScoringService

logger = logging.getLogger(__name__)


# =============================================================================
# Calibration Store Implementations
# =============================================================================

class JsonCalibrationStore:
    """
    JSON file-based calibration data storage.
    
    Implements ICalibrationStore protocol.
    This is the preferred storage format for production use.
    """
    
    def __init__(self, path: Path | str):
        """
        Initialize JSON calibration store.
        
        Args:
            path: Path to the JSON calibration file.
        """
        self._path = Path(path)
    
    def exists(self) -> bool:
        """Check if calibration file exists."""
        return self._path.exists()
    
    def load(self) -> CalibrationData | None:
        """
        Load calibration data from JSON file.
        
        Returns:
            CalibrationData if file exists, None otherwise.
            
        Raises:
            CalibrationFileCorruptError: If file exists but cannot be parsed.
        """
        if not self.exists():
            return None
            
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return CalibrationData(**data)
        except json.JSONDecodeError as e:
            raise CalibrationFileCorruptError(str(self._path), str(e))
        except Exception as e:
            raise CalibrationFileCorruptError(str(self._path), str(e))
    
    def save(self, data: CalibrationData) -> None:
        """
        Save calibration data to JSON file.
        
        Args:
            data: Calibration data to persist.
        """
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data.model_dump(mode="json"), f, indent=2, default=str)
        logger.info(f"Calibration data saved to {self._path}")


# =============================================================================
# Commander
# =============================================================================

class Commander:
    """
    The verification gate for AI-generated code.
    
    Commander compares code security scores against a calibrated threshold
    to make statistically-grounded accept/reject decisions.
    
    The threshold (q̂) is derived from Split Conformal Prediction,
    providing bounded guarantees on the unsafe code acceptance rate.
    
    Attributes:
        threshold: Current verification threshold (q̂).
        
    Example:
        >>> from assured_sentinel import Commander, BanditScorer
        >>> commander = Commander(scorer=BanditScorer())
        >>> result = commander.verify("print('hello')")
        >>> result.passed
        True
        >>> result = commander.verify("exec(user_input)")
        >>> result.passed
        False
    """
    
    def __init__(
        self,
        scorer: IScoringService | None = None,
        calibration_store: ICalibrationStore | None = None,
        config: VerificationConfig | None = None,
        settings: Settings | None = None,
    ):
        """
        Initialize Commander.
        
        Args:
            scorer: Scoring service. Creates BanditScorer if None.
            calibration_store: Calibration data store. Uses JSON store if None.
            config: Verification configuration.
            settings: Application settings.
        """
        self._settings = settings or get_settings()
        self._config = config or VerificationConfig(
            default_threshold=self._settings.default_threshold,
            calibration_path=self._settings.calibration_path,
        )
        
        # Lazy import to avoid circular dependency
        if scorer is None:
            from assured_sentinel.core.scorer import BanditScorer
            scorer = BanditScorer()
        self._scorer = scorer
        
        self._calibration_store = calibration_store or JsonCalibrationStore(
            self._config.calibration_path
        )
        
        self._threshold = self._load_threshold()
        logger.info(f"Commander initialized. Threshold (q̂): {self._threshold}")
    
    @property
    def threshold(self) -> float:
        """Current verification threshold (q̂)."""
        return self._threshold
    
    @threshold.setter
    def threshold(self, value: float) -> None:
        """Set verification threshold manually."""
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {value}")
        self._threshold = value
        logger.info(f"Threshold manually set to {value}")
    
    def _load_threshold(self) -> float:
        """
        Load threshold from calibration store.
        
        Returns:
            Calibrated threshold if available, default otherwise.
        """
        try:
            calibration = self._calibration_store.load()
            if calibration:
                logger.info(
                    f"Loaded calibration from {self._config.calibration_path} "
                    f"(calibrated: {calibration.calibrated_at})"
                )
                return calibration.q_hat
        except CalibrationFileCorruptError as e:
            logger.error(f"Calibration file corrupt: {e}")
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
        
        logger.warning(
            f"No calibration found. Using default threshold: "
            f"{self._config.default_threshold}"
        )
        return self._config.default_threshold
    
    def verify(self, code: str) -> VerificationResult:
        """
        Verify code against the calibrated threshold.
        
        This is the main verification gate. Code with scores at or below
        the threshold passes; code above the threshold is rejected.
        
        Args:
            code: Python source code to verify.
            
        Returns:
            VerificationResult with status, score, threshold, and reason.
        """
        start_time = time.perf_counter()
        
        # Calculate non-conformity score
        score = self._scorer.score(code)
        
        # Compare against threshold
        is_passed = score <= self._threshold
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        if is_passed:
            reason = "Code meets assurance standards."
            logger.info(f"APPROVED (Score: {score:.4f} <= {self._threshold:.4f})")
        else:
            reason = f"Security score {score:.4f} exceeds threshold {self._threshold:.4f}."
            logger.warning(f"REJECTED (Score: {score:.4f} > {self._threshold:.4f})")
        
        return VerificationResult(
            status=VerificationStatus.PASS if is_passed else VerificationStatus.REJECT,
            score=score,
            threshold=self._threshold,
            reason=reason,
            latency_ms=latency_ms,
        )
    
    def reload_calibration(self) -> None:
        """
        Reload calibration data from store.
        
        Call this after running calibration to pick up new threshold.
        """
        self._threshold = self._load_threshold()


# =============================================================================
# Factory Function
# =============================================================================

def create_commander(
    threshold: float | None = None,
    calibration_path: Path | str | None = None,
) -> Commander:
    """
    Factory function to create a configured Commander.
    
    Args:
        threshold: Override threshold (ignores calibration file).
        calibration_path: Custom path to calibration file.
        
    Returns:
        Configured Commander instance.
    """
    config = VerificationConfig()
    if calibration_path:
        config.calibration_path = Path(calibration_path)
    
    commander = Commander(config=config)
    
    if threshold is not None:
        commander.threshold = threshold
    
    return commander
