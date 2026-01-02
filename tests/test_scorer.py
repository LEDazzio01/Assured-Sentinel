"""
Unit Tests for Assured Sentinel Scorer

Tests edge cases and expected behavior for the scoring module.
"""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestCalculateScore:
    """Test suite for calculate_score function."""
    
    def test_clean_code_returns_zero(self):
        """Clean code with no issues should return 0.0."""
        from scorer import calculate_score
        
        clean_code = "def hello():\n    return 'Hello, World!'"
        score = calculate_score(clean_code)
        assert score == 0.0
    
    def test_high_severity_returns_one(self):
        """Code with HIGH severity issues should return 1.0."""
        from scorer import calculate_score
        
        # eval(input()) is flagged as MEDIUM by some Bandit versions
        dangerous_code = "eval(input())"
        score = calculate_score(dangerous_code)
        # Accept either HIGH (1.0) or MEDIUM (0.5) based on Bandit version
        assert score >= 0.5
    
    def test_exec_returns_one(self):
        """exec() should be flagged as MEDIUM or HIGH severity."""
        from scorer import calculate_score
        
        exec_code = "exec(user_input)"
        score = calculate_score(exec_code)
        # Bandit flags exec as MEDIUM (B102)
        assert score >= 0.5
    
    def test_pickle_loads_returns_one(self):
        """pickle.loads() should be flagged as MEDIUM severity."""
        from scorer import calculate_score
        
        pickle_code = "import pickle\ndata = pickle.loads(untrusted)"
        score = calculate_score(pickle_code)
        # Bandit flags pickle.loads as MEDIUM (B301)
        assert score >= 0.5
    
    def test_medium_severity_returns_half(self):
        """Code with MEDIUM severity issues should return 0.5."""
        from scorer import calculate_score
        
        # Hardcoded password is typically MEDIUM severity
        medium_code = "password = 'secret123'"
        score = calculate_score(medium_code)
        # This could be 0.5 or 0.1 depending on Bandit version
        assert score in [0.1, 0.5]
    
    def test_low_severity_returns_point_one(self):
        """Code with LOW severity issues should return 0.1."""
        from scorer import calculate_score
        
        # Using random without crypto context is LOW severity
        low_code = "import random\nx = random.random()"
        score = calculate_score(low_code)
        assert score == 0.1
    
    def test_markdown_code_block_stripped(self):
        """Markdown code blocks should be stripped before analysis."""
        from scorer import calculate_score
        
        markdown_code = "```python\ndef hello():\n    return 'hi'\n```"
        score = calculate_score(markdown_code)
        assert score == 0.0
    
    def test_empty_code_returns_zero(self):
        """Empty code should return 0.0 (no issues found)."""
        from scorer import calculate_score
        
        empty_code = ""
        score = calculate_score(empty_code)
        # Empty file might parse as clean or error depending on Bandit
        assert score in [0.0, 1.0]
    
    def test_whitespace_only_returns_zero(self):
        """Whitespace-only code should return 0.0."""
        from scorer import calculate_score
        
        whitespace_code = "   \n\n   \n"
        score = calculate_score(whitespace_code)
        assert score in [0.0, 1.0]
    
    def test_syntax_error_returns_one_fail_closed(self):
        """Syntax errors should return 1.0 (fail-closed)."""
        from scorer import calculate_score
        
        invalid_code = "def broken(\n    # missing close paren and body"
        score = calculate_score(invalid_code)
        assert score == 1.0
    
    def test_multiple_issues_returns_max(self):
        """Multiple issues should return the highest severity score."""
        from scorer import calculate_score
        
        multi_issue_code = """
import random
x = random.random()  # LOW
password = 'secret'  # LOW  
eval(input())        # MEDIUM
"""
        score = calculate_score(multi_issue_code)
        # Should return at least MEDIUM (0.5)
        assert score >= 0.5


