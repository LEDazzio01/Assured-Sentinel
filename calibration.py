import numpy as np
from datasets import load_dataset
from scorer import calculate_non_conformity
import os

# Configuration
ALPHA = 0.1  # 10% Risk Tolerance (90% Confidence)
CALIBRATION_SIZE = 100  # Number of samples

def get_calibration_data(n=100):
    """
    Fetches 'Ground Truth' code samples and injects synthetic noise.
    """
    print(f"--- Loading {n} samples from MBPP dataset ---")
    try:
        dataset = load_dataset("mbpp", split="test", trust_remote_code=True)
        samples = []
        for i, row in enumerate(dataset):
            if i >= n:
                break
            samples.append(row['code'])
            
        # --- SYNTHETIC INJECTION START ---
        # We inject ~5% 'bad' code to simulate a realistic environment 
        # where some code has minor or major issues.
        # This forces the math to calculate a non-zero threshold.
        
        print("--- Injecting Synthetic Vulnerabilities (Simulation Mode) ---")
        vulnerabilities = [
            "import pickle\ndef load(x): return pickle.loads(x)", # High Severity
            "password = 'password123'", # Low/Medium Severity
            "import subprocess\nsubprocess.call(cmd, shell=True)", # High Severity
            "import random\nprint(random.random())", # Low Severity (standard random warning)
            "tmp_file = '/tmp/tempfile'" # Medium (predictable path)
        ]
        
        # Replace the last few samples with vulnerable ones
        # We inject enough to challenge the alpha=0.1 (10%) boundary
        samples[-len(vulnerabilities):] = vulnerabilities
        # --- SYNTHETIC INJECTION END ---
        
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
        print("CRITICAL: No calibration data found.")
        return 0.0

    # 2. Score Data (The Scorer)
    scores = []
    print(f"Scoring {len(code_samples)} samples against Bandit security profile...")
    
    for i, code in enumerate(code_samples):
        score = calculate_non_conformity(code)
        scores.append(score)

    # 3. Calculate Threshold (q_hat)
    # Formula: q_hat = Quantile of scores at probability (n+1)(1-alpha)/n
    # This is the 'Finite Sample Correction'
    n = len(scores)
    q_level = np.ceil((n + 1) * (1 - alpha)) / n
    q_level = min(1.0, q_level) # Clip to max 1.0
    
    q_hat = np.quantile(scores, q_level, method='higher')
    
    print(f"\n--- Calibration Results ---")
    print(f"N (Samples): {n}")
    print(f"Alpha (Risk): {alpha}")
    print(f"Threshold (q_hat): {q_hat}")
    
    return q_hat

if __name__ == "__main__":
    calibrate()
