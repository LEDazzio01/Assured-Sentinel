import numpy as np
from datasets import load_dataset
from scorer import calculate_non_conformity
import os

# Configuration
ALPHA = 0.1  # 10% Risk Tolerance
CALIBRATION_SIZE = 100 

def get_calibration_data(n=100):
    """
    Fetches 'Ground Truth' code samples and injects HEAVY synthetic noise.
    """
    print(f"--- Loading {n} samples from MBPP dataset ---")
    try:
        # Removed trust_remote_code to fix warning
        dataset = load_dataset("mbpp", split="test")
        samples = []
        for i, row in enumerate(dataset):
            if i >= n:
                break
            samples.append(row['code'])
            
        # --- AGGRESSIVE SYNTHETIC INJECTION ---
        # To force a non-zero threshold at Alpha=0.1 (10%), 
        # we must inject >10% vulnerable code. 
        # We will inject 20% (20 samples) to shift the distribution.
        
        print("--- Injecting 20% Synthetic Vulnerabilities ---")
        
        # A mix of High (1.0), Medium (0.5), and Low (0.1) issues
        bad_patterns = [
            "import pickle\npickle.loads(x)", # High
            "password = 'secret'", # Medium
            "eval(user_input)", # High
            "import random\nprint(random.random())", # Low
            "tmp = '/tmp/insecure'" # Medium
        ]
        
        # Cycle through bad patterns to fill 20 spots
        injection_count = 20
        for i in range(1, injection_count + 1):
            # Overwrite the last N samples
            pattern = bad_patterns[i % len(bad_patterns)]
            samples[-i] = pattern
            
        return samples
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return []

def calibrate(alpha=ALPHA):
    """
    The Mathematical Core: Calculates q_hat.
    """
    print(f"\n--- Starting Calibration Sequence (Alpha={alpha}) ---")
    
    # 1. Load Data
    code_samples = get_calibration_data(CALIBRATION_SIZE)
    if not code_samples:
        return 0.0

    # 2. Score Data
    scores = []
    print(f"Scoring {len(code_samples)} samples...")
    
    for i, code in enumerate(code_samples):
        score = calculate_non_conformity(code)
        scores.append(score)

    # 3. Calculate Threshold (q_hat)
    # Finite Sample Correction
    n = len(scores)
    q_level = np.ceil((n + 1) * (1 - alpha)) / n
    q_level = min(1.0, q_level)
    
    q_hat = np.quantile(scores, q_level, method='higher')
    
    print(f"\n--- Calibration Results ---")
    print(f"N: {n}")
    print(f"Alpha: {alpha}")
    print(f"Threshold (q_hat): {q_hat}")
    
    # Save this value! You will need it for Day 4 (The Commander).
    return q_hat

if __name__ == "__main__":
    calibrate()
