"""
Logging infrastructure module.

This module provides logging functionality for the Taiga MCP Server,
including configuration, formatters, handlers, and decorators for
automatic operation logging and error tracing.
"""

from src.infrastructure.logging.config import LoggingConfig, LogLevel
from src.infrastructure.logging.correlation import (
    CorrelationIdManager,
    correlation_id_var,
)
from src.infrastructure.logging.decorators import log_api_call, log_operation
from src.infrastructure.logging.logger import (
    TaigaLogFormatter,
    get_logger,
    setup_logging,
)
from src.infrastructure.logging.performance import (
    APIMetrics,
    EndpointMetricsStore,
    PerformanceLogger,
    get_performance_logger,
    reset_performance_logger,
)

__all__ = [
    "APIMetrics",
    "CorrelationIdManager",
    "EndpointMetricsStore",
    "LogLevel",
    "LoggingConfig",
    "PerformanceLogger",
    "TaigaLogFormatter",
    "correlation_id_var",
    "get_logger",
    "get_performance_logger",
    "log_api_call",
    "log_operation",
    "reset_performance_logger",
    "setup_logging",
]
