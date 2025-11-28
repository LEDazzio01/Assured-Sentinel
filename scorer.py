import subprocess
import tempfile
import os
import json
import logging

logger = logging.getLogger("Commander")

def calculate_score(code_snippet: str) -> float:
    """
    Calculates the Non-Conformity Score using Bandit (SAST).
    
    Score Mapping:
    - 1.0: HIGH severity issues found (Immediate Reject)
    - 0.5: MEDIUM severity issues found
    - 0.1: LOW/Undefined issues found
    - 0.0: Clean code
    
    Args:
        code_snippet (str): The Python code to analyze.
        
    Returns:
        float: A deterministic score between 0.0 and 1.0.
    """
    # Create a temporary file to hold the code snippet
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code_snippet)
        temp_file_path = temp_file.name

    try:
        # Run bandit as a subprocess
        # -f json: Output as JSON
        # -q: Quiet mode
        # --exit-zero: Don't fail the build, just report
        result = subprocess.run(
            ['bandit', '-f', 'json', '-q', '--exit-zero', temp_file_path],
            capture_output=True,
            text=True
        )
        
        # Parse the JSON output
        report = json.loads(result.stdout)
        results = report.get('results', [])
        
        if not results:
            return 0.0

        # Determine the highest severity present
        max_severity_score = 0.0
        
        for issue in results:
            severity = issue.get('issue_severity', 'LOW')
            confidence = issue.get('issue_confidence', 'LOW')
            
            # Simple scoring logic
            if severity == 'HIGH':
                current_score = 1.0
            elif severity == 'MEDIUM':
                current_score = 0.5
            else:
                current_score = 0.1
            
            # We take the maximum risk found in the snippet
            if current_score > max_severity_score:
                max_severity_score = current_score

        return max_severity_score

    except Exception as e:
        logger.error(f"Scorer failed to run Bandit: {e}")
        # Fail open or closed? For safety, we fail closed (High Risk) if the tool breaks.
        return 1.0
        
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)