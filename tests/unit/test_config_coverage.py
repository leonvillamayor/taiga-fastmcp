"""
Tests adicionales para mejorar la cobertura del módulo config.
"""

import os
from unittest.mock import patch

import pytest

from src.config import (
    ServerConfig,
    TaigaConfig,
    get_server_config,
    get_taiga_config,
    load_config,
    set_server_config,
    set_taiga_config,
)
from src.domain.exceptions import ConfigurationError


class TestLoadConfig:
    """Tests para la función load_config."""

    @pytest.mark.unit
    def test_load_config_with_env_file(self, tmp_path) -> None:
        """
        Verifica que load_config carga desde un archivo .env específico.
        """
        # Arrange
        env_file = tmp_path / ".env"
        env_content = """
TAIGA_API_URL=https://api.taiga.io/api/v1
TAIGA_USERNAME=test@example.com
TAIGA_PASSWORD=password123
MCP_SERVER_NAME=test-server
MCP_TRANSPORT=stdio
        """
        env_file.write_text(env_content)

        # Act
        with patch.dict(os.environ, {}, clear=True):
            taiga_cfg, server_cfg = load_config(str(env_file))

        # Assert
        assert taiga_cfg.taiga_api_url == "https://api.taiga.io/api/v1"
        assert taiga_cfg.taiga_username == "test@example.com"
        assert server_cfg.mcp_server_name == "test-server"

    @pytest.mark.unit
    def test_load_config_searches_parent_dirs(self, tmp_path) -> None:
        """
        Verifica que load_config busca .env en directorios padre.
        """
        # Arrange
        parent_dir = tmp_path / "parent"
        parent_dir.mkdir()
        env_file = parent_dir / ".env"
        env_content = """
TAIGA_API_URL=https://parent.taiga.io/api/v1
TAIGA_USERNAME=parent@example.com
TAIGA_PASSWORD=parentpass123
        """
        env_file.write_text(env_content)

        child_dir = parent_dir / "child"
        child_dir.mkdir()

        # Act
        with (
            patch("pathlib.Path.cwd", return_value=child_dir),
            patch.dict(os.environ, {}, clear=True),
        ):
            taiga_cfg, _server_cfg = load_config()

        # Assert
        assert taiga_cfg.taiga_api_url == "https://parent.taiga.io/api/v1"
        assert taiga_cfg.taiga_username == "parent@example.com"

    @pytest.mark.unit
    def test_load_config_without_env_file(self) -> None:
        """
        Verifica que load_config funciona sin archivo .env.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://env.taiga.io/api/v1",
                "TAIGA_USERNAME": "env@example.com",
                "TAIGA_PASSWORD": "envpass123",
            },
        ):
            # Act
            with patch("pathlib.Path.exists", return_value=False):
                taiga_cfg, _server_cfg = load_config()

            # Assert
            assert taiga_cfg.taiga_api_url == "https://env.taiga.io/api/v1"
            assert taiga_cfg.taiga_username == "env@example.com"


class TestGlobalConfigManagement:
    """Tests para gestión de configuración global."""

    def setup_method(self) -> None:
        """Reset global config before each test."""
        import src.config

        src.config._taiga_config = None
        src.config._server_config = None

    @pytest.mark.unit
    def test_get_taiga_config_creates_singleton(self) -> None:
        """
        Verifica que get_taiga_config crea una instancia singleton.
        """
        # Arrange
        import src.config

        src.config._taiga_config = None

        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://singleton.taiga.io/api/v1",
                "TAIGA_USERNAME": "singleton@example.com",
                "TAIGA_PASSWORD": "singletonpass123",
            },
        ):
            # Act
            config1 = get_taiga_config()
            config2 = get_taiga_config()

            # Assert
            assert config1 is config2  # Same instance
            assert config1.taiga_api_url == "https://singleton.taiga.io/api/v1"

    @pytest.mark.unit
    def test_set_taiga_config(self) -> None:
        """
        Verifica que set_taiga_config actualiza la configuración global.
        """
        # Arrange
        import src.config

        src.config._taiga_config = None  # Reset

        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://new.taiga.io/api/v1",
                "TAIGA_USERNAME": "new@example.com",
                "TAIGA_PASSWORD": "newpass123",
            },
            clear=True,
        ):
            new_config = TaigaConfig()

            # Act
            set_taiga_config(new_config)
            retrieved = src.config._taiga_config

            # Assert
            assert retrieved is new_config
            assert retrieved.taiga_api_url == "https://new.taiga.io/api/v1"

    @pytest.mark.unit
    def test_get_server_config_creates_singleton(self) -> None:
        """
        Verifica que get_server_config crea una instancia singleton.
        """
        # Arrange
        import src.config

        src.config._server_config = None

        # Act
        config1 = get_server_config()
        config2 = get_server_config()

        # Assert
        assert config1 is config2

    @pytest.mark.unit
    def test_set_server_config(self) -> None:
        """
        Verifica que set_server_config actualiza la configuración global.
        """
        # Arrange
        import src.config

        src.config._server_config = None  # Reset

        with patch.dict(
            os.environ,
            {"MCP_SERVER_NAME": "new-server", "MCP_TRANSPORT": "http", "MCP_PORT": "9000"},
            clear=True,
        ):
            new_config = ServerConfig()

            # Act
            set_server_config(new_config)
            retrieved = src.config._server_config

            # Assert
            assert retrieved is new_config
            assert retrieved.mcp_server_name == "new-server"
            assert retrieved.mcp_port == 9000


class TestAuthenticationErrorHandling:
    """Tests para manejo de errores de autenticación."""

    @pytest.mark.unit
    def test_handle_auth_error_401(self) -> None:
        """
        Verifica manejo de error 401 unauthorized.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )
        error = Exception("401 Unauthorized")

        # Act & Assert
        with pytest.raises(ConfigurationError, match="Authentication failed"):
            config.handle_auth_error(error)

    @pytest.mark.unit
    def test_handle_auth_error_404(self) -> None:
        """
        Verifica manejo de error 404 not found.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )
        error = Exception("404 Not Found")

        # Act & Assert
        with pytest.raises(ConfigurationError, match="API endpoint not found"):
            config.handle_auth_error(error)

    @pytest.mark.unit
    def test_handle_auth_error_generic(self) -> None:
        """
        Verifica manejo de error genérico.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )
        error = Exception("Connection timeout")

        # Act & Assert
        with pytest.raises(ConfigurationError, match="Authentication error: Connection timeout"):
            config.handle_auth_error(error)


