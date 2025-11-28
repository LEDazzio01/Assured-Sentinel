import subprocess
import tempfile
import os
import json
import logging

# Configure logger just like in commander.py
logger = logging.getLogger("Commander")

def calculate_score(code_snippet: str) -> float:
    """
    REVISED (Day 4): Deterministic Security Scoring via Bandit.
    
    Returns:
        float: 
            0.0 (Secure) 
            0.1 - 0.9 (Low/Medium Risk)
            1.0 (High Risk - Immediate Rejection)
    """
    # 1. Create a temporary file to hold the Analyst's code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code_snippet)
        temp_file_path = temp_file.name

    try:
        # 2. Run Bandit Analysis
        # -f json: Machine readable output
        # -q: Quiet (no banner)
        # --exit-zero: Ensure script doesn't crash on finding errors
        result = subprocess.run(
            ['bandit', '-f', 'json', '-q', '--exit-zero', temp_file_path],
            capture_output=True,
            text=True
        )
        
        # 3. Parse Results
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error("Failed to parse Bandit JSON output.")
            return 1.0 # Fail Safe (Reject if we can't verify)

        results = report.get('results', [])
        
        if not results:
            return 0.0 # Clean Code

        # 4. Deterministic Scoring Logic
        max_severity_score = 0.0
        
        for issue in results:
            severity = issue.get('issue_severity', 'LOW')
            
            if severity == 'HIGH':
                return 1.0 # Immediate max score
            elif severity == 'MEDIUM':
                current_score = 0.5
            else:
                current_score = 0.1
            
            if current_score > max_severity_score:
                max_severity_score = current_score

        return max_severity_score

    except Exception as e:
        logger.error(f"Scorer System Failure: {e}")
        return 1.0 # Fail Safe
        
    finally:
        # 5. Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)