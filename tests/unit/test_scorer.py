"""
Unit tests for the Scorer module.

Tests the BanditScorer, MarkdownCodeSanitizer, and related components.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

from assured_sentinel.core.scorer import (
    BanditScorer,
    MarkdownCodeSanitizer,
    StandardTempFileManager,
    RamdiskTempFileManager,
    calculate_score,
    _clean_code,
    create_scorer,
)
from assured_sentinel.models import ScoringConfig, Severity
from assured_sentinel.exceptions import (
    BanditNotFoundError,
    BanditParseError,
    ScoringTimeoutError,
)


class TestMarkdownCodeSanitizer:
    """Tests for the MarkdownCodeSanitizer class."""
    
    def test_strips_python_code_fence(self):
        """Should strip ```python code fences."""
        sanitizer = MarkdownCodeSanitizer()
        code = "```python\nprint('hello')\n```"
        
        result = sanitizer.sanitize(code)
        
        assert result == "print('hello')"
    
    def test_strips_generic_code_fence(self):
        """Should strip ``` code fences."""
        sanitizer = MarkdownCodeSanitizer()
        code = "```\nprint('hello')\n```"
        
        result = sanitizer.sanitize(code)
        
        assert result == "print('hello')"
    
    def test_preserves_code_without_fence(self):
        """Should preserve code without fences."""
        sanitizer = MarkdownCodeSanitizer()
        code = "print('hello')"
        
        result = sanitizer.sanitize(code)
        
        assert result == "print('hello')"
    
    def test_handles_empty_string(self):
        """Should handle empty string."""
        sanitizer = MarkdownCodeSanitizer()
        
        result = sanitizer.sanitize("")
        
        assert result == ""
    
    def test_handles_multiline_code(self):
        """Should handle multi-line code blocks."""
        sanitizer = MarkdownCodeSanitizer()
        code = "```python\ndef foo():\n    pass\n```"
        
        result = sanitizer.sanitize(code)
        
        assert "def foo():" in result
        assert "pass" in result
        assert "```" not in result


class TestStandardTempFileManager:
    """Tests for the StandardTempFileManager class."""
    
    def test_creates_temp_file(self):
        """Should create a temp file with content."""
        manager = StandardTempFileManager()
        content = "print('test')"
        
        path = manager.create(content)
        
        try:
            assert path.exists()
            assert path.read_text() == content
            assert path.suffix == ".py"
        finally:
            manager.cleanup(path)
    
    def test_cleanup_removes_file(self):
        """Should remove file on cleanup."""
        manager = StandardTempFileManager()
        path = manager.create("test")
        
        manager.cleanup(path)
        
        assert not path.exists()
    
    def test_cleanup_handles_nonexistent_file(self):
        """Should not raise error for nonexistent file."""
        manager = StandardTempFileManager()
        path = Path("/nonexistent/file.py")
        
        # Should not raise
        manager.cleanup(path)


class TestBanditScorer:
    """Tests for the BanditScorer class."""
    
    def test_clean_code_returns_zero(self, safe_code):
        """Clean code with no issues should return 0.0."""
        scorer = BanditScorer()
        
        score = scorer.score(safe_code)
        
        assert score == 0.0
    
    def test_exec_code_returns_medium_or_higher(self, dangerous_exec_code):
        """exec() should be flagged as MEDIUM or higher."""
        scorer = BanditScorer()
        
        score = scorer.score(dangerous_exec_code)
        
        assert score >= 0.5
    
    def test_eval_code_returns_medium_or_higher(self, dangerous_eval_code):
        """eval() should be flagged as MEDIUM or higher."""
        scorer = BanditScorer()
        
        score = scorer.score(dangerous_eval_code)
        
        assert score >= 0.5
    
    def test_pickle_code_returns_medium_or_higher(self, dangerous_pickle_code):
        """pickle.loads() should be flagged as MEDIUM or higher."""
        scorer = BanditScorer()
        
        score = scorer.score(dangerous_pickle_code)
        
        assert score >= 0.5
    
    def test_low_severity_returns_point_one(self, low_severity_code):
        """LOW severity issues should return 0.1."""
        scorer = BanditScorer()
        
        score = scorer.score(low_severity_code)
        
        assert score == 0.1
    
    def test_syntax_error_returns_one_fail_closed(self, syntax_error_code):
        """Syntax errors should return 1.0 (fail-closed)."""
        scorer = BanditScorer()
        
        score = scorer.score(syntax_error_code)
        
        assert score == 1.0
    
    def test_markdown_code_is_cleaned(self, markdown_wrapped_code):
        """Markdown code blocks should be stripped before analysis."""
        scorer = BanditScorer()
        
        score = scorer.score(markdown_wrapped_code)
        
        assert score == 0.0
    
    def test_empty_code(self):
        """Empty code should return 0.0 or 1.0."""
        scorer = BanditScorer()
        
        score = scorer.score("")
        
        assert score in [0.0, 1.0]
    
    def test_bandit_not_found_fail_closed(self):
        """Should return 1.0 when Bandit not found (fail-closed)."""
        config = ScoringConfig(fail_closed=True)
        scorer = BanditScorer(config=config)
        
        with patch("shutil.which", return_value=None):
            # Clear the cache
            scorer._find_bandit.cache_clear()
            score = scorer.score("print('hello')")
        
        assert score == 1.0
    
    def test_subprocess_timeout_fail_closed(self, safe_code):
        """Should return 1.0 on timeout (fail-closed)."""
        import subprocess
        
        config = ScoringConfig(fail_closed=True, timeout_seconds=1)
        scorer = BanditScorer(config=config)
        
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("bandit", 1)):
            with patch("shutil.which", return_value="/usr/bin/bandit"):
                scorer._find_bandit.cache_clear()
                score = scorer.score(safe_code)
        
        assert score == 1.0


class TestBanditScorerWithMocks:
    """Tests using mocked Bandit output."""
    
    def test_parse_clean_output(self, mock_bandit_clean_output):
        """Should parse clean Bandit output correctly."""
        scorer = BanditScorer()
        
        mock_result = MagicMock()
        mock_result.stdout = mock_bandit_clean_output
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            with patch("shutil.which", return_value="/usr/bin/bandit"):
                scorer._find_bandit.cache_clear()
                score = scorer.score("print('hello')")
        
        assert score == 0.0
    
    def test_parse_medium_severity_output(self, mock_bandit_medium_output):
        """Should parse MEDIUM severity output correctly."""
        scorer = BanditScorer()
        
        mock_result = MagicMock()
        mock_result.stdout = mock_bandit_medium_output
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            with patch("shutil.which", return_value="/usr/bin/bandit"):
                scorer._find_bandit.cache_clear()
                score = scorer.score("exec(x)")
        
        assert score == 0.5
    
    def test_parse_high_severity_output(self, mock_bandit_high_output):
        """Should parse HIGH severity output correctly."""
        scorer = BanditScorer()
        
        mock_result = MagicMock()
        mock_result.stdout = mock_bandit_high_output
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            with patch("shutil.which", return_value="/usr/bin/bandit"):
                scorer._find_bandit.cache_clear()
                score = scorer.score("pickle.loads(x)")
        
        assert score == 1.0
    
    def test_parse_syntax_error_output(self, mock_bandit_syntax_error_output):
        """Should handle syntax error output."""
        scorer = BanditScorer()
        
        mock_result = MagicMock()
        mock_result.stdout = mock_bandit_syntax_error_output
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            with patch("shutil.which", return_value="/usr/bin/bandit"):
                scorer._find_bandit.cache_clear()
                score = scorer.score("invalid syntax")
        
        assert score == 1.0


class TestBackwardCompatibility:
    """Tests for backward compatibility functions."""
    
    def test_calculate_score_function(self, safe_code):
        """calculate_score() should work as before."""
        score = calculate_score(safe_code)
        
        assert score == 0.0
    
    def test_clean_code_function(self):
        """_clean_code() should work as before."""
        code = "```python\nprint('hello')\n```"
        
        result = _clean_code(code)
        
        assert result == "print('hello')"


class TestCreateScorer:
    """Tests for the create_scorer factory function."""
    
    def test_creates_default_scorer(self):
        """Should create scorer with default settings."""
        scorer = create_scorer()
        
        assert isinstance(scorer, BanditScorer)
    
    def test_creates_scorer_with_custom_timeout(self):
        """Should respect timeout setting."""
        scorer = create_scorer(timeout_seconds=60)
        
        assert scorer._config.timeout_seconds == 60
    
    def test_creates_scorer_with_fail_open(self):
        """Should respect fail_closed setting."""
        scorer = create_scorer(fail_closed=False)
        
        assert scorer._config.fail_closed is False
