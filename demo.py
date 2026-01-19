"""
Demo Module: Backward Compatibility Shim
========================================

.. deprecated:: 2.0.0
    This module is deprecated. Use `sentinel demo` CLI command instead.

To run the demo::

    sentinel demo

This module provides the demo functionality for backward compatibility.
See CHANGELOG.md for migration guide.
"""

import warnings

warnings.warn(
    "The 'demo' module is deprecated and will be removed in version 3.0. "
    "Use 'sentinel demo' CLI command instead.",
    DeprecationWarning,
    stacklevel=2,
)

from assured_sentinel import Commander
from assured_sentinel.models import VerificationStatus


def main() -> None:
    """Run offline demonstration of Assured Sentinel."""
    print("\n" + "=" * 50)
    print("=== ASSURED SENTINEL - OFFLINE DEMO ===")
    print("=" * 50 + "\n")

    commander = Commander()
    print(f"📊 Using calibrated threshold: {commander.threshold:.2f}\n")

    test_cases = [
        ("exec(user_input)", "Dangerous exec() call"),
        ("eval(input())", "Dangerous eval() call"),
        ("import pickle; pickle.loads(data)", "Unsafe pickle deserialization"),
        ("def factorial(n): return 1 if n <= 1 else n * factorial(n-1)", "Safe recursive function"),
        ("print('Hello, World!')", "Safe print statement"),
        ("def add(a, b): return a + b", "Safe arithmetic function"),
    ]

    passed = 0
    rejected = 0

    for code, description in test_cases:
        result = commander.verify(code)
        status_emoji = "✅" if result.status == VerificationStatus.PASS else "🚫"
        decision = "PASS" if result.status == VerificationStatus.PASS else "REJECT"
        
        print(f"📝 Testing: {description}")
        print(f"   Code: {code[:50]}...")
        print(f"   🔍 Bandit Score: {result.score}")
        print(f"   {status_emoji} Decision: {decision}")
        print()
        
        if result.status == VerificationStatus.PASS:
            passed += 1
        else:
            rejected += 1

    print("=" * 50)
    print(f"📊 Summary: {passed} passed, {rejected} rejected")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
