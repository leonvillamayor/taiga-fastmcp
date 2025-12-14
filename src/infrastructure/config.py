"""
Configuration management for Taiga MCP Server.
"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.domain.exceptions import ConfigurationError


class TaigaConfig(BaseSettings):
    """
    Configuration for Taiga API connection.

    All settings are loaded from environment variables or .env file.
    """

    # Taiga API settings
    api_url: str = Field(
        default="https://api.taiga.io/api/v1",
        alias="TAIGA_API_URL",
        description="Base URL for Taiga API",
    )
    username: str | None = Field(
        default=None,
        alias="TAIGA_USERNAME",
        description="Taiga username (email) for authentication",
    )
    password: str | None = Field(
        default=None, alias="TAIGA_PASSWORD", description="Taiga password for authentication"
    )
    auth_token: str | None = Field(
        default=None, alias="TAIGA_AUTH_TOKEN", description="Pre-configured authentication token"
    )

    # Request settings
    timeout: float = Field(
        default=30.0, alias="TAIGA_TIMEOUT", description="Timeout in seconds for API requests"
    )
    max_retries: int = Field(
        default=3,
        alias="TAIGA_MAX_RETRIES",
        description="Maximum number of retries for failed requests",
    )

    # MCP Server settings
    server_name: str = Field(
        default="taiga-mcp-server", alias="MCP_SERVER_NAME", description="Name of the MCP server"
    )
    transport: str = Field(
        default="stdio", alias="MCP_TRANSPORT", description="Transport protocol: stdio or http"
    )
    host: str = Field(default="127.0.0.1", alias="MCP_HOST", description="Host for HTTP transport")
    port: int = Field(default=8000, alias="MCP_PORT", description="Port for HTTP transport")
    debug: bool = Field(default=False, alias="MCP_DEBUG", description="Enable debug mode")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Ensure API URL doesn't end with slash."""
        return v.rstrip("/")

    @field_validator("transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate transport protocol."""
        if v not in ["stdio", "http"]:
            raise ValueError(f"Invalid transport: {v}. Must be 'stdio' or 'http'")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError(f"Invalid port: {v}. Must be between 1 and 65535")
        return v

    def has_credentials(self) -> bool:
        """Check if credentials are available for authentication."""
        return bool(self.auth_token or (self.username and self.password))

    def validate_for_authentication(self) -> None:
        """Validate that necessary authentication info is present."""
        if not self.has_credentials():
            raise ConfigurationError(
                "No authentication credentials provided. "
                "Set either TAIGA_AUTH_TOKEN or both TAIGA_USERNAME and TAIGA_PASSWORD"
            )


def load_config(env_file: str | None = None) -> TaigaConfig:
    """
    Load configuration from environment and/or .env file.

    Args:
        env_file: Path to .env file (optional)

    Returns:
        TaigaConfig instance with loaded settings
    """
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
    else:
        # Try to find .env in current directory or parent directories
        current_dir = Path.cwd()
        for parent in [current_dir, *list(current_dir.parents)]:
            env_path = parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                break

    return TaigaConfig()


# Global config instance
_config: TaigaConfig | None = None


def get_config() -> TaigaConfig:
    """
    Get the global configuration instance.

    Returns:
        TaigaConfig instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: TaigaConfig) -> None:
    """
    Set the global configuration instance.

    Args:
        config: TaigaConfig instance to use globally
    """
    global _config
    _config = config
