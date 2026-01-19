"""
Unit tests for the Commander module.

Tests the Commander class and JsonCalibrationStore.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from assured_sentinel.core.commander import (
    Commander,
    JsonCalibrationStore,
    create_commander,
)
from assured_sentinel.models import (
    CalibrationData,
    VerificationConfig,
    VerificationResult,
    VerificationStatus,
)
from assured_sentinel.exceptions import (
    CalibrationFileCorruptError,
)


class TestJsonCalibrationStore:
    """Tests for the JsonCalibrationStore class."""
    
    def test_exists_returns_false_for_missing_file(self, tmp_path: Path):
        """exists() should return False when file doesn't exist."""
        store = JsonCalibrationStore(tmp_path / "nonexistent.json")
        
        assert store.exists() is False
    
    def test_exists_returns_true_for_existing_file(self, calibration_file: Path):
        """exists() should return True when file exists."""
        store = JsonCalibrationStore(calibration_file)
        
        assert store.exists() is True
    
    def test_load_returns_none_for_missing_file(self, tmp_path: Path):
        """load() should return None when file doesn't exist."""
        store = JsonCalibrationStore(tmp_path / "nonexistent.json")
        
        result = store.load()
        
        assert result is None
    
    def test_load_returns_calibration_data(
        self, calibration_file: Path, sample_calibration_data: CalibrationData
    ):
        """load() should return CalibrationData for valid file."""
        store = JsonCalibrationStore(calibration_file)
        
        result = store.load()
        
        assert result is not None
        assert result.q_hat == sample_calibration_data.q_hat
        assert result.alpha == sample_calibration_data.alpha
    
    def test_load_raises_for_corrupt_file(self, tmp_path: Path):
        """load() should raise CalibrationFileCorruptError for invalid JSON."""
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json {{{")
        store = JsonCalibrationStore(path)
        
        with pytest.raises(CalibrationFileCorruptError):
            store.load()
    
    def test_save_creates_file(self, tmp_path: Path, sample_calibration_data: CalibrationData):
        """save() should create a valid JSON file."""
        path = tmp_path / "new_calibration.json"
        store = JsonCalibrationStore(path)
        
        store.save(sample_calibration_data)
        
        assert path.exists()
        with open(path) as f:
            data = json.load(f)
        assert data["q_hat"] == sample_calibration_data.q_hat


class TestCommander:
    """Tests for the Commander class."""
    
    def test_uses_default_threshold_when_no_calibration(self, tmp_path: Path):
        """Should use default threshold if calibration file missing."""
        config = VerificationConfig(
            default_threshold=0.25,
            calibration_path=tmp_path / "nonexistent.json",
        )
        
        commander = Commander(config=config)
        
        assert commander.threshold == 0.25
    
    def test_loads_threshold_from_calibration(self, calibration_file: Path):
        """Should load threshold from calibration file."""
        config = VerificationConfig(
            default_threshold=0.99,
            calibration_path=calibration_file,
        )
        
        commander = Commander(config=config)
        
        assert commander.threshold == 0.15  # From fixture
    
    def test_threshold_setter(self, tmp_path: Path):
        """Should allow manual threshold setting."""
        config = VerificationConfig(calibration_path=tmp_path / "none.json")
        commander = Commander(config=config)
        
        commander.threshold = 0.5
        
        assert commander.threshold == 0.5
    
    def test_threshold_setter_validation(self, tmp_path: Path):
        """Should reject invalid threshold values."""
        config = VerificationConfig(calibration_path=tmp_path / "none.json")
        commander = Commander(config=config)
        
        with pytest.raises(ValueError):
            commander.threshold = 1.5
        
        with pytest.raises(ValueError):
            commander.threshold = -0.1
    
    def test_verify_pass_for_low_score(self, mock_scorer, tmp_path: Path):
        """Should PASS when score <= threshold."""
        mock_scorer.score.return_value = 0.0
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=tmp_path / "none.json",
        )
        
        commander = Commander(scorer=mock_scorer, config=config)
        result = commander.verify("print('hello')")
        
        assert result.status == VerificationStatus.PASS
        assert result.score == 0.0
        assert result.passed is True
    
    def test_verify_reject_for_high_score(self, mock_scorer, tmp_path: Path):
        """Should REJECT when score > threshold."""
        mock_scorer.score.return_value = 0.5
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=tmp_path / "none.json",
        )
        
        commander = Commander(scorer=mock_scorer, config=config)
        result = commander.verify("exec(x)")
        
        assert result.status == VerificationStatus.REJECT
        assert result.score == 0.5
        assert result.passed is False
    
    def test_verify_pass_at_boundary(self, mock_scorer, tmp_path: Path):
        """Should PASS when score == threshold (boundary case)."""
        mock_scorer.score.return_value = 0.15
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=tmp_path / "none.json",
        )
        
        commander = Commander(scorer=mock_scorer, config=config)
        result = commander.verify("some_code")
        
        assert result.status == VerificationStatus.PASS
    
    def test_verify_includes_latency(self, mock_scorer, tmp_path: Path):
        """Verify result should include latency."""
        config = VerificationConfig(calibration_path=tmp_path / "none.json")
        commander = Commander(scorer=mock_scorer, config=config)
        
        result = commander.verify("print('hello')")
        
        assert result.latency_ms is not None
        assert result.latency_ms >= 0
    
    def test_verify_includes_reason(self, mock_scorer, tmp_path: Path):
        """Verify result should include reason."""
        mock_scorer.score.return_value = 0.5
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=tmp_path / "none.json",
        )
        
        commander = Commander(scorer=mock_scorer, config=config)
        result = commander.verify("exec(x)")
        
        assert "exceeds threshold" in result.reason
    
    def test_reload_calibration(
        self, tmp_path: Path, sample_calibration_data: CalibrationData
    ):
        """reload_calibration() should update threshold."""
        path = tmp_path / "calibration.json"
        config = VerificationConfig(
            default_threshold=0.1,
            calibration_path=path,
        )
        
        # Start without calibration
        commander = Commander(config=config)
        assert commander.threshold == 0.1
        
        # Create calibration file
        store = JsonCalibrationStore(path)
        store.save(sample_calibration_data)
        
        # Reload
        commander.reload_calibration()
        
        assert commander.threshold == 0.15


