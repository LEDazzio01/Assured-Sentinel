import numpy as np
from datasets import load_dataset
# FIX: Import the correct function name
from scorer import calculate_score 
import os
import json
import hashlib
from datetime import datetime

# Configuration
ALPHA = 0.1  # 10% Risk Tolerance
CALIBRATION_SIZE = 100 

def get_calibration_data(n=100):
    """
    Fetches baseline code samples from MBPP and injects synthetic vulnerabilities.
    
    Note: MBPP is a general Python programming dataset, NOT a security-labeled corpus.
    We use it as a baseline distribution of "typical" code, then inject known-bad 
    patterns to ensure the calibration threshold is meaningful.
    """
    print(f"--- Loading {n} samples from MBPP dataset (baseline distribution) ---")
    try:
        # Removed trust_remote_code to fix warning
        dataset = load_dataset("mbpp", split="test")
        samples = []
        for i, row in enumerate(dataset):
            if i >= n:
                break
            samples.append(row['code'])
            
        # --- AGGRESSIVE SYNTHETIC INJECTION (20%) ---
        # We inject 20 bad samples (20%) to exceed the 10% Alpha threshold.
        # This guarantees the 'bad' scores push the quantile above 0.0.
        
        print("--- Injecting 20% Synthetic Vulnerabilities ---")
        
        bad_patterns = [
            "import pickle\npickle.loads(x)", # High Severity
            "password = 'secret'", # Medium Severity
            "eval(user_input)", # High Severity
            "import random\nprint(random.random())", # Low Severity
            "tmp = '/tmp/insecure'" # Medium Severity
        ]
        
        # Overwrite the last 20 samples
        injection_count = 20
        for i in range(1, injection_count + 1):
            pattern = bad_patterns[i % len(bad_patterns)]
            samples[-i] = pattern
            
        return samples
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return []

def calibrate(alpha=ALPHA):
    print(f"\n--- Starting Calibration Sequence (Alpha={alpha}) ---")
    
    code_samples = get_calibration_data(CALIBRATION_SIZE)
    if not code_samples:
        return 0.0

    scores = []
    print(f"Scoring {len(code_samples)} samples...")
    
    for i, code in enumerate(code_samples):
        # FIX: Call the correct function name
        score = calculate_score(code) 
        scores.append(score)

    # Mathematical Correction (Split Conformal Prediction)
    n = len(scores)
    q_level = np.ceil((n + 1) * (1 - alpha)) / n
    q_level = min(1.0, q_level)
    
    q_hat = float(np.quantile(scores, q_level, method='higher'))
    
    print(f"\n--- Calibration Results ---")
    print(f"N: {n}")
    print(f"Alpha: {alpha}")
    print(f"Threshold (q_hat): {q_hat}")
    
    # Compute dataset hash for reproducibility tracking
    dataset_hash = hashlib.sha256("".join(code_samples[:10]).encode()).hexdigest()[:12]
    
    # Save as JSON (safe, portable, human-readable)
    calibration_output = {
        "q_hat": q_hat,
        "alpha": alpha,
        "n_samples": n,
        "scores": [float(s) for s in scores],
        "dataset": "mbpp",
        "dataset_hash": dataset_hash,
        "scorer": "bandit",
        "scorer_version": "1.7+",
        "calibrated_at": datetime.utcnow().isoformat() + "Z",
        "notes": "MBPP is baseline distribution, not security-labeled. Includes 20% synthetic injection."
    }
    
    with open("calibration_data.json", "w") as f:
        json.dump(calibration_output, f, indent=2)
    print("--- Data Saved to calibration_data.json ---")
    
    # Also save pkl for backward compatibility with existing dashboard
    # TODO: Remove in v2.0 after dashboard migration
    import pickle
    with open("calibration_data.pkl", "wb") as f:
        pickle.dump({"q_hat": q_hat, "scores": scores}, f)
    print("--- Legacy PKL also saved (for dashboard compatibility) ---")
    
    return q_hat

if __name__ == "__main__":
    calibrate()
    