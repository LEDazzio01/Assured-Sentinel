import subprocess
import tempfile
import os
import json
import logging
import shutil

# Configure logger
logger = logging.getLogger("Commander")

def calculate_score(code_snippet: str) -> float:
    """
    Deterministically scores Python code using Bandit.
    Returns: 0.0 (Secure) to 1.0 (High Risk).
    """
    # 0. Pre-flight Check
    if not shutil.which("bandit"):
        logger.error("CRITICAL: 'bandit' executable not found in PATH.")
        return 1.0 # Fail Safe

    # 1. Create a temporary file
    # We use delete=False to ensure Windows compatibility, then clean up manually
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code_snippet)
        temp_file_path = temp_file.name

    try:
        # 2. Run Bandit Analysis
        result = subprocess.run(
            ['bandit', '-f', 'json', '-q', '--exit-zero', temp_file_path],
            capture_output=True,
            text=True
        )
        
        # 3. Parse Results
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            # If bandit output is empty or malformed
            logger.error(f"Bandit JSON parse failed. Stderr: {result.stderr}")
            return 1.0 

        results = report.get('results', [])
        
        if not results:
            return 0.0 # Clean Code

        # 4. Deterministic Scoring Logic
        max_severity_score = 0.0
        
        for issue in results:
            severity = issue.get('issue_severity', 'LOW')
            
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
        # 5. Cleanup
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass # Best effort cleanup