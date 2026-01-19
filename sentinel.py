"""
Sentinel Entry Point: Backward Compatibility Shim
=================================================

.. deprecated:: 2.0.0
    This module is deprecated. Use `sentinel` CLI command instead.

To run the CLI::

    sentinel --help
    sentinel verify "print('hello')"
    sentinel demo

This module provides the main entry point for backward compatibility.
See CHANGELOG.md for migration guide.
"""

import warnings

warnings.warn(
    "The 'sentinel' module is deprecated and will be removed in version 3.0. "
    "Use the 'sentinel' CLI command instead.",
    DeprecationWarning,
    stacklevel=2,
)

from assured_sentinel.cli.main import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
