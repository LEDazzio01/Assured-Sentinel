"""
Unit tests for the Calibrator module.

Tests the ConformalCalibrator, CalibrationRunner, and dataset loaders.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

from assured_sentinel.core.calibrator import (
    ConformalCalibrator,
    CalibrationRunner,
    MBPPDatasetLoader,
    StaticDatasetLoader,
    SYNTHETIC_VULNERABILITIES,
    calibrate,
    get_calibration_data,
)
from assured_sentinel.models import CalibrationConfig, CalibrationData
from assured_sentinel.exceptions import InsufficientSamplesError, DatasetLoadError


class TestConformalCalibrator:
    """Tests for the ConformalCalibrator class."""
    
    def test_calibrate_computes_threshold(self):
        """Should compute valid threshold from scores."""
        calibrator = ConformalCalibrator()
        scores = [0.0, 0.0, 0.1, 0.1, 0.5, 0.5, 1.0, 1.0, 1.0, 1.0]
        
        q_hat = calibrator.calibrate(scores, alpha=0.1)
        
        assert 0.0 <= q_hat <= 1.0
    
    def test_calibrate_with_all_zeros(self):
        """Should handle all-zero scores."""
        calibrator = ConformalCalibrator()
        scores = [0.0] * 100
        
        q_hat = calibrator.calibrate(scores, alpha=0.1)
        
        assert q_hat == 0.0
    
    def test_calibrate_with_all_ones(self):
        """Should handle all-one scores."""
        calibrator = ConformalCalibrator()
        scores = [1.0] * 100
        
        q_hat = calibrator.calibrate(scores, alpha=0.1)
        
        assert q_hat == 1.0
    
    def test_calibrate_raises_for_insufficient_samples(self):
        """Should raise error for less than 2 samples."""
        calibrator = ConformalCalibrator()
        
        with pytest.raises(InsufficientSamplesError):
            calibrator.calibrate([0.0], alpha=0.1)
        
        with pytest.raises(InsufficientSamplesError):
            calibrator.calibrate([], alpha=0.1)
    
    def test_higher_alpha_gives_lower_threshold(self):
        """Higher alpha should generally give lower/equal threshold."""
        calibrator = ConformalCalibrator()
        scores = [0.0] * 80 + [0.5] * 10 + [1.0] * 10
        
        q_hat_low = calibrator.calibrate(scores, alpha=0.05)
        q_hat_high = calibrator.calibrate(scores, alpha=0.2)
        
        # Higher alpha = more tolerance = potentially lower threshold
        assert q_hat_high <= q_hat_low


class TestStaticDatasetLoader:
    """Tests for the StaticDatasetLoader class."""
    
    def test_loads_samples(self):
        """Should return provided samples."""
        samples = ["code1", "code2", "code3"]
        loader = StaticDatasetLoader(samples)
        
        result = loader.load(3)
        
        assert result == samples
    
    def test_limits_to_n_samples(self):
        """Should limit to n_samples."""
        samples = ["code1", "code2", "code3"]
        loader = StaticDatasetLoader(samples)
        
        result = loader.load(2)
        
        assert len(result) == 2


class TestMBPPDatasetLoader:
    """Tests for the MBPPDatasetLoader class."""
    
    def test_injects_vulnerabilities(self):
        """Should inject synthetic vulnerabilities."""
        loader = MBPPDatasetLoader(injection_rate=0.2)
        
        # Mock the dataset
        mock_dataset = [{"code": f"sample_{i}"} for i in range(100)]
        
        with patch("datasets.load_dataset", return_value=mock_dataset):
            samples = loader.load(100)
        
        # Check that some vulnerabilities were injected
        vulnerability_count = sum(
            1 for s in samples
            if any(v in s for v in SYNTHETIC_VULNERABILITIES)
        )
        
        assert vulnerability_count > 0
    
    def test_handles_dataset_error(self):
        """Should raise DatasetLoadError on failure."""
        loader = MBPPDatasetLoader()
        
        with patch(
            "datasets.load_dataset",
            side_effect=Exception("Network error"),
        ):
            with pytest.raises(DatasetLoadError):
                loader.load(100)


class TestCalibrationRunner:
    """Tests for the CalibrationRunner class."""
    
    def test_run_creates_calibration_data(self, tmp_path: Path):
        """Should produce valid CalibrationData."""
        # Create mock scorer
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = 0.0
        
        # Create static dataset
        static_loader = StaticDatasetLoader(["code"] * 10)
        
        config = CalibrationConfig(
            alpha=0.1,
            n_samples=10,
            output_path=tmp_path / "calibration.json",
        )
        
        runner = CalibrationRunner(
            scorer=mock_scorer,
            dataset_loader=static_loader,
            config=config,
        )
        
        data = runner.run(verbose=False)
        
        assert isinstance(data, CalibrationData)
        assert data.q_hat >= 0.0
        assert data.n_samples == 10
        assert len(data.scores) == 10
    
    def test_run_saves_to_file(self, tmp_path: Path):
        """Should save calibration data to file."""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = 0.0
        static_loader = StaticDatasetLoader(["code"] * 5)
        
        output_path = tmp_path / "calibration.json"
        config = CalibrationConfig(
            alpha=0.1,
            n_samples=5,
            output_path=output_path,
        )
        
        runner = CalibrationRunner(
            scorer=mock_scorer,
            dataset_loader=static_loader,
            config=config,
        )
        
        runner.run(verbose=False)
        
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert "q_hat" in data
    
    def test_run_uses_all_scores(self, tmp_path: Path):
        """Should score all samples."""
        mock_scorer = MagicMock()
        mock_scorer.score.side_effect = [0.0, 0.1, 0.5, 1.0, 0.0]
        static_loader = StaticDatasetLoader(["code"] * 5)
        
        config = CalibrationConfig(
            alpha=0.1,
            n_samples=5,
            output_path=tmp_path / "cal.json",
        )
        
        runner = CalibrationRunner(
            scorer=mock_scorer,
            dataset_loader=static_loader,
            config=config,
        )
        
        data = runner.run(verbose=False)
        
        assert mock_scorer.score.call_count == 5
        assert data.scores == [0.0, 0.1, 0.5, 1.0, 0.0]


class TestBackwardCompatibility:
    """Tests for backward compatibility functions."""
    
    def test_calibrate_function(self, tmp_path: Path, monkeypatch):
        """calibrate() function should work."""
        # Point to temp directory
        monkeypatch.chdir(tmp_path)
        
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = 0.0
        
        static_loader = StaticDatasetLoader(["code"] * 10)
        
        with patch(
            "assured_sentinel.core.scorer.BanditScorer",
            return_value=mock_scorer,
        ):
            with patch(
                "assured_sentinel.core.calibrator.MBPPDatasetLoader",
                return_value=static_loader,
            ):
                q_hat = calibrate(alpha=0.1, n_samples=10)
        
        assert isinstance(q_hat, float)
        assert 0.0 <= q_hat <= 1.0
