"""
Calibration Module: Backward Compatibility Shim
===============================================

.. deprecated:: 2.0.0
    This module is deprecated. Use `assured_sentinel.core.calibrator` instead.

Example migration::

    # Old (deprecated)
    from calibration import calibrate, get_calibration_data

    # New (recommended)
    from assured_sentinel.core.calibrator import ConformalCalibrator, CalibrationRunner

    # Or use the convenience functions
    from assured_sentinel.core.calibrator import calibrate, get_calibration_data

This module re-exports symbols from the new package for backward compatibility.
See CHANGELOG.md for migration guide.
"""

import warnings

warnings.warn(
    "The 'calibration' module is deprecated and will be removed in version 3.0. "
    "Use 'assured_sentinel.core.calibrator' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from assured_sentinel.core.calibrator import (
    ConformalCalibrator,
    CalibrationRunner,
    MBPPDatasetLoader,
    StaticDatasetLoader,
    calibrate,
    get_calibration_data,
)

__all__ = [
    "ConformalCalibrator",
    "CalibrationRunner",
    "MBPPDatasetLoader",
    "StaticDatasetLoader",
    "calibrate",
    "get_calibration_data",
]
