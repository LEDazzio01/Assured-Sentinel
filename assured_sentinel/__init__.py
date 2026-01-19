"""
Assured Sentinel: Probabilistic Guardrails for AI-Generated Code

This package provides statistical guarantees for AI-generated code safety
using Conformal Prediction and deterministic SAST scoring.
"""

from assured_sentinel.core.commander import Commander
from assured_sentinel.core.scorer import BanditScorer
from assured_sentinel.core.calibrator import ConformalCalibrator
from assured_sentinel.models import VerificationResult, CalibrationData
from assured_sentinel.config import Settings

__version__ = "2.0.0"
__all__ = [
    "Commander",
    "BanditScorer",
    "ConformalCalibrator",
    "VerificationResult",
    "CalibrationData",
    "Settings",
]
