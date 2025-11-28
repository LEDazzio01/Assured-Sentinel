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
    Strips Markdown code blocks (```python ... ```) to ensure valid syntax.
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
    # 0. Pre-flight Check
    if not shutil.which("bandit"):
        logger.error("CRITICAL: 'bandit' executable not found in PATH.")
        return 1.0 # Fail Safe

    # 1. Sanitize Code
    clean_code = _clean_code(code_snippet)
    
    # 2. Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(clean_code)
        temp_file_path = temp_file.name

    try:
        # 3. Run Bandit Analysis
        # -f json: Machine readable output
        # -q: Quiet (no banner)
        # --exit-zero: Ensure script doesn't crash on finding errors
        # -ll: Log level (ensure we catch everything)
        result = subprocess.run(
            ['bandit', '-f', 'json', '-q', '--exit-zero', temp_file_path],
            capture_output=True,
            text=True
        )
        
        # 4. Parse Results
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error(f"Bandit JSON parse failed. Stderr: {result.stderr}")
            return 1.0 

        results = report.get('results', [])
        
        # DEBUG: Log what happened
        if results:
            logger.warning(f"Bandit found {len(results)} issues.")
        else:
            logger.info("Bandit found 0 issues (Clean).")
            
        if not results:
            return 0.0 # Clean Code

        # 5. Deterministic Scoring Logic
        max_severity_score = 0.0
        
        for issue in results:
            severity = issue.get('issue_severity', 'LOW')
            confidence = issue.get('issue_confidence', 'LOW') # Optional: Use confidence too
            
            logger.warning(f"Issue Found: {issue.get('test_id')} - {severity} Severity")
            
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
        # 6. Cleanup
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass