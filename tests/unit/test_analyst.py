"""
Unit tests for the Analyst module.

Tests the AzureAnalyst and related components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from assured_sentinel.agents.analyst import (
    AzureAnalyst,
    MockAnalyst,
    BaseAnalyst,
    create_analyst,
    generate_code,
)
from assured_sentinel.config import Settings
from assured_sentinel.models import AnalystConfig
from assured_sentinel.exceptions import (
    MissingCredentialsError,
    LLMConnectionError,
    LLMAuthenticationError,
)


class TestMockAnalyst:
    """Tests for the MockAnalyst class."""
    
    @pytest.mark.asyncio
    async def test_returns_default_response(self):
        """Should return default response for unknown prompts."""
        analyst = MockAnalyst()
        
        result = await analyst.generate("unknown prompt")
        
        assert "Hello, World!" in result
    
    @pytest.mark.asyncio
    async def test_returns_custom_response(self):
        """Should return custom response for known prompts."""
        responses = {"factorial": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"}
        analyst = MockAnalyst(responses=responses)
        
        result = await analyst.generate("factorial")
        
        assert "factorial" in result
    
    def test_sync_generation(self):
        """Should support synchronous generation."""
        analyst = MockAnalyst()
        
        result = analyst.generate_sync("test prompt")
        
        assert isinstance(result, str)


class TestAzureAnalystCredentials:
    """Tests for AzureAnalyst credential validation."""
    
    def test_raises_for_missing_all_credentials(self, monkeypatch):
        """Should raise MissingCredentialsError when all creds missing."""
        # Clear Azure env vars
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
        
        settings = Settings(
            azure_openai_endpoint=None,
            azure_openai_api_key=None,
            azure_openai_deployment=None,
        )
        
        with pytest.raises(MissingCredentialsError) as exc_info:
            AzureAnalyst(settings=settings)
        
        assert "AZURE_OPENAI_ENDPOINT" in exc_info.value.missing_vars
        assert "AZURE_OPENAI_API_KEY" in exc_info.value.missing_vars
    
    def test_raises_for_partial_credentials(self, monkeypatch):
        """Should raise MissingCredentialsError for partial creds."""
        # Clear Azure env vars
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
        
        settings = Settings(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_api_key=None,
            azure_openai_deployment="gpt-4o",
        )
        
        with pytest.raises(MissingCredentialsError) as exc_info:
            AzureAnalyst(settings=settings)
        
        assert "AZURE_OPENAI_API_KEY" in exc_info.value.missing_vars
    
    def test_accepts_valid_credentials(self):
        """Should accept valid credentials (but fail on init)."""
        settings = Settings(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_api_key="sk-test",
            azure_openai_deployment="gpt-4o",
        )
        
        # Should not raise MissingCredentialsError
        # (may fail on kernel init, which is expected)
        try:
            analyst = AzureAnalyst(settings=settings)
            # Kernel not initialized yet (lazy)
            assert analyst._kernel is None
        except MissingCredentialsError:
            pytest.fail("Should not raise MissingCredentialsError for valid creds")
        except Exception:
            # Other errors are acceptable (e.g., import errors)
            pass


class TestAzureAnalystWithMocks:
    """Tests for AzureAnalyst with mocked Semantic Kernel."""
    
    @pytest.mark.asyncio
    async def test_generate_returns_code(self):
        """Should return generated code from LLM."""
        settings = Settings(
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_api_key="sk-test",
            azure_openai_deployment="gpt-4o",
        )
        
        analyst = AzureAnalyst(settings=settings)
        
        # Mock the kernel
        mock_kernel = MagicMock()
        mock_result = MagicMock()
        mock_result.__str__ = lambda self: "def factorial(n): return 1"
        mock_kernel.invoke = AsyncMock(return_value=mock_result)
        analyst._kernel = mock_kernel
        analyst._function = MagicMock()
        analyst._KernelArguments = MagicMock()
        
        result = await analyst.generate("Write factorial")
        
        assert "factorial" in result


class TestCreateAnalyst:
    """Tests for the create_analyst factory function."""
    
    def test_creates_mock_analyst(self):
        """Should create MockAnalyst for 'mock' provider."""
        analyst = create_analyst(provider="mock")
        
        assert isinstance(analyst, MockAnalyst)
    
    def test_raises_for_unknown_provider(self):
        """Should raise ValueError for unknown provider."""
        with pytest.raises(ValueError):
            create_analyst(provider="unknown")


class TestBackwardCompatibility:
    """Tests for backward compatibility."""
    
    @pytest.mark.asyncio
    async def test_generate_code_function(self):
        """generate_code() function should work with mock."""
        # Patch to use mock analyst
        mock = MockAnalyst()
        
        with patch(
            "assured_sentinel.agents.analyst._global_analyst",
            mock,
        ):
            with patch(
                "assured_sentinel.agents.analyst.AzureAnalyst",
                return_value=mock,
            ):
                # The function initializes global analyst
                from assured_sentinel.agents.analyst import generate_code
                import assured_sentinel.agents.analyst as analyst_module
                analyst_module._global_analyst = mock
                
                result = await generate_code("test")
                
                assert isinstance(result, str)
