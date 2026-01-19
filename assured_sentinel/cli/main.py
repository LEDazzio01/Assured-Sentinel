"""
Assured Sentinel CLI.

A command-line interface for verifying Python code snippets against
the calibrated conformal prediction threshold.

Usage:
    sentinel verify "print('hello')"
    sentinel verify --file script.py
    sentinel calibrate --alpha 0.1
    sentinel demo
    sentinel scan ./src --recursive
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import logging
import os
import sys
from pathlib import Path
from typing import NoReturn

from assured_sentinel import __version__
from assured_sentinel.config import Settings, get_settings
from assured_sentinel.core.commander import Commander
from assured_sentinel.core.scorer import BanditScorer
from assured_sentinel.models import VerificationStatus

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def setup_logging(level: str = "INFO") -> None:
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# =============================================================================
# Commands
# =============================================================================

def cmd_verify(args: argparse.Namespace) -> int:
    """Handle the verify command."""
    # Get code from file or argument
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"{RED}Error: File '{args.file}' not found.{RESET}", file=sys.stderr)
            return 1
        code = filepath.read_text()
    else:
        code = args.code
    
    if not code:
        print(
            f"{RED}Error: No code provided. Use --file or provide code as argument.{RESET}",
            file=sys.stderr,
        )
        return 1
    
    # Initialize commander
    commander = Commander()
    if args.threshold is not None:
        commander.threshold = args.threshold
    
    # Run verification
    result = commander.verify(code)
    
    # Output format
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        status_symbol = "✅" if result.passed else "🚫"
        status_color = GREEN if result.passed else RED
        
        print(f"{status_color}{status_symbol} {result.status.value}{RESET}")
        print(f"   Score: {result.score:.4f}")
        print(f"   Threshold: {result.threshold:.4f}")
        if result.latency_ms:
            print(f"   Latency: {result.latency_ms:.1f}ms")
        if not result.passed:
            print(f"   Reason: {result.reason}")
    
    return 0 if result.passed else 1


def cmd_calibrate(args: argparse.Namespace) -> int:
    """Handle the calibrate command."""
    from assured_sentinel.core.calibrator import CalibrationRunner
    from assured_sentinel.models import CalibrationConfig
    
    config = CalibrationConfig(
        alpha=args.alpha,
        n_samples=args.samples,
        output_path=Path(args.output) if args.output else Path("calibration_data.json"),
    )
    
    print(f"{BOLD}Running calibration with α = {args.alpha}...{RESET}")
    
    try:
        runner = CalibrationRunner(config=config)
        data = runner.run(verbose=True)
        return 0
    except Exception as e:
        print(f"{RED}Calibration failed: {e}{RESET}", file=sys.stderr)
        return 1


def cmd_demo(args: argparse.Namespace) -> int:
    """Handle the demo command."""
    print(f"""
{BOLD}{'='*60}
🛡️  ASSURED SENTINEL - OFFLINE DEMO
{'='*60}{RESET}

