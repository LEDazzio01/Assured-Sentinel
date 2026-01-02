#!/usr/bin/env python3
"""
Assured Sentinel CLI

A command-line interface for verifying Python code snippets against
the calibrated conformal prediction threshold.

Usage:
    sentinel verify "print('hello')"
    sentinel verify --file script.py
    sentinel verify --alpha 0.05 "eval(input())"
    sentinel calibrate --alpha 0.1
    sentinel demo
"""

import argparse
import sys
import json
import os

def verify_code(code: str, alpha: float = None, threshold: float = None) -> dict:
    """Verify a code snippet and return the decision."""
    from commander import Commander
    from scorer import calculate_score
    
    # Use custom threshold if provided, otherwise load from calibration
    if threshold is not None:
        commander = Commander(default_threshold=threshold)
        commander.threshold = threshold
    else:
        commander = Commander(default_threshold=0.15)
    
    return commander.verify(code)


def cmd_verify(args):
    """Handle the verify command."""
    # Get code from file or argument
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            return 1
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        code = args.code
    
    if not code:
        print("Error: No code provided. Use --file or provide code as argument.", file=sys.stderr)
        return 1
    
    # Run verification
    result = verify_code(code, threshold=args.threshold)
    
    # Output format
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status_symbol = "✅" if result['status'] == 'PASS' else "🚫"
        print(f"{status_symbol} {result['status']}")
        print(f"   Score: {result['score']:.4f}")
        print(f"   Threshold: {result['threshold']:.4f}")
        if result['status'] == 'REJECT':
            print(f"   Reason: {result['reason']}")
    
    # Exit code: 0 for PASS, 1 for REJECT
    return 0 if result['status'] == 'PASS' else 1


def cmd_calibrate(args):
    """Handle the calibrate command."""
    from calibration import calibrate
    
    print(f"Running calibration with α = {args.alpha}...")
    q_hat = calibrate(alpha=args.alpha)
    print(f"\nCalibration complete. Threshold: {q_hat}")
    return 0


def cmd_demo(args):
    """Handle the demo command."""
    from demo import run_demo
    return run_demo()


def cmd_scan(args):
    """Scan a directory of Python files."""
    from commander import Commander
    from scorer import calculate_score
    import glob
    
    commander = Commander(default_threshold=args.threshold or 0.15)
    
    # Find Python files
    pattern = os.path.join(args.path, "**/*.py") if args.recursive else os.path.join(args.path, "*.py")
    files = glob.glob(pattern, recursive=args.recursive)
    
    if not files:
        print(f"No Python files found in '{args.path}'")
        return 0
    
    results = {"passed": 0, "rejected": 0, "files": []}
    
    for filepath in files:
        with open(filepath, 'r') as f:
            code = f.read()
        
        decision = commander.verify(code)
        result = {
            "file": filepath,
            "status": decision['status'],
            "score": decision['score']
        }
        results["files"].append(result)
        
        if decision['status'] == 'PASS':
            results["passed"] += 1
            if not args.quiet:
                print(f"✅ {filepath}: PASS (score: {decision['score']:.2f})")
        else:
            results["rejected"] += 1
            print(f"🚫 {filepath}: REJECT (score: {decision['score']:.2f})")
    
    # Summary
    print(f"\n--- Summary ---")
    print(f"Total: {len(files)} | Passed: {results['passed']} | Rejected: {results['rejected']}")
    
    if args.json:
        print(json.dumps(results, indent=2))
    
    # Exit with error if any rejections
    return 1 if results["rejected"] > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Assured Sentinel: Probabilistic Guardrails for AI-Generated Code"
    )
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a code snippet')
    verify_parser.add_argument('code', nargs='?', help='Python code to verify')
    verify_parser.add_argument('--file', '-f', help='Read code from file')
    verify_parser.add_argument('--threshold', '-t', type=float, help='Override threshold (default: from calibration)')
    verify_parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    verify_parser.set_defaults(func=cmd_verify)
    
    # calibrate command
    calibrate_parser = subparsers.add_parser('calibrate', help='Run calibration')
    calibrate_parser.add_argument('--alpha', '-a', type=float, default=0.1, help='Risk tolerance (default: 0.1)')
    calibrate_parser.set_defaults(func=cmd_calibrate)
    
    # demo command
    demo_parser = subparsers.add_parser('demo', help='Run offline demo')
    demo_parser.set_defaults(func=cmd_demo)
    
    # scan command
    scan_parser = subparsers.add_parser('scan', help='Scan directory of Python files')
    scan_parser.add_argument('path', help='Directory path to scan')
    scan_parser.add_argument('--recursive', '-r', action='store_true', help='Scan recursively')
    scan_parser.add_argument('--threshold', '-t', type=float, help='Override threshold')
    scan_parser.add_argument('--quiet', '-q', action='store_true', help='Only show rejections')
    scan_parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    scan_parser.set_defaults(func=cmd_scan)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
