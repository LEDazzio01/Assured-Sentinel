#!/usr/bin/env python3
"""
Assured Sentinel - Offline Demo

This script demonstrates the core verification functionality without
requiring an Azure OpenAI API key. It tests the scorer and commander
with pre-defined code samples.

Usage:
    python demo.py
    # or
    make demo
"""

from commander import Commander
from scorer import calculate_score
import sys

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header():
    """Print demo header."""
    print(f"""
{BOLD}{'='*60}
🛡️  ASSURED SENTINEL - OFFLINE DEMO
{'='*60}{RESET}

This demo shows the core verification flow without requiring
an Azure OpenAI API key. We test pre-defined code samples.
""")


def print_result(description: str, code: str, score: float, decision: dict):
    """Pretty-print a verification result."""
    status_color = GREEN if decision['status'] == 'PASS' else RED
    status_emoji = '✅' if decision['status'] == 'PASS' else '🚫'
    
    print(f"{BLUE}📝 Testing:{RESET} {description}")
    print(f"{YELLOW}   Code:{RESET} {code[:60]}{'...' if len(code) > 60 else ''}")
    print(f"{YELLOW}   🔍 Bandit Score:{RESET} {score}")
    print(f"{status_color}   {status_emoji} Decision: {decision['status']} "
          f"(Score {score} {'<=' if decision['status'] == 'PASS' else '>'} "
          f"Threshold {decision['threshold']}){RESET}")
    if decision['status'] == 'REJECT':
        print(f"{RED}   Reason: {decision['reason']}{RESET}")
    print()


def run_demo():
    """Run the demonstration."""
    print_header()
    
    # Initialize Commander with demo threshold (ignore calibration file for demo)
    # This ensures consistent demo results regardless of calibration state
    print(f"{BOLD}Initializing Commander...{RESET}")
    
    # Force the threshold for demo consistency
    from unittest.mock import patch
    import os
    
    # Temporarily hide calibration file to force default threshold
    with patch.object(os.path, 'exists', lambda x: False if 'calibration' in x else os.path.exists.__wrapped__(x) if hasattr(os.path.exists, '__wrapped__') else True):
        commander = Commander(default_threshold=0.15)
    
    # Manually set threshold to ensure demo consistency
    commander.threshold = 0.15
    print(f"   Threshold (q̂): {commander.threshold}\n")
    
    # Test cases: (description, code_snippet, expected_outcome)
    test_cases = [
        (
            "Dangerous: exec() with user input",
            "exec(user_input)",
            "REJECT"
        ),
        (
            "Dangerous: eval() with input",
            "result = eval(input('Enter expression: '))",
            "REJECT"
        ),
        (
            "Dangerous: pickle.loads() - deserialization attack",
            "import pickle\ndata = pickle.loads(untrusted_data)",
            "REJECT"
        ),
        (
            "Safe: Simple factorial function",
            "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
            "PASS"
        ),
        (
            "Safe: Hello World",
            "print('Hello, World!')",
            "PASS"
        ),
        (
            "Safe: List comprehension",
            "squares = [x**2 for x in range(10)]",
            "PASS"
        ),
        (
            "Low Risk: Hardcoded password (passes at LOW)",
            "password = 'supersecret123'",
            "PASS"  # Bandit flags as LOW severity = 0.1, below threshold
        ),
        (
            "Low Risk: Weak random (typically passes)",
            "import random\nprint(random.random())",
            "PASS"  # LOW severity = 0.1, below default threshold
        ),
    ]
    
    print(f"{BOLD}Running {len(test_cases)} test cases...{RESET}\n")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for description, code, expected in test_cases:
        score = calculate_score(code)
        decision = commander.verify(code)
        
        print_result(description, code, score, decision)
        
        if decision['status'] == expected:
            passed += 1
        else:
            failed += 1
            print(f"{RED}   ⚠️  Expected {expected}, got {decision['status']}{RESET}\n")
    
    # Summary
    print("-" * 60)
    print(f"""
{BOLD}📊 DEMO SUMMARY{RESET}
   Total tests: {len(test_cases)}
   {GREEN}Passed: {passed}{RESET}
   {RED if failed > 0 else GREEN}Failed: {failed}{RESET}

{BOLD}🔑 KEY TAKEAWAYS{RESET}
   • Dangerous patterns (exec, eval, pickle.loads) → REJECTED
   • Safe functional code → ACCEPTED  
   • Medium severity issues → REJECTED (score > threshold)
   • Low severity issues → Often ACCEPTED (score ≤ threshold)
   • Fail-closed: If Bandit can't parse it, it's REJECTED

{BOLD}📚 NEXT STEPS{RESET}
   1. Run calibration:     python calibration.py
   2. Launch dashboard:    streamlit run dashboard.py
   3. Full LLM loop:       python run_day5.py (requires Azure OpenAI)

{BOLD}{'='*60}{RESET}
""")
    
    return 0 if failed == 0 else 1


def main():
    """Main entry point."""
    try:
        sys.exit(run_demo())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Demo interrupted.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Error running demo: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
