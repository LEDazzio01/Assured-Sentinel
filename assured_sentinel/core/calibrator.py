"""
Calibration Module: Split Conformal Prediction.

This module implements calibration using Split Conformal Prediction to
compute a threshold (q̂) that provides statistical guarantees on the
unsafe code acceptance rate.

The calibration process:
1. Load code samples from a dataset (e.g., MBPP)
2. Inject synthetic vulnerabilities to ensure meaningful distribution
3. Score all samples using the scoring service
4. Compute the quantile threshold based on risk tolerance (α)
5. Save calibration data for use by Commander
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from assured_sentinel.config import Settings, get_settings
from assured_sentinel.core.commander import JsonCalibrationStore
from assured_sentinel.exceptions import (
    CalibrationError,
    DatasetLoadError,
    InsufficientSamplesError,
)
from assured_sentinel.models import CalibrationConfig, CalibrationData

if TYPE_CHECKING:
    from assured_sentinel.protocols import ICalibrationStore, IDatasetLoader, IScoringService

logger = logging.getLogger(__name__)


# =============================================================================
# Synthetic Vulnerability Patterns
# =============================================================================

SYNTHETIC_VULNERABILITIES = [
    # High severity patterns
    "import pickle\npickle.loads(untrusted_data)",
    "eval(user_input)",
    "exec(user_code)",
    "__import__('os').system(cmd)",
    
    # Medium severity patterns
    "password = 'hardcoded_secret'",
    "api_key = 'sk-1234567890'",
    "tmp = '/tmp/insecure_path'",
    "subprocess.call(user_input, shell=True)",
    
    # Low severity patterns
    "import random\nprint(random.random())",
    "assert user_is_admin",
]


# =============================================================================
# Dataset Loaders
# =============================================================================

class MBPPDatasetLoader:
    """
    Loads code samples from the MBPP (Mostly Basic Python Problems) dataset.
    
    Implements IDatasetLoader protocol.
    
    Note: MBPP is a general Python programming dataset, NOT a security-labeled
    corpus. We use it as a baseline distribution of "typical" code, then
    inject known-bad patterns to ensure the calibration threshold is meaningful.
    """
    
    def __init__(self, injection_rate: float = 0.2):
        """
        Initialize MBPP dataset loader.
        
        Args:
            injection_rate: Rate of synthetic vulnerability injection (default: 20%).
        """
        self._injection_rate = injection_rate
    
    def load(self, n_samples: int) -> list[str]:
        """
        Load code samples from MBPP dataset with synthetic injection.
        
        Args:
            n_samples: Number of samples to load.
            
        Returns:
            List of code strings.
            
        Raises:
            DatasetLoadError: If dataset cannot be loaded.
        """
        logger.info(f"Loading {n_samples} samples from MBPP dataset...")
        
        try:
            from datasets import load_dataset
            dataset = load_dataset("mbpp", split="test")
        except Exception as e:
            raise DatasetLoadError("mbpp", str(e))
        
        samples = []
        for i, row in enumerate(dataset):
            if i >= n_samples:
                break
            samples.append(row["code"])
        
        if len(samples) < n_samples:
            logger.warning(
                f"Only {len(samples)} samples available, requested {n_samples}"
            )
        
        # Inject synthetic vulnerabilities
        samples = self._inject_vulnerabilities(samples)
        
        return samples
    
    def _inject_vulnerabilities(self, samples: list[str]) -> list[str]:
        """
        Inject synthetic vulnerabilities into samples.
        
        Overwrites the last N samples (where N = injection_rate * len(samples))
        with known-vulnerable patterns.
        
        Args:
            samples: Original code samples.
            
        Returns:
            Samples with vulnerabilities injected.
        """
        injection_count = int(len(samples) * self._injection_rate)
        logger.info(
            f"Injecting {injection_count} synthetic vulnerabilities "
            f"({self._injection_rate * 100:.0f}%)"
        )
        
        for i in range(1, injection_count + 1):
            pattern = SYNTHETIC_VULNERABILITIES[i % len(SYNTHETIC_VULNERABILITIES)]
            samples[-i] = pattern
        
        return samples


class StaticDatasetLoader:
    """
    Loads code samples from a static list.
    
    Useful for testing and offline scenarios.
    """
    
    def __init__(self, samples: list[str]):
        """
        Initialize with static samples.
        
        Args:
            samples: List of code samples.
        """
        self._samples = samples
    
    def load(self, n_samples: int) -> list[str]:
        """Load samples (up to n_samples)."""
        return self._samples[:n_samples]


# =============================================================================
# Calibrator
# =============================================================================

class ConformalCalibrator:
    """
    Computes calibration threshold using Split Conformal Prediction.
    
    The calibrator computes q̂ (q-hat) such that:
    P(score > q̂) ≤ α
    
    where α is the risk tolerance (e.g., 0.1 for 10% error rate).
    
    Example:
        >>> calibrator = ConformalCalibrator()
        >>> q_hat = calibrator.calibrate(scores=[0.0, 0.1, 0.5, 1.0], alpha=0.1)
        >>> q_hat
        0.5
    """
    
    def calibrate(self, scores: list[float], alpha: float) -> float:
        """
        Compute calibration threshold from scores.
        
        Uses the mathematical correction for finite sample size:
        q_level = ceil((n + 1) * (1 - α)) / n
        
        Args:
            scores: List of non-conformity scores from calibration set.
            alpha: Risk tolerance (e.g., 0.1 for 10% error rate).
            
        Returns:
            Calibrated threshold (q̂).
            
        Raises:
            InsufficientSamplesError: If not enough samples provided.
        """
        n = len(scores)
        if n < 2:
            raise InsufficientSamplesError(required=2, available=n)
        
        # Mathematical correction for Split Conformal Prediction
        q_level = np.ceil((n + 1) * (1 - alpha)) / n
        q_level = min(1.0, q_level)
        
        q_hat = float(np.quantile(scores, q_level, method="higher"))
        
        logger.info(f"Calibration: n={n}, α={alpha}, q̂={q_hat}")
        
        return q_hat


# =============================================================================
# Calibration Runner
# =============================================================================

class CalibrationRunner:
    """
    Orchestrates the full calibration process.
    
    This class coordinates:
    1. Loading samples from dataset
    2. Scoring all samples
    3. Computing threshold
    4. Saving results
    
    Example:
        >>> runner = CalibrationRunner()
        >>> data = runner.run()
        >>> print(f"Threshold: {data.q_hat}")
    """
    
    def __init__(
        self,
        scorer: IScoringService | None = None,
        dataset_loader: IDatasetLoader | None = None,
        calibrator: ConformalCalibrator | None = None,
        calibration_store: ICalibrationStore | None = None,
        config: CalibrationConfig | None = None,
        settings: Settings | None = None,
    ):
        """
        Initialize calibration runner.
        
        Args:
            scorer: Scoring service. Creates BanditScorer if None.
            dataset_loader: Dataset loader. Uses MBPPDatasetLoader if None.
            calibrator: Calibrator. Uses ConformalCalibrator if None.
            calibration_store: Store for saving results. Uses JSON if None.
            config: Calibration configuration.
            settings: Application settings.
        """
        self._settings = settings or get_settings()
        self._config = config or CalibrationConfig(
            alpha=self._settings.alpha,
            n_samples=self._settings.calibration_n_samples,
            output_path=self._settings.calibration_path,
        )
        
        # Lazy import to avoid circular dependency
        if scorer is None:
            from assured_sentinel.core.scorer import BanditScorer
            scorer = BanditScorer()
        self._scorer = scorer
        
        self._dataset_loader = dataset_loader or MBPPDatasetLoader(
            injection_rate=self._config.injection_rate
        )
        self._calibrator = calibrator or ConformalCalibrator()
        self._calibration_store = calibration_store or JsonCalibrationStore(
            self._config.output_path
        )
    
    def run(self, verbose: bool = True) -> CalibrationData:
        """
        Run the full calibration process.
        
        Args:
            verbose: Print progress to stdout.
            
        Returns:
            CalibrationData with computed threshold and metadata.
            
        Raises:
            CalibrationError: If calibration fails.
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"CALIBRATION (α={self._config.alpha})")
            print(f"{'='*60}\n")
        
        # 1. Load samples
        samples = self._dataset_loader.load(self._config.n_samples)
        if verbose:
            print(f"✓ Loaded {len(samples)} samples")
        
        # 2. Score all samples
        scores = self._score_samples(samples, verbose)
        if verbose:
            print(f"✓ Scored {len(scores)} samples")
        
        # 3. Compute threshold
        q_hat = self._calibrator.calibrate(scores, self._config.alpha)
        if verbose:
            print(f"✓ Computed threshold: {q_hat}")
        
        # 4. Build calibration data
        dataset_hash = hashlib.sha256(
            "".join(samples[:10]).encode()
        ).hexdigest()[:12]
        
        calibration_data = CalibrationData(
            q_hat=q_hat,
            alpha=self._config.alpha,
            n_samples=len(samples),
            scores=scores,
            dataset="mbpp",
            dataset_hash=dataset_hash,
            scorer="bandit",
            scorer_version="1.7+",
            calibrated_at=datetime.utcnow(),
            notes=(
                "MBPP is baseline distribution, not security-labeled. "
                f"Includes {self._config.injection_rate * 100:.0f}% synthetic injection."
            ),
        )
        
        # 5. Save results
        self._calibration_store.save(calibration_data)
        if verbose:
            print(f"✓ Saved to {self._config.output_path}")
            print(f"\n{'='*60}")
            print(f"CALIBRATION COMPLETE: q̂ = {q_hat}")
            print(f"{'='*60}\n")
        
        return calibration_data
    
    def _score_samples(self, samples: list[str], verbose: bool) -> list[float]:
        """Score all samples."""
        scores = []
        total = len(samples)
        
        for i, code in enumerate(samples):
            score = self._scorer.score(code)
            scores.append(score)
            
            if verbose and (i + 1) % 20 == 0:
                print(f"  Scoring progress: {i + 1}/{total}")
        
        return scores


# =============================================================================
# Module-level Functions (Backward Compatibility)
# =============================================================================

def calibrate(alpha: float = 0.1, n_samples: int = 100) -> float:
    """
    Run calibration and return threshold (backward compatibility).
    
    Args:
        alpha: Risk tolerance.
        n_samples: Number of samples to use.
        
    Returns:
        Calibrated threshold (q̂).
    """
    config = CalibrationConfig(alpha=alpha, n_samples=n_samples)
    runner = CalibrationRunner(config=config)
    data = runner.run()
    return data.q_hat


def get_calibration_data(n: int = 100) -> list[str]:
    """
    Get calibration data samples (backward compatibility).
    
    Args:
        n: Number of samples to load.
        
    Returns:
        List of code samples.
    """
    loader = MBPPDatasetLoader()
    return loader.load(n)
