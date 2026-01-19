"""
Scorer Module: Backward Compatibility Shim
==========================================

.. deprecated:: 2.0.0
    This module is deprecated. Use `assured_sentinel.core.scorer` instead.

Example migration::

    # Old (deprecated)
    from scorer import calculate_score, _clean_code

    # New (recommended)
    from assured_sentinel.core.scorer import BanditScorer, MarkdownCodeSanitizer

    # Or use the convenience functions
    from assured_sentinel.core.scorer import calculate_score, _clean_code

This module re-exports symbols from the new package for backward compatibility.
See CHANGELOG.md for migration guide.
"""

import warnings

warnings.warn(
    "The 'scorer' module is deprecated and will be removed in version 3.0. "
    "Use 'assured_sentinel.core.scorer' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from assured_sentinel.core.scorer import (
    BanditScorer,
    MarkdownCodeSanitizer,
    StandardTempFileManager,
    RamdiskTempFileManager,
    calculate_score,
    _clean_code,
)

__all__ = [
    "BanditScorer",
    "MarkdownCodeSanitizer",
    "StandardTempFileManager",
    "RamdiskTempFileManager",
    "calculate_score",
    "_clean_code",
]
