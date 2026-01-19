"""
Analyst Module: Backward Compatibility Shim
===========================================

.. deprecated:: 2.0.0
    This module is deprecated. Use `assured_sentinel.agents.analyst` instead.

Example migration::

    # Old (deprecated)
    from analyst import Analyst

    # New (recommended)
    from assured_sentinel.agents.analyst import AzureAnalyst, MockAnalyst

    # Factory function
    from assured_sentinel.agents.analyst import generate_code

This module re-exports symbols from the new package for backward compatibility.
See CHANGELOG.md for migration guide.
"""

import warnings

warnings.warn(
    "The 'analyst' module is deprecated and will be removed in version 3.0. "
    "Use 'assured_sentinel.agents.analyst' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from assured_sentinel.agents.analyst import (
    BaseAnalyst,
    AzureAnalyst,
    MockAnalyst,
    Analyst,  # Alias for AzureAnalyst
    generate_code,
)

__all__ = [
    "BaseAnalyst",
    "AzureAnalyst",
    "MockAnalyst",
    "Analyst",
    "generate_code",
]