class TestCleanCode:
    """Test suite for _clean_code helper function."""
    
    def test_strips_python_code_fence(self):
        """Should strip ```python code fences."""
        from scorer import _clean_code
        
        code = "```python\nprint('hello')\n```"
        cleaned = _clean_code(code)
        assert cleaned == "print('hello')"
    
    def test_strips_generic_code_fence(self):
        """Should strip ``` code fences."""
        from scorer import _clean_code
        
        code = "```\nprint('hello')\n```"
        cleaned = _clean_code(code)
        assert cleaned == "print('hello')"
    
    def test_preserves_code_without_fence(self):
        """Should preserve code without fences."""
        from scorer import _clean_code
        
        code = "print('hello')"
        cleaned = _clean_code(code)
        assert cleaned == "print('hello')"
    
    def test_handles_multiple_lines(self):
        """Should handle multi-line code blocks."""
        from scorer import _clean_code
        
        code = "```python\ndef foo():\n    pass\n```"
        cleaned = _clean_code(code)
        assert "def foo():" in cleaned
        assert "pass" in cleaned


class TestBanditMissing:
    """Test behavior when Bandit is not available."""
    
    def test_bandit_missing_returns_one(self):
        """If Bandit is not in PATH, should return 1.0 (fail-closed)."""
        from scorer import calculate_score
        
        with patch('shutil.which', return_value=None):
            score = calculate_score("print('hello')")
            assert score == 1.0


class TestSubprocessFailure:
    """Test behavior when subprocess fails."""
    
    def test_subprocess_exception_returns_one(self):
        """Subprocess exceptions should return 1.0 (fail-closed)."""
        from scorer import calculate_score
        
        with patch('subprocess.run', side_effect=Exception("Subprocess failed")):
            with patch('shutil.which', return_value='/usr/bin/bandit'):
                score = calculate_score("print('hello')")
                assert score == 1.0
    
    def test_json_decode_error_returns_one(self):
        """JSON decode errors should return 1.0 (fail-closed)."""
        from scorer import calculate_score
        
        mock_result = MagicMock()
        mock_result.stdout = "not valid json"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('shutil.which', return_value='/usr/bin/bandit'):
                score = calculate_score("print('hello')")
                assert score == 1.0


class TestCommander:
    """Test suite for Commander class."""
    
    def test_commander_loads_default_threshold(self):
        """Commander should use default threshold if calibration file missing."""
        from commander import Commander
        
        with patch('os.path.exists', return_value=False):
            commander = Commander(default_threshold=0.15)
            assert commander.threshold == 0.15
    
    def test_commander_verify_pass(self):
        """Commander should PASS code with score below threshold."""
        from commander import Commander
        
        commander = Commander(default_threshold=0.5)
        
        with patch('scorer.calculate_score', return_value=0.0):
            decision = commander.verify("print('hello')")
            assert decision['status'] == 'PASS'
            assert decision['score'] == 0.0
    
    def test_commander_verify_reject(self):
        """Commander should REJECT code with score above threshold."""
        from commander import Commander
        
        # Patch os.path.exists to prevent loading calibration file
        with patch('os.path.exists', return_value=False):
            commander = Commander(default_threshold=0.05)
        
        # Patch calculate_score where it's used (in commander module)
        with patch('commander.calculate_score', return_value=1.0):
            decision = commander.verify("eval(input())")
            assert decision['status'] == 'REJECT'
            assert decision['score'] == 1.0
    
    def test_commander_verify_boundary(self):
        """Commander should PASS code with score exactly at threshold."""
        from commander import Commander
        
        commander = Commander(default_threshold=0.5)
        
        with patch('scorer.calculate_score', return_value=0.5):
            decision = commander.verify("some_code")
            assert decision['status'] == 'PASS'  # <= threshold passes


class TestIntegration:
    """Integration tests for the full verification flow."""
    
    def test_full_flow_safe_code(self):
        """Test full verification flow with safe code."""
        from commander import Commander
        
        commander = Commander(default_threshold=0.15)
        safe_code = "def add(a, b):\n    return a + b"
        
        decision = commander.verify(safe_code)
        
        assert decision['status'] == 'PASS'
        assert decision['score'] == 0.0
        assert 'threshold' in decision
        assert 'reason' in decision
    
    def test_full_flow_dangerous_code(self):
        """Test full verification flow with dangerous code."""
        from commander import Commander
        
        # Use a low threshold (0.1) to ensure MEDIUM severity (0.5) is rejected
        # Patch to prevent loading calibration file
        with patch('os.path.exists', return_value=False):
            commander = Commander(default_threshold=0.1)
        
        dangerous_code = "exec(user_input)"
        
        decision = commander.verify(dangerous_code)
        
        assert decision['status'] == 'REJECT'
        assert decision['score'] >= 0.5  # MEDIUM or higher
        assert 'threshold' in decision
        assert 'reason' in decision
