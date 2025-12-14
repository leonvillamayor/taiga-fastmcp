"""
Logger setup and formatters.

Provides centralized logging configuration with custom formatters
that include correlation IDs and support for both console and file output.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from typing import Any

from src.infrastructure.logging.config import LoggingConfig
from src.infrastructure.logging.correlation import correlation_id_var


class TaigaLogFormatter(logging.Formatter):
    """
    Custom log formatter that includes correlation ID and masks sensitive data.

    This formatter extends the standard logging.Formatter to:
    - Include correlation ID from context
    - Mask sensitive fields (passwords, tokens, etc.)
    - Support JSON output format
    """

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        json_format: bool = False,
        sensitive_fields: list[str] | None = None,
    ) -> None:
        """
        Initialize the formatter.

        Args:
            fmt: Log format string
            datefmt: Date format string
            json_format: Whether to output in JSON format
            sensitive_fields: List of field names to mask
        """
        super().__init__(fmt, datefmt)
        self.json_format = json_format
        self.sensitive_fields = sensitive_fields or [
            "password",
            "auth_token",
            "token",
            "secret",
            "api_key",
        ]

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record."""
        # Add correlation ID to the record
        record.correlation_id = correlation_id_var.get() or "-"

        if self.json_format:
            return self._format_json(record)
        return super().format(record)

    def _format_json(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "correlation_id": getattr(record, "correlation_id", "-"),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = self._mask_sensitive(record.extra_data)

        return json.dumps(log_data, default=str)

    def _mask_sensitive(self, data: Any) -> Any:
        """Mask sensitive fields in data structures."""
        if isinstance(data, dict):
            return {
                k: "***MASKED***" if k.lower() in self.sensitive_fields else self._mask_sensitive(v)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._mask_sensitive(item) for item in data]
        return data


class CorrelationIdFilter(logging.Filter):
    """Filter that adds correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the record."""
        record.correlation_id = correlation_id_var.get() or "-"
        return True


_loggers: dict[str, logging.Logger] = {}
_logging_configured = False


def setup_logging(config: LoggingConfig | None = None) -> None:
    """
    Setup the logging system with the given configuration.

    Args:
        config: Logging configuration. If None, uses defaults.
    """
    global _logging_configured

    if _logging_configured:
        return

    if config is None:
        config = LoggingConfig()

    # Get root logger for the application
    root_logger = logging.getLogger("taiga_mcp")
    root_logger.setLevel(config.get_log_level_value())

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = TaigaLogFormatter(
        fmt=config.log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        json_format=config.log_json,
        sensitive_fields=config.log_sensitive_fields,
    )

    # Create correlation ID filter
    correlation_filter = CorrelationIdFilter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(config.get_log_level_value())
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if config.log_file:
        file_handler = RotatingFileHandler(
            filename=str(config.log_file),
            maxBytes=config.log_file_max_bytes,
            backupCount=config.log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(config.get_log_level_value())
        file_handler.setFormatter(formatter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)

    # Prevent propagation to root logger
    root_logger.propagate = False

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically module name)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Operation completed successfully")
    """
    # Ensure logging is configured
    if not _logging_configured:
        setup_logging()

    # Create child logger under taiga_mcp namespace
    full_name = f"taiga_mcp.{name}" if not name.startswith("taiga_mcp") else name

    if full_name not in _loggers:
        logger = logging.getLogger(full_name)
        _loggers[full_name] = logger

    return _loggers[full_name]


def reset_logging() -> None:
    """Reset logging configuration (useful for testing)."""
    global _logging_configured, _loggers
    _logging_configured = False
    _loggers.clear()

    # Clear handlers from root logger
    root_logger = logging.getLogger("taiga_mcp")
    root_logger.handlers.clear()
