"""
Configuration management for Taiga MCP Server.
"""

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.domain.exceptions import ConfigurationError


class MCPConfig(BaseSettings):
    """
    MCP Server configuration settings.
    """

    mcp_server_name: str = Field(
        default="Taiga MCP Server", alias="MCP_SERVER_NAME", description="Name of the MCP server"
    )
    mcp_transport: str = Field(
        default="stdio", alias="MCP_TRANSPORT", description="Transport protocol: stdio or http"
    )
    mcp_host: str = Field(
        default="127.0.0.1", alias="MCP_HOST", description="Host for HTTP transport"
    )
    mcp_port: int = Field(default=8000, alias="MCP_PORT", description="Port for HTTP transport")
    mcp_debug: bool = Field(default=False, alias="MCP_DEBUG", description="Enable debug mode")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("mcp_transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate transport protocol."""
        if v not in ["stdio", "http"]:
            raise ValueError(f"Invalid transport: {v}. Must be 'stdio' or 'http'")
        return v

    @field_validator("mcp_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError(f"Invalid port: {v}. Must be between 1 and 65535")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump(exclude_none=True)


class ServerConfig(BaseSettings):
    """
    MCP Server configuration settings.
    """

    mcp_server_name: str = Field(
        default="Taiga MCP Server", alias="MCP_SERVER_NAME", description="Name of the MCP server"
    )
    mcp_transport: str = Field(
        default="stdio", alias="MCP_TRANSPORT", description="Transport protocol: stdio or http"
    )
    mcp_host: str = Field(
        default="127.0.0.1", alias="MCP_HOST", description="Host for HTTP transport"
    )
    mcp_port: int = Field(default=8000, alias="MCP_PORT", description="Port for HTTP transport")
    mcp_debug: bool = Field(default=False, alias="MCP_DEBUG", description="Enable debug mode")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("mcp_transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate transport protocol."""
        if v not in ["stdio", "http"]:
            raise ValueError(f"Invalid transport: {v}. Must be 'stdio' or 'http'")
        return v

    @field_validator("mcp_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError(f"Invalid port: {v}. Must be between 1 and 65535")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump(exclude_none=True)


class TaigaConfig(BaseSettings):
    """
    Configuration for Taiga API connection.

    All settings are loaded from environment variables or .env file.
    """

    # Taiga API settings
    taiga_api_url: str = Field(..., alias="TAIGA_API_URL", description="Base URL for Taiga API")
    taiga_username: str = Field(
        ..., alias="TAIGA_USERNAME", description="Taiga username (email) for authentication"
    )
    taiga_password: str = Field(
        ..., alias="TAIGA_PASSWORD", description="Taiga password for authentication"
    )
    taiga_auth_token: str | None = Field(
        default=None, alias="TAIGA_AUTH_TOKEN", description="Pre-configured authentication token"
    )

    # Request settings
    timeout: float = Field(
        default=30.0, alias="TAIGA_TIMEOUT", description="Timeout in seconds for API requests"
    )
    auth_timeout: float = Field(
        default=30.0,
        alias="TAIGA_AUTH_TIMEOUT",
        description="Timeout in seconds for authentication requests",
    )
    max_retries: int = Field(
        default=3,
        alias="TAIGA_MAX_RETRIES",
        description="Maximum number of retries for failed requests",
    )
    max_auth_retries: int = Field(
        default=3,
        alias="TAIGA_MAX_AUTH_RETRIES",
        description="Maximum number of retries for authentication",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("taiga_api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate and normalize API URL."""
        # Check if URL has valid format
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL format: {v}. URL must start with http:// or https://")

        # Basic URL validation
        if len(v) < 10:  # Minimum valid URL would be like "http://x.y"
            raise ValueError(f"Invalid URL: {v}")

        # Remove trailing slash
        return v.rstrip("/")

    @field_validator("taiga_username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username is not empty and is a valid email."""
        if v is not None and v.strip() == "":
            raise ValueError("Username cannot be empty")

        # Validate email format
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError(f"Invalid email format: {v}")

        return v

    @field_validator("taiga_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password is not empty and meets minimum requirements."""
        if v is not None and v.strip() == "":
            raise ValueError("Password cannot be empty")

        # Validate minimum length
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")

        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        """Validate timeout is positive."""
        if v <= 0:
            raise ValueError(f"Timeout must be positive, got {v}")
        return v

    @field_validator("auth_timeout")
    @classmethod
    def validate_auth_timeout(cls, v: float) -> float:
        """Validate auth_timeout is positive."""
        if v <= 0:
            raise ValueError(f"Auth timeout must be positive, got {v}")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max_retries is non-negative and within limits."""
        if v < 0:
            raise ValueError(f"Max retries must be non-negative, got {v}")
        if v > 10:
            raise ValueError(f"Max retries cannot exceed 10, got {v}")
        return v

    @field_validator("max_auth_retries")
    @classmethod
    def validate_max_auth_retries(cls, v: int) -> int:
        """Validate max_auth_retries is non-negative."""
        if v < 0:
            raise ValueError(f"Max auth retries must be non-negative, got {v}")
        return v

    @property
    def api_url(self) -> str:
        """Alias for taiga_api_url for backward compatibility with container."""
        return self.taiga_api_url

    def has_credentials(self) -> bool:
        """Check if credentials are available for authentication."""
        return bool(self.taiga_auth_token or (self.taiga_username and self.taiga_password))

    def validate_for_authentication(self) -> None:
        """Validate that necessary authentication info is present."""
        if not self.has_credentials():
            raise ConfigurationError(
                "No authentication credentials provided. "
                "Set either TAIGA_AUTH_TOKEN or both TAIGA_USERNAME and TAIGA_PASSWORD"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary without sensitive data."""
        data = self.model_dump(exclude_none=True)
        # Remove sensitive data
        data.pop("taiga_password", None)
        data.pop("taiga_auth_token", None)
        return data

    def get_api_endpoint(self, endpoint: str) -> str:
        """
        Get full API endpoint URL.

        Args:
            endpoint: The endpoint path (e.g., 'auth', 'projects', etc.)

        Returns:
            Full URL for the endpoint
        """
        endpoint = endpoint.lstrip("/")
        return f"{self.taiga_api_url}/{endpoint}"

    def is_username_email(self) -> bool:
        """Check if username is an email address."""
        if not self.taiga_username:
            return False
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, self.taiga_username))

    def reload(self) -> None:
        """Reload configuration from environment variables."""
        # Re-read environment variables
        new_config = TaigaConfig()
        # Update current instance with new values
        for field in self.__class__.model_fields:
            setattr(self, field, getattr(new_config, field))

    def __str__(self) -> str:
        """String representation without sensitive data."""
        data = self.model_dump()
        # Hide sensitive data
        if data.get("taiga_password"):
            data["taiga_password"] = "***"
        if data.get("taiga_auth_token"):
            data["taiga_auth_token"] = "***"
        return " ".join([f"{k}={v!r}" for k, v in data.items()])

    def __repr__(self) -> str:
        """Representation without sensitive data."""
        return f"<TaigaConfig {self.__str__()}>"

    def handle_auth_error(self, error: Exception) -> None:
        """
        Handle authentication errors.

        Args:
            error: The authentication error

        Raises:
            ConfigurationError: With appropriate error message
        """
        error_msg = str(error)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            raise ConfigurationError(
                "Authentication failed. Please check your username and password."
            )
        if "404" in error_msg:
            raise ConfigurationError(
                f"API endpoint not found. Please check TAIGA_API_URL: {self.taiga_api_url}"
            )
        raise ConfigurationError(f"Authentication error: {error}")

    def should_retry_auth(self, attempt: int, error: Exception) -> bool:
        """
        Determine if authentication should be retried.

        Args:
            attempt: The current attempt number
            error: The error that occurred

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        error_msg = str(error).lower()
        # Don't retry on permanent failures
        if "401" in error_msg or "unauthorized" in error_msg:
            return False  # Bad credentials
        if "403" in error_msg or "forbidden" in error_msg:
            return False  # Access denied

        # Retry on temporary failures
        if "timeout" in error_msg or "connection" in error_msg:
            return True
        return "500" in error_msg or "502" in error_msg or "503" in error_msg  # Server errors

    def export_to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """
        Export configuration to dictionary.

        Args:
            include_secrets: Whether to include sensitive data

        Returns:
            Configuration as dictionary
        """
        data = self.model_dump()
        if not include_secrets:
            # Hide sensitive data
            if data.get("taiga_password"):
                data["taiga_password"] = "***"
            if data.get("taiga_auth_token"):
                data["taiga_auth_token"] = "***"
        return data


def load_config(env_file: str | None = None) -> tuple[TaigaConfig, ServerConfig]:
    """
    Load configuration from environment and/or .env file.

    Args:
        env_file: Path to .env file (optional)

    Returns:
        Tuple of (TaigaConfig, ServerConfig) instances with loaded settings
    """
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path, override=True)
    else:
        # Try to find .env in current directory or parent directories
        current_dir = Path.cwd()
        for parent in [current_dir, *list(current_dir.parents)]:
            env_path = parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                break

    return TaigaConfig(), ServerConfig()


# Global config instances
_taiga_config: TaigaConfig | None = None
_server_config: ServerConfig | None = None


def get_taiga_config() -> TaigaConfig:
    """
    Get the global Taiga configuration instance.

    Returns:
        TaigaConfig instance
    """
    global _taiga_config
    if _taiga_config is None:
        _taiga_config, _ = load_config()
    return _taiga_config


def get_server_config() -> ServerConfig:
    """
    Get the global server configuration instance.

    Returns:
        ServerConfig instance
    """
    global _server_config
    if _server_config is None:
        _, _server_config = load_config()
    return _server_config


def set_taiga_config(config: TaigaConfig) -> None:
    """
    Set the global Taiga configuration instance.

    Args:
        config: TaigaConfig instance to use globally
    """
    global _taiga_config
    _taiga_config = config


def set_server_config(config: ServerConfig) -> None:
    """
    Set the global server configuration instance.

    Args:
        config: ServerConfig instance to use globally
    """
    global _server_config
    _server_config = config
