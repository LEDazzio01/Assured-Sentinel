"""
Pytest fixtures and configuration for Assured Sentinel tests.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import json

from assured_sentinel.models import (
    CalibrationData,
    ScoringConfig,
    VerificationConfig,
    VerificationResult,
    VerificationStatus,
)


# =============================================================================
# Sample Code Fixtures
# =============================================================================

@pytest.fixture
def safe_code() -> str:
    """Sample safe Python code."""
    return "def hello():\n    return 'Hello, World!'"


@pytest.fixture
def dangerous_exec_code() -> str:
    """Code with exec() - should be flagged."""
    return "exec(user_input)"


@pytest.fixture
def dangerous_eval_code() -> str:
    """Code with eval() - should be flagged."""
    return "result = eval(input('Enter: '))"


@pytest.fixture
def dangerous_pickle_code() -> str:
    """Code with pickle.loads() - should be flagged."""
    return "import pickle\ndata = pickle.loads(untrusted)"


@pytest.fixture
def low_severity_code() -> str:
    """Code with LOW severity issue (random)."""
    return "import random\nx = random.random()"


@pytest.fixture
def syntax_error_code() -> str:
    """Code with syntax error."""
    return "def broken(\n    # missing close paren"


@pytest.fixture
def markdown_wrapped_code() -> str:
    """Code wrapped in markdown fences."""
    return "```python\ndef hello():\n    return 'hi'\n```"


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def scoring_config() -> ScoringConfig:
    """Default scoring configuration."""
    return ScoringConfig(
        timeout_seconds=30,
        fail_closed=True,
        use_ramdisk=False,
    )


@pytest.fixture
def verification_config(tmp_path: Path) -> VerificationConfig:
    """Verification config with temp calibration path."""
    return VerificationConfig(
        default_threshold=0.15,
        calibration_path=tmp_path / "calibration_data.json",
    )


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_bandit_clean_output() -> str:
    """Mock Bandit output for clean code."""
    return json.dumps({
        "errors": [],
        "generated_at": "2024-01-01T00:00:00Z",
        "metrics": {},
        "results": [],
    })


@pytest.fixture
def mock_bandit_medium_output() -> str:
    """Mock Bandit output with MEDIUM severity issue."""
    return json.dumps({
        "errors": [],
        "results": [
            {
                "test_id": "B102",
                "issue_severity": "MEDIUM",
                "issue_confidence": "HIGH",
                "issue_text": "Use of exec detected.",
                "line_number": 1,
            }
        ],
    })


@pytest.fixture
def mock_bandit_high_output() -> str:
    """Mock Bandit output with HIGH severity issue."""
    return json.dumps({
        "errors": [],
        "results": [
            {
                "test_id": "B301",
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "issue_text": "Pickle usage detected.",
                "line_number": 2,
            }
        ],
    })


@pytest.fixture
def mock_bandit_syntax_error_output() -> str:
    """Mock Bandit output for code with syntax errors."""
    return json.dumps({
        "errors": [
            {
                "filename": "test.py",
                "reason": "syntax error",
            }
        ],
        "results": [],
    })


# =============================================================================
# Calibration Fixtures
# =============================================================================

@pytest.fixture
def sample_calibration_data() -> CalibrationData:
    """Sample calibration data."""
    return CalibrationData(
        q_hat=0.15,
        alpha=0.1,
        n_samples=100,
        scores=[0.0] * 80 + [0.1] * 10 + [0.5] * 5 + [1.0] * 5,
        dataset="test",
        dataset_hash="abc123",
        scorer="bandit",
    )


@pytest.fixture
def calibration_file(tmp_path: Path, sample_calibration_data: CalibrationData) -> Path:
    """Create a temporary calibration file."""
    path = tmp_path / "calibration_data.json"
    with open(path, "w") as f:
        json.dump(sample_calibration_data.model_dump(mode="json"), f, default=str)
    return path


# =============================================================================
# Scorer Fixtures
# =============================================================================

@pytest.fixture
def mock_scorer():
    """Mock scorer that returns configurable scores."""
    scorer = MagicMock()
    scorer.score.return_value = 0.0
    return scorer


# =============================================================================
# Integration Test Fixtures
# =============================================================================

@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with Python files."""
    # Create some Python files
    (tmp_path / "safe.py").write_text("def hello():\n    return 'Hello!'")
    (tmp_path / "unsafe.py").write_text("exec(user_input)")
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.py").write_text("print('nested')")
    
    return tmp_path
