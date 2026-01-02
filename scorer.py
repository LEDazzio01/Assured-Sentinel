"""
Scorer Module: Deterministic Security Scoring via Bandit
=========================================================

This module provides a non-conformity measure for code security by invoking
Bandit (Python SAST) and mapping findings to a 0.0-1.0 risk score.

TODO: PRODUCTION OPTIMIZATION
-----------------------------
The current implementation uses tempfile creation for each scoring request,
which creates an I/O bottleneck at scale:

    Current Throughput: ~100-200 req/s (disk I/O bound)
    Target Throughput:  1000+ req/s (required for CI/CD integration)

Bottleneck Analysis:
    1. tempfile.NamedTemporaryFile() → filesystem write (~1-5ms)
    2. Bandit subprocess spawn → process creation overhead (~10-50ms)
    3. Bandit file read → filesystem read (~1-5ms)
    4. os.remove() → filesystem delete (~1-2ms)

Proposed Architecture for Scale:

    Option A: Ramdisk (Quick Win)
    -----------------------------
    - Mount tmpfs at /dev/shm or dedicated ramdisk
    - Set tempfile.tempdir = '/dev/shm/sentinel'
    - Eliminates disk I/O, keeps process isolation
    - Expected: ~500-1000 req/s

    Option B: In-Memory AST Analysis (Maximum Performance)
    -------------------------------------------------------
    - Use bandit.core.BanditManager directly as library
    - Parse code to AST in-memory (ast.parse())
    - Run Bandit checks on AST without file I/O
    - Expected: ~5000+ req/s
    - Trade-off: Loses process isolation; crashes affect main process
    - Mitigation: Watchdog thread with timeout; worker pool pattern

    Option C: Microservice Architecture (Enterprise Scale)
    -------------------------------------------------------
    - Dedicated scorer microservice with worker pool
    - gRPC or HTTP/2 for low-latency communication
    - Horizontal scaling behind load balancer
    - Expected: Linear scaling with replicas
    - Trade-off: Operational complexity; network latency

Decision: Process isolation (subprocess) chosen for MVP stability.
See docs/Decision-log.md D-011 for full rationale.
"""

import subprocess
import tempfile
import os
import json
import logging
import shutil
import re

# Configure logger
logger = logging.getLogger("Commander")

def _clean_code(code: str) -> str:
    """
    Strips Markdown code blocks to isolate the Python code.
    """
    # Remove starting ```python or ```
    code = re.sub(r"^```[a-zA-Z]*\n", "", code.strip())
    # Remove ending ```
    code = re.sub(r"\n```$", "", code.strip())
    return code.strip()

def calculate_score(code_snippet: str) -> float:
    """
    Deterministically scores Python code using Bandit.
    Returns: 0.0 (Secure) to 1.0 (High Risk).
    """
    if not shutil.which("bandit"):
        logger.error("CRITICAL: 'bandit' executable not found in PATH.")
        return 1.0 # Fail Safe

    # 1. Sanitize Code
    clean_code = _clean_code(code_snippet)
    
    # 2. Create Temp File
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(clean_code)
        temp_file_path = temp_file.name

    try:
        # 3. Run Bandit
        result = subprocess.run(
            ['bandit', '-f', 'json', '-q', '--exit-zero', temp_file_path],
            capture_output=True,
            text=True
        )
        
        # 4. Parse Output
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error(f"Bandit JSON parse failed: {result.stderr}")
            return 1.0 

        # --- CRITICAL FIX: CHECK FOR PARSING ERRORS ---
        errors = report.get('errors', [])
        if errors:
            logger.warning(f"Bandit failed to parse the code (Syntax Error?): {errors}")
            return 1.0 # REJECT if we can't scan it

        # 5. Check Security Issues
        results = report.get('results', [])
        
        if not results:
            return 0.0 # Truly Clean

        max_severity_score = 0.0
        for issue in results:
            severity = issue.get('issue_severity', 'LOW')
            logger.warning(f"Issue: {issue.get('test_id')} ({severity})")
            
            if severity == 'HIGH':
                return 1.0 
            elif severity == 'MEDIUM':
                current_score = 0.5
            else:
                current_score = 0.1
            
            if current_score > max_severity_score:
                max_severity_score = current_score

        return max_severity_score

    except Exception as e:
        logger.error(f"Scorer System Failure: {e}")
        return 1.0 
        
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass