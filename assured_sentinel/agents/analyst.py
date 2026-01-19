"""
Analyst Module: LLM-based Code Generation.

This module provides code generation agents that interface with LLMs
to generate Python code based on user prompts.

The analyst follows the Open/Closed Principle by defining an abstract
base class that can be extended for different LLM providers.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from assured_sentinel.config import Settings, get_settings
from assured_sentinel.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    MissingCredentialsError,
)
from assured_sentinel.models import AnalystConfig

if TYPE_CHECKING:
    from assured_sentinel.protocols import ICodeGenerator

logger = logging.getLogger(__name__)


# =============================================================================
# Abstract Base Analyst
# =============================================================================

class BaseAnalyst(ABC):
    """
    Abstract base class for code generation agents.
    
    All LLM-based code generators should inherit from this class
    and implement the generate() method.
    """
    
    def __init__(self, config: AnalystConfig | None = None):
        """
        Initialize analyst.
        
        Args:
            config: Analyst configuration.
        """
        self._config = config or AnalystConfig()
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate code based on the given prompt.
        
        Args:
            prompt: User request describing desired code.
            
        Returns:
            Generated Python code.
            
        Raises:
            AnalystError: If code generation fails.
        """
        ...
    
    def generate_sync(self, prompt: str) -> str:
        """
        Synchronous wrapper for generate().
        
        Args:
            prompt: User request describing desired code.
            
        Returns:
            Generated Python code.
        """
        return asyncio.run(self.generate(prompt))


# =============================================================================
# Azure OpenAI Analyst
# =============================================================================

class AzureAnalyst(BaseAnalyst):
    """
    Code generation agent using Azure OpenAI via Semantic Kernel.
    
    This analyst uses high temperature (0.8) to drive stochastic
    proposal generation, allowing for creative code solutions.
    
    Environment Variables:
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
        AZURE_OPENAI_API_KEY: Azure OpenAI API key
        AZURE_OPENAI_DEPLOYMENT_NAME: Deployment name (e.g., gpt-4o)
    
    Example:
        >>> analyst = AzureAnalyst()
        >>> code = await analyst.generate("Write a function to calculate factorial")
        >>> print(code)
    """
    
    PROMPT_TEMPLATE = """
SYSTEM ROLE:
You are a Senior Python Engineer. You act as 'The Analyst'.
Your goal is to write functional, efficient Python code to solve the user's problem.
Do not explain the code excessively. Provide the code block clearly.

USER REQUEST:
{{$input}}
"""
    
    def __init__(
        self,
        config: AnalystConfig | None = None,
        settings: Settings | None = None,
    ):
        """
        Initialize Azure OpenAI analyst.
        
        Args:
            config: Analyst configuration.
            settings: Application settings.
            
        Raises:
            MissingCredentialsError: If Azure credentials are not configured.
        """
        super().__init__(config)
        self._settings = settings or get_settings()
        
        # Validate credentials
        self._validate_credentials()
        
        # Initialize Semantic Kernel (lazy)
        self._kernel = None
        self._function = None
    
    def _validate_credentials(self) -> None:
        """Validate that all required Azure credentials are present."""
        missing = []
        if not self._settings.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self._settings.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if not self._settings.azure_openai_deployment:
            missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        if missing:
            raise MissingCredentialsError(missing)
    
    def _initialize_kernel(self) -> None:
        """Initialize Semantic Kernel with Azure OpenAI service."""
        try:
            import semantic_kernel as sk
            from semantic_kernel.connectors.ai.open_ai import (
                AzureChatCompletion,
                AzureChatPromptExecutionSettings,
            )
            from semantic_kernel.functions import KernelArguments
        except ImportError as e:
            raise LLMConnectionError(
                "Azure OpenAI",
                details=f"semantic-kernel not installed: {e}",
            )
        
        self._kernel = sk.Kernel()
        self._KernelArguments = KernelArguments
        
        try:
            self._kernel.add_service(
                AzureChatCompletion(
                    service_id="analyst",
                    deployment_name=self._settings.azure_openai_deployment,
                    endpoint=self._settings.azure_openai_endpoint,
                    api_key=self._settings.azure_openai_api_key,
                )
            )
        except Exception as e:
            raise LLMConnectionError(
                "Azure OpenAI",
                self._settings.azure_openai_endpoint,
                str(e),
            )
        
        # Configure execution settings
        req_settings = AzureChatPromptExecutionSettings(service_id="analyst")
        req_settings.temperature = self._config.temperature
        req_settings.top_p = self._config.top_p
        
        self._function = self._kernel.add_function(
            plugin_name="AnalystPlugin",
            function_name="generate_code",
            prompt=self.PROMPT_TEMPLATE,
            prompt_execution_settings=req_settings,
        )
        
        logger.info("Semantic Kernel initialized for Azure OpenAI")
    
    async def generate(self, prompt: str) -> str:
        """
        Generate code using Azure OpenAI.
        
        Args:
            prompt: User request describing desired code.
            
        Returns:
            Generated Python code.
            
        Raises:
            AnalystError: If code generation fails.
        """
        if self._kernel is None:
            self._initialize_kernel()
        
        logger.info(f"Generating code for: '{prompt[:50]}...'")
        
        try:
            result = await self._kernel.invoke(
                self._function,
                self._KernelArguments(input=prompt),
            )
            return str(result)
        except Exception as e:
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "401" in error_msg:
                raise LLMAuthenticationError("Azure OpenAI")
            raise LLMConnectionError("Azure OpenAI", details=str(e))


# =============================================================================
# Mock Analyst (for testing/demo)
# =============================================================================

class MockAnalyst(BaseAnalyst):
    """
    Mock analyst for testing and demo purposes.
    
    Returns predefined responses without making LLM calls.
    """
    
    def __init__(self, responses: dict[str, str] | None = None):
        """
        Initialize mock analyst.
        
        Args:
            responses: Dict mapping prompts to responses.
        """
        super().__init__()
        self._responses = responses or {}
        self._default_response = 'def hello():\n    return "Hello, World!"'
    
    async def generate(self, prompt: str) -> str:
        """Return mock response."""
        return self._responses.get(prompt, self._default_response)


# =============================================================================
# Factory Function
# =============================================================================

def create_analyst(
    provider: str = "azure",
    settings: Settings | None = None,
) -> BaseAnalyst:
    """
    Factory function to create an analyst.
    
    Args:
        provider: LLM provider ("azure" or "mock").
        settings: Application settings.
        
    Returns:
        Configured analyst instance.
        
    Raises:
        ValueError: If provider is not supported.
    """
    if provider == "azure":
        return AzureAnalyst(settings=settings)
    elif provider == "mock":
        return MockAnalyst()
    else:
        raise ValueError(f"Unsupported provider: {provider}")


# =============================================================================
# Backward Compatibility
# =============================================================================

# Alias for backward compatibility
Analyst = AzureAnalyst

# Global analyst instance for backward compatibility
_global_analyst: AzureAnalyst | None = None


async def generate_code(user_request: str) -> str:
    """
    Generate code (backward compatibility function).
    
    This function maintains backward compatibility with run_day4.py
    and run_day5.py. For new code, use AzureAnalyst class directly.
    
    Args:
        user_request: User prompt.
        
    Returns:
        Generated code.
    """
    global _global_analyst
    if _global_analyst is None:
        _global_analyst = AzureAnalyst()
    return await _global_analyst.generate(user_request)
