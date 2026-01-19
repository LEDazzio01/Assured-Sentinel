"""
Commander Module: Backward Compatibility Shim
=============================================

.. deprecated:: 2.0.0
    This module is deprecated. Use `assured_sentinel.core.commander` instead.

Example migration::

    # Old (deprecated)
    from commander import Commander

    # New (recommended)
    from assured_sentinel import Commander
    # or
    from assured_sentinel.core.commander import Commander

This module re-exports symbols from the new package for backward compatibility.
See CHANGELOG.md for migration guide.
"""

import warnings

warnings.warn(
    "The 'commander' module is deprecated and will be removed in version 3.0. "
    "Use 'assured_sentinel.core.commander' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from assured_sentinel.core.commander import Commander, JsonCalibrationStore

__all__ = ["Commander", "JsonCalibrationStore"]
