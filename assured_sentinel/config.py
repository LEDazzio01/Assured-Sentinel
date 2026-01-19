"""
Configuration management for Assured Sentinel.

This module provides centralized configuration using Pydantic Settings,
supporting environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables
    with the SENTINEL_ prefix (e.g., SENTINEL_ALPHA=0.05).
    
    Attributes:
        alpha: Risk tolerance for calibration (default: 0.1).
        default_threshold: Fallback threshold if no calibration (default: 0.15).
        calibration_path: Path to calibration data file.
        calibration_n_samples: Number of samples for calibration.
        scoring_timeout: Timeout for scoring operations in seconds.
        scoring_fail_closed: Return 1.0 on scoring errors.
        use_ramdisk: Use ramdisk for temp files (performance).
        ramdisk_path: Path to ramdisk mount point.
        log_level: Logging level.
        azure_openai_endpoint: Azure OpenAI endpoint URL.
        azure_openai_api_key: Azure OpenAI API key.
        azure_openai_deployment: Azure OpenAI deployment name.
        analyst_temperature: LLM temperature for code generation.
        analyst_top_p: Top-p sampling parameter.
        max_retries: Max retries in correction loop.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="SENTINEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Calibration settings
    alpha: float = Field(default=0.1, gt=0.0, lt=1.0)
    default_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    calibration_path: Path = Path("calibration_data.json")
    calibration_n_samples: int = Field(default=100, gt=0)
    
    # Scoring settings
    scoring_timeout: int = Field(default=30, gt=0)
    scoring_fail_closed: bool = True
    use_ramdisk: bool = False
    ramdisk_path: Path = Path("/dev/shm/sentinel")
    
    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    # Azure OpenAI settings (optional - for Analyst)
    azure_openai_endpoint: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_ENDPOINT",
    )
    azure_openai_api_key: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_API_KEY",
    )
    azure_openai_deployment: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_DEPLOYMENT_NAME",
    )
    
    # Analyst settings
    analyst_temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    analyst_top_p: float = Field(default=0.95, gt=0.0, le=1.0)
    
    # Retry settings
    max_retries: int = Field(default=3, ge=1)
    
    @property
    def has_azure_credentials(self) -> bool:
        """Check if Azure OpenAI credentials are configured."""
        return all([
            self.azure_openai_endpoint,
            self.azure_openai_api_key,
            self.azure_openai_deployment,
        ])


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Settings are loaded once and cached for performance.
    Call get_settings.cache_clear() to reload.
    
    Returns:
        Settings instance with values from environment.
    """
    return Settings()
