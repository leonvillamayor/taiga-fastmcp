"""
Logging configuration module.

Provides Pydantic-based configuration for the logging system,
following the same patterns used in src/config.py.
"""

import logging
from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfig(BaseSettings):
    """
    Configuration for the logging system.

    This configuration class follows the same pattern as TaigaConfig,
    using Pydantic BaseSettings for environment variable loading.

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format
        log_file: Path to log file (optional, if not set logs to console only)
        log_file_max_bytes: Maximum size of log file before rotation
        log_file_backup_count: Number of backup files to keep
        log_json: Whether to output logs in JSON format
        log_include_correlation_id: Whether to include correlation ID in logs
        log_include_timestamp: Whether to include timestamp in logs
        log_include_module: Whether to include module name in logs
        log_include_function: Whether to include function name in logs
    """

    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level",
    )

    log_format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        description="Log message format",
    )

    log_file: Path | None = Field(
        default=None,
        description="Path to log file (optional)",
    )

    log_file_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        description="Maximum size of log file before rotation",
    )

    log_file_backup_count: int = Field(
        default=5,
        description="Number of backup files to keep",
    )

    log_json: bool = Field(
        default=False,
        description="Whether to output logs in JSON format",
    )

    log_include_correlation_id: bool = Field(
        default=True,
        description="Whether to include correlation ID in logs",
    )

    log_include_timestamp: bool = Field(
        default=True,
        description="Whether to include timestamp in logs",
    )

    log_include_module: bool = Field(
        default=True,
        description="Whether to include module name in logs",
    )

    log_include_function: bool = Field(
        default=True,
        description="Whether to include function name in logs",
    )

    log_sensitive_fields: list[str] = Field(
        default=["password", "auth_token", "token", "secret", "api_key"],
        description="Fields to mask in logs for security",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="LOG_",
    )

    def get_log_level_value(self) -> int:
        """Get the numeric value of the log level."""
        level_map: dict[LogLevel, int] = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        return level_map[self.log_level]
