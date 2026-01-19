"""
Dashboard Module: Backward Compatibility Shim
=============================================

.. deprecated:: 2.0.0
    This module is deprecated. Use `assured_sentinel.dashboard.app` instead.

To run the dashboard, use::

    streamlit run assured_sentinel/dashboard/app.py

Or via CLI::

    sentinel dashboard

This module re-exports the main function for backward compatibility.
See CHANGELOG.md for migration guide.
"""

import warnings

warnings.warn(
    "The 'dashboard' module is deprecated and will be removed in version 3.0. "
    "Use 'assured_sentinel.dashboard.app' instead or run 'streamlit run assured_sentinel/dashboard/app.py'.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from assured_sentinel.dashboard.app import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
