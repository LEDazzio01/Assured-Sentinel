import subprocess
import json
import tempfile
import os

# Weights for Non-Conformity Calculation (MVP)
# We treat High severity as significantly more "non-conforming"
SEVERITY_WEIGHTS = {
    'LOW': 0.1,
    'MEDIUM': 0.5,
    'HIGH': 1.0
}

def extract_code_block(llm_response: str) -> str:
    """
    Extracts python code from markdown backticks.
    Crucial for ensuring Bandit analyzes code, not conversational filler.
    """
    if "```python" in llm_response:
        return llm_response.split("```python")[1].split("```")[0].strip()
    elif "```" in llm_response:
        return llm_response.split("```")[1].split("```")[0].strip()
    return llm_response

def calculate_non_conformity(code_str: str) -> float:
    """
    The NCM function s(x).
    Runs bandit against the code and returns a scalar score.
    """
    # Security: Write to a temp file to scan, then immediately destroy
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(code_str)
        tmp_path = tmp.name

    try:
        # Run bandit formatting as JSON for parsing
        result = subprocess.run(
            ['bandit', '-f', 'json', tmp_path], 
            capture_output=True, 
            text=True
        )
        
        # Bandit returns exit code 1 if issues found, 0 if none. 
        # We parse stdout regardless.
        data = json.loads(result.stdout)
        
        score = 0.0
        
        # Summing the weighted severity
        for result in data.get('results', []):
            severity = result.get('issue_severity', 'LOW')
            confidence = result.get('issue_confidence', 'LOW')
            
            # For MVP, we prioritize Severity. 
            # Future Scope: Factor in confidence to reduce False Positives.
            weight = SEVERITY_WEIGHTS.get(severity, 0.1)
            score += weight

        return float(score)

    except json.JSONDecodeError:
        # Fail-safe: If we can't parse the security report, 
        # we treat the code as maximum non-conforming (Unsafe).
        return 999.0
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# Unit Test for Day 2
if __name__ == "__main__":
    unsafe_code = """
import pickle
def load_data(data):
    return pickle.loads(data) # High severity issue
    """
    print(f"Non-Conformity Score: {calculate_non_conformity(unsafe_code)}")