class TestIntegration:
    """Integration tests for Commander with real scorer."""
    
    def test_full_flow_safe_code(self, safe_code, tmp_path: Path):
        """Test full verification flow with safe code."""
        config = VerificationConfig(
            default_threshold=0.15,
            calibration_path=tmp_path / "none.json",
        )
        commander = Commander(config=config)
        
        result = commander.verify(safe_code)
        
        assert result.status == VerificationStatus.PASS
        assert result.score == 0.0
    
    def test_full_flow_dangerous_code(self, dangerous_exec_code, tmp_path: Path):
        """Test full verification flow with dangerous code."""
        config = VerificationConfig(
            default_threshold=0.1,
            calibration_path=tmp_path / "none.json",
        )
        commander = Commander(config=config)
        
        result = commander.verify(dangerous_exec_code)
        
        assert result.status == VerificationStatus.REJECT
        assert result.score >= 0.5


class TestCreateCommander:
    """Tests for the create_commander factory function."""
    
    def test_creates_default_commander(self):
        """Should create commander with default settings."""
        commander = create_commander()
        
        assert isinstance(commander, Commander)
    
    def test_creates_commander_with_threshold_override(self):
        """Should respect threshold override."""
        commander = create_commander(threshold=0.5)
        
        assert commander.threshold == 0.5
    
    def test_creates_commander_with_custom_path(self, tmp_path: Path):
        """Should respect custom calibration path."""
        path = tmp_path / "custom.json"
        
        commander = create_commander(calibration_path=path)
        
        # Should use default since file doesn't exist
        assert commander.threshold > 0
