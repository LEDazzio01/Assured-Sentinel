"""
Integration tests for the full verification flow.

These tests verify that all components work together correctly.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

from assured_sentinel.core.commander import Commander, JsonCalibrationStore
from assured_sentinel.core.scorer import BanditScorer
from assured_sentinel.core.calibrator import (
    CalibrationRunner,
    StaticDatasetLoader,
    ConformalCalibrator,
)
from assured_sentinel.models import (
    VerificationStatus,
    VerificationConfig,
    CalibrationConfig,
    CalibrationData,
)


class TestFullVerificationFlow:
    """Integration tests for the complete verification pipeline."""
    
    def test_safe_code_passes(self, tmp_path: Path):
        """Safe code should pass verification."""
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=tmp_path / "cal.json",
        )
        commander = Commander(config=config)
        
        result = commander.verify("def add(a, b):\n    return a + b")
        
        assert result.status == VerificationStatus.PASS
        assert result.score == 0.0
    
    def test_dangerous_code_rejected(self, tmp_path: Path):
        """Dangerous code should be rejected."""
        config = VerificationConfig(
            default_threshold=0.1,
            calibration_path=tmp_path / "cal.json",
        )
        commander = Commander(config=config)
        
        result = commander.verify("exec(user_input)")
        
        assert result.status == VerificationStatus.REJECT
        assert result.score >= 0.5
    
    def test_calibration_affects_threshold(self, tmp_path: Path):
        """Calibration data should affect verification threshold."""
        # Create calibration with high threshold
        cal_path = tmp_path / "cal.json"
        calibration = CalibrationData(
            q_hat=0.9,  # Very permissive
            alpha=0.1,
            n_samples=100,
            scores=[0.0] * 100,
        )
        
        store = JsonCalibrationStore(cal_path)
        store.save(calibration)
        
        config = VerificationConfig(
            default_threshold=0.1,  # Would reject
            calibration_path=cal_path,
        )
        commander = Commander(config=config)
        
        # Medium severity code (0.5) should now pass
        result = commander.verify("exec(x)")
        
        assert commander.threshold == 0.9
        assert result.passed  # 0.5 <= 0.9


class TestCalibrationToVerificationFlow:
    """Tests for the calibration -> verification flow."""
    
    def test_calibration_produces_usable_threshold(self, tmp_path: Path):
        """Calibration should produce threshold usable by Commander."""
        # Run calibration
        mock_scorer = MagicMock()
        mock_scorer.score.side_effect = [0.0] * 80 + [0.5] * 15 + [1.0] * 5
        
        cal_path = tmp_path / "cal.json"
        config = CalibrationConfig(
            alpha=0.1,
            n_samples=100,
            output_path=cal_path,
        )
        
        runner = CalibrationRunner(
            scorer=mock_scorer,
            dataset_loader=StaticDatasetLoader(["code"] * 100),
            config=config,
        )
        
        data = runner.run(verbose=False)
        
        # Verify Commander can use the calibration
        ver_config = VerificationConfig(
            default_threshold=0.0,
            calibration_path=cal_path,
        )
        commander = Commander(config=ver_config)
        
        assert commander.threshold == data.q_hat
    
    def test_end_to_end_with_real_scorer(self, tmp_path: Path):
        """Full end-to-end test with real BanditScorer."""
        # Create test samples
        samples = [
            "def add(a, b): return a + b",  # Clean
            "print('hello')",  # Clean
            "x = [i*2 for i in range(10)]",  # Clean
            "exec(user_input)",  # Dangerous
            "eval(code)",  # Dangerous
        ]
        
        cal_path = tmp_path / "cal.json"
        config = CalibrationConfig(
            alpha=0.1,
            n_samples=5,
            injection_rate=0.0,  # No additional injection
            output_path=cal_path,
        )
        
        runner = CalibrationRunner(
            scorer=BanditScorer(),
            dataset_loader=StaticDatasetLoader(samples),
            config=config,
        )
        
        data = runner.run(verbose=False)
        
        # Now verify some code
        ver_config = VerificationConfig(calibration_path=cal_path)
        commander = Commander(config=ver_config)
        
        # Clean code should pass
        clean_result = commander.verify("def factorial(n): return 1 if n <= 1 else n * factorial(n-1)")
        assert clean_result.passed
        
        # Dangerous code should fail (unless threshold is very high)
        dangerous_result = commander.verify("exec(malicious_code)")
        # The result depends on calibration, but score should be high
        assert dangerous_result.score >= 0.5


class TestScanDirectory:
    """Integration tests for directory scanning."""
    
    def test_scan_finds_unsafe_files(self, temp_workspace: Path):
        """Should identify unsafe files in workspace."""
        from assured_sentinel.core.commander import Commander
        from assured_sentinel.models import VerificationConfig
        
        # Use a non-existent calibration path to force default threshold
        config = VerificationConfig(
            default_threshold=0.1,
            calibration_path=temp_workspace / "nonexistent_calibration.json",
        )
        commander = Commander(config=config)
        
        results = []
        for py_file in temp_workspace.rglob("*.py"):
            code = py_file.read_text()
            result = commander.verify(code)
            results.append((py_file.name, result))
        
        # Check results
        result_dict = {name: r for name, r in results}
        
        assert result_dict["safe.py"].passed
        assert not result_dict["unsafe.py"].passed


class TestErrorRecovery:
    """Tests for error handling and recovery."""
    
    def test_handles_corrupt_calibration_gracefully(self, tmp_path: Path):
        """Should handle corrupt calibration file gracefully."""
        cal_path = tmp_path / "corrupt.json"
        cal_path.write_text("not valid json {{{")
        
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=cal_path,
        )
        
        # Should not raise, should use default
        commander = Commander(config=config)
        
        assert commander.threshold == 0.15
    
    def test_handles_missing_calibration_gracefully(self, tmp_path: Path):
        """Should handle missing calibration file gracefully."""
        config = VerificationConfig(
            default_threshold=0.25,
            calibration_path=tmp_path / "nonexistent.json",
        )
        
        commander = Commander(config=config)
        
        assert commander.threshold == 0.25
    
    def test_verification_continues_after_scorer_error(self, tmp_path: Path):
        """Verification should continue even if scorer has issues."""
        # Create scorer that fails sometimes
        mock_scorer = MagicMock()
        mock_scorer.score.side_effect = [0.0, 1.0, 0.0]  # Second call returns fail-closed value
        
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=tmp_path / "none.json",
        )
        commander = Commander(scorer=mock_scorer, config=config)
        
        # First call succeeds
        r1 = commander.verify("code1")
        assert r1.passed
        
        # Second call returns high score (fail-closed)
        r2 = commander.verify("code2")
        assert not r2.passed
        
        # Third call succeeds again
        r3 = commander.verify("code3")
        assert r3.passed