class TestAuthRetryLogic:
    """Tests para lógica de reintentos de autenticación."""

    @pytest.mark.unit
    def test_should_retry_auth_max_attempts_exceeded(self) -> None:
        """
        Verifica que no se reintenta cuando se exceden los intentos máximos.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
            max_retries=3,
        )
        error = Exception("timeout")

        # Act
        result = config.should_retry_auth(attempt=4, error=error)

        # Assert
        assert result is False

    @pytest.mark.unit
    def test_should_retry_auth_401_unauthorized(self) -> None:
        """
        Verifica que no se reintenta con error 401.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )
        error = Exception("401 Unauthorized")

        # Act
        result = config.should_retry_auth(attempt=1, error=error)

        # Assert
        assert result is False

    @pytest.mark.unit
    def test_should_retry_auth_403_forbidden(self) -> None:
        """
        Verifica que no se reintenta con error 403.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )
        error = Exception("403 Forbidden")

        # Act
        result = config.should_retry_auth(attempt=1, error=error)

        # Assert
        assert result is False

    @pytest.mark.unit
    def test_should_retry_auth_timeout(self) -> None:
        """
        Verifica que sí se reintenta con timeout.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )
        error = Exception("Connection timeout")

        # Act
        result = config.should_retry_auth(attempt=1, error=error)

        # Assert
        assert result is True

    @pytest.mark.unit
    def test_should_retry_auth_server_error(self) -> None:
        """
        Verifica que sí se reintenta con errores de servidor.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )

        # Act & Assert
        assert config.should_retry_auth(1, Exception("500 Internal Server Error")) is True
        assert config.should_retry_auth(1, Exception("502 Bad Gateway")) is True
        assert config.should_retry_auth(1, Exception("503 Service Unavailable")) is True

    @pytest.mark.unit
    def test_should_retry_auth_unknown_error(self) -> None:
        """
        Verifica comportamiento con error desconocido.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )
        error = Exception("Unknown error")

        # Act
        result = config.should_retry_auth(attempt=1, error=error)

        # Assert
        assert result is False


class TestConfigurationExportMethods:
    """Tests para métodos de exportación de configuración."""

    @pytest.mark.unit
    def test_export_to_dict_with_secrets(self) -> None:
        """
        Verifica export_to_dict con secretos incluidos.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://test.taiga.io/api/v1",
                "TAIGA_USERNAME": "test@example.com",
                "TAIGA_PASSWORD": "testpass123",
                "TAIGA_AUTH_TOKEN": "secret-token",
            },
            clear=True,
        ):
            config = TaigaConfig()

            # Act
            result = config.export_to_dict(include_secrets=True)

            # Assert
            assert result["taiga_password"] == "testpass123"
            assert result["taiga_auth_token"] == "secret-token"

    @pytest.mark.unit
    def test_export_to_dict_without_secrets(self) -> None:
        """
        Verifica export_to_dict sin secretos.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://test.taiga.io/api/v1",
                "TAIGA_USERNAME": "test@example.com",
                "TAIGA_PASSWORD": "testpass123",
                "TAIGA_AUTH_TOKEN": "secret-token",
            },
            clear=True,
        ):
            config = TaigaConfig()

            # Act
            result = config.export_to_dict(include_secrets=False)

            # Assert
            assert result["taiga_password"] == "***"
            assert result["taiga_auth_token"] == "***"

    @pytest.mark.unit
    def test_export_to_dict_without_token(self) -> None:
        """
        Verifica export_to_dict cuando no hay token.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="testpass123",
        )

        # Act
        result = config.export_to_dict(include_secrets=False)

        # Assert
        assert result["taiga_password"] == "***"
        assert "taiga_auth_token" in result  # Key exists
        assert result["taiga_auth_token"] is None  # But value is None


class TestConfigurationStringRepresentation:
    """Tests para representación en string de configuración."""

    @pytest.mark.unit
    def test_taiga_config_str_hides_password(self) -> None:
        """
        Verifica que __str__ oculta el password.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="supersecret123",
        )

        # Act
        string_repr = str(config)

        # Assert
        assert "supersecret123" not in string_repr
        assert "***" in string_repr

    @pytest.mark.unit
    def test_taiga_config_repr_hides_password(self) -> None:
        """
        Verifica que __repr__ oculta el password.
        """
        # Arrange
        config = TaigaConfig(
            taiga_api_url="https://test.taiga.io/api/v1",
            taiga_username="test@example.com",
            taiga_password="supersecret123",
            taiga_auth_token="token123",
        )

        # Act
        repr_str = repr(config)

        # Assert
        assert "supersecret123" not in repr_str
        assert "token123" not in repr_str
        assert "***" in repr_str