This demo shows the core verification flow without requiring
an Azure OpenAI API key. We test pre-defined code samples.
""")
    
    # Initialize with demo threshold
    commander = Commander()
    commander.threshold = 0.15
    print(f"Threshold (q̂): {commander.threshold}\n")
    
    # Test cases
    test_cases = [
        ("Dangerous: exec() with user input", "exec(user_input)"),
        ("Dangerous: eval() with input", "result = eval(input('Enter: '))"),
        ("Dangerous: pickle.loads()", "import pickle\ndata = pickle.loads(untrusted)"),
        ("Safe: Simple factorial", "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"),
        ("Safe: Hello World", "print('Hello, World!')"),
        ("Safe: List comprehension", "squares = [x**2 for x in range(10)]"),
        ("Low Risk: Hardcoded password", "password = 'supersecret123'"),
        ("Low Risk: Weak random", "import random\nprint(random.random())"),
    ]
    
    passed = 0
    failed = 0
    
    print(f"{BOLD}Running {len(test_cases)} test cases...{RESET}\n")
    print("-" * 60)
    
    for description, code in test_cases:
        result = commander.verify(code)
        
        status_color = GREEN if result.passed else RED
        status_symbol = "✅" if result.passed else "🚫"
        
        print(f"{BLUE}📝 {description}{RESET}")
        print(f"   Code: {code[:50]}{'...' if len(code) > 50 else ''}")
        print(f"   Score: {result.score}")
        print(f"{status_color}   {status_symbol} {result.status.value}{RESET}")
        print()
        
        if result.passed:
            passed += 1
        else:
            failed += 1
    
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

{BOLD}📚 NEXT STEPS{RESET}
   1. Run calibration:     sentinel calibrate
   2. Launch dashboard:    streamlit run dashboard.py
   3. Full LLM loop:       python run_day5.py (requires Azure OpenAI)

{BOLD}{'='*60}{RESET}
""")
    
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """Scan a directory of Python files."""
    commander = Commander()
    if args.threshold:
        commander.threshold = args.threshold
    
    # Find Python files
    path = Path(args.path)
    if not path.exists():
        print(f"{RED}Error: Path '{args.path}' not found.{RESET}", file=sys.stderr)
        return 1
    
    if path.is_file():
        files = [path]
    else:
        pattern = "**/*.py" if args.recursive else "*.py"
        files = list(path.glob(pattern))
    
    if not files:
        print(f"{YELLOW}No Python files found in '{args.path}'{RESET}")
        return 0
    
    results = {"passed": 0, "rejected": 0, "files": []}
    
    for filepath in files:
        code = filepath.read_text()
        result = commander.verify(code)
        
        file_result = {
            "file": str(filepath),
            "status": result.status.value,
            "score": result.score,
        }
        results["files"].append(file_result)
        
        if result.passed:
            results["passed"] += 1
            if not args.quiet:
                print(f"{GREEN}✅ {filepath}: PASS (score: {result.score:.2f}){RESET}")
        else:
            results["rejected"] += 1
            print(f"{RED}🚫 {filepath}: REJECT (score: {result.score:.2f}){RESET}")
    
    # Summary
    print(f"\n{BOLD}--- Summary ---{RESET}")
    print(f"Total: {len(files)} | Passed: {results['passed']} | Rejected: {results['rejected']}")
    
    if args.json:
        print(json.dumps(results, indent=2))
    
    return 1 if results["rejected"] > 0 else 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run the LLM correction loop."""
    settings = get_settings()
    
    if not settings.has_azure_credentials:
        print(
            f"{RED}Error: Azure OpenAI credentials not configured.{RESET}",
            file=sys.stderr,
        )
        print("Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME")
        return 1
    
    from assured_sentinel.agents.analyst import AzureAnalyst
    
    async def run_loop():
        analyst = AzureAnalyst()
        commander = Commander()
        
        prompt = args.prompt or "Write a Python function to calculate factorial."
        max_retries = args.retries
        
        print(f"{BOLD}>>> User Request: {prompt}{RESET}\n")
        
        for attempt in range(1, max_retries + 1):
            print(f"{BLUE}--- Attempt {attempt}/{max_retries} ---{RESET}")
            
            try:
                code = await analyst.generate(prompt)
                print(f"[Analyst] Generated code (snippet):\n{code[:100]}...\n")
            except Exception as e:
                print(f"{RED}[!] Analyst Error: {e}{RESET}")
                break
            
            result = commander.verify(code)
            print(f"[Commander] {result.status.value} (Score: {result.score:.4f})")
            
            if result.passed:
                print(f"\n{GREEN}✅ SUCCESS! Assured code on attempt {attempt}.{RESET}")
                print(f"\n{BOLD}Final Code:{RESET}\n{code}")
                return 0
            else:
                print(f"{YELLOW}Adjusting prompt for retry...{RESET}\n")
                prompt = f"{prompt}\n\nIMPORTANT: Avoid security issues. Previous attempt was rejected."
        
        print(f"{RED}❌ Max retries exceeded.{RESET}")
        return 1
    
    return asyncio.run(run_loop())


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Assured Sentinel: Probabilistic Guardrails for AI-Generated Code",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a code snippet")
    verify_parser.add_argument("code", nargs="?", help="Python code to verify")
    verify_parser.add_argument("--file", "-f", help="Read code from file")
    verify_parser.add_argument(
        "--threshold", "-t", type=float, help="Override threshold"
    )
    verify_parser.add_argument(
        "--json", "-j", action="store_true", help="Output as JSON"
    )
    
    # calibrate command
    calibrate_parser = subparsers.add_parser("calibrate", help="Run calibration")
    calibrate_parser.add_argument(
        "--alpha", "-a", type=float, default=0.1, help="Risk tolerance (default: 0.1)"
    )
    calibrate_parser.add_argument(
        "--samples", "-n", type=int, default=100, help="Number of samples"
    )
    calibrate_parser.add_argument(
        "--output", "-o", help="Output file path"
    )
    
    # demo command
    demo_parser = subparsers.add_parser("demo", help="Run offline demo")
    
    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directory of Python files")
    scan_parser.add_argument("path", help="Directory path to scan")
    scan_parser.add_argument(
        "--recursive", "-r", action="store_true", help="Scan recursively"
    )
    scan_parser.add_argument("--threshold", "-t", type=float, help="Override threshold")
    scan_parser.add_argument(
        "--quiet", "-q", action="store_true", help="Only show rejections"
    )
    scan_parser.add_argument(
        "--json", "-j", action="store_true", help="Output as JSON"
    )
    
    # run command
    run_parser = subparsers.add_parser("run", help="Run LLM correction loop")
    run_parser.add_argument("prompt", nargs="?", help="Prompt for code generation")
    run_parser.add_argument(
        "--retries", "-r", type=int, default=3, help="Max retry attempts"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Dispatch to command handler
    commands = {
        "verify": cmd_verify,
        "calibrate": cmd_calibrate,
        "demo": cmd_demo,
        "scan": cmd_scan,
        "run": cmd_run,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
