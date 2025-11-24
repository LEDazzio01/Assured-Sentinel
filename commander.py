import pickle
import logging
from scorer import calculate_score # From Day 2

class Commander:
    def __init__(self, calibration_file="calibration_data.pkl"):
        self.threshold = self._load_threshold(calibration_file)
        print(f"Commander initialized with Risk Threshold (q_hat): {self.threshold}")

    def _load_threshold(self, filepath):
        """
        Loads the q_hat derived from Day 3's calibration.
        """
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                return data['q_hat']
        except FileNotFoundError:
            logging.error("Calibration file not found. Run calibration.py first.")
            raise

    def verify(self, code_snippet):
        """
        The Logic Gate.
        Returns: (bool, float, str) -> (is_assured, score, reason)
        """
        # 1. Calculate Non-Conformity Score (Inverse Security Score)
        score = calculate_score(code_snippet) # [cite: 25]
        
        # 2. Compare against calibrated threshold q_hat 
        is_assured = score <= self.threshold
        
        if is_assured:
            return True, score, "Code meets assurance standards."
        else:
            return False, score, f"REJECTED: Score {score} exceeds risk threshold {self.threshold}."