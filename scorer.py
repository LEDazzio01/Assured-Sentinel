import random

def calculate_score(code_snippet: str) -> float:
    """
    Simulates the Non-Conformity Measure (NCM).
    In a full prod environment, this runs 'bandit' analysis.
    
    Returns:
        float: 0.0 (Secure) to 1.0 (High Risk/Non-Conforming)
    """
    # 1. High Risk Patterns (simulating Bandit 'High' severity)
    if "import os" in code_snippet or "exec(" in code_snippet or "os.system" in code_snippet:
        return round(random.uniform(0.8, 1.0), 3)
        
    # 2. Medium Risk Patterns (simulating unverified requests, etc.)
    elif "requests.get" in code_snippet and "verify=False" in code_snippet:
        return round(random.uniform(0.4, 0.7), 3)
        
    # 3. Low/No Risk (Safe code)
    else:
        return round(random.uniform(0.0, 0.15), 3)