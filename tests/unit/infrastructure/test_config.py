"""
Tests unitarios para el módulo de configuración de infraestructura.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.domain.exceptions import ConfigurationError
from src.infrastructure.config import TaigaConfig, get_config, load_config, set_config


@pytest.fixture(autouse=True)
def clean_env() -> None:
    """Limpia las variables de entorno de Taiga antes de cada test."""
    env_vars = [
        "TAIGA_API_URL",
        "TAIGA_USERNAME",
        "TAIGA_PASSWORD",
        "TAIGA_AUTH_TOKEN",
        "TAIGA_TIMEOUT",
        "TAIGA_MAX_RETRIES",
        "MCP_SERVER_NAME",
        "MCP_TRANSPORT",
        "MCP_HOST",
        "MCP_PORT",
        "MCP_DEBUG",
    ]
    # Guarda valores originales
    original_env = {var: os.environ.get(var) for var in env_vars}

    # Limpia las variables
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restaura valores originales
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture(autouse=True)
def reset_global_config() -> None:
    """Resetea la configuración global antes de cada test."""
    import src.infrastructure.config

    src.infrastructure.config._config = None
    yield
    src.infrastructure.config._config = None


class TestTaigaConfig:
    """Tests para la clase TaigaConfig."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_configuration(self) -> None:
        """Verifica configuración por defecto."""
        # Crear config sin cargar .env
        config = TaigaConfig(_env_file=None)

        assert config.api_url == "https://api.taiga.io/api/v1"
        assert config.username is None
        assert config.password is None
        assert config.auth_token is None
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.server_name == "taiga-mcp-server"
        assert config.transport == "stdio"
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.debug is False

    def test_configuration_from_env_vars(self) -> None:
        """Verifica carga de configuración desde variables de entorno."""
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://custom.taiga.io/api",
                "TAIGA_USERNAME": "test@example.com",
                "TAIGA_PASSWORD": "testpass",
                "TAIGA_AUTH_TOKEN": "test_token",
                "TAIGA_TIMEOUT": "60.0",
                "TAIGA_MAX_RETRIES": "5",
                "MCP_SERVER_NAME": "custom-server",
                "MCP_TRANSPORT": "http",
                "MCP_HOST": "0.0.0.0",
                "MCP_PORT": "9000",
                "MCP_DEBUG": "true",
            },
        ):
            config = TaigaConfig()

            assert config.api_url == "https://custom.taiga.io/api"
            assert config.username == "test@example.com"
            assert config.password == "testpass"
            assert config.auth_token == "test_token"
            assert config.timeout == 60.0
            assert config.max_retries == 5
            assert config.server_name == "custom-server"
            assert config.transport == "http"
            assert config.host == "0.0.0.0"
            assert config.port == 9000
            assert config.debug is True

    def test_validate_api_url_removes_trailing_slash(self) -> None:
        """Verifica que se elimine la barra final de la URL."""
        with patch.dict(os.environ, {"TAIGA_API_URL": "https://api.taiga.io/api/v1/"}):
            config = TaigaConfig()
            assert config.api_url == "https://api.taiga.io/api/v1"

    def test_validate_transport_valid_values(self) -> None:
        """Verifica valores válidos para transport."""
        # stdio
        with patch.dict(os.environ, {"MCP_TRANSPORT": "stdio"}):
            config = TaigaConfig()
            assert config.transport == "stdio"

        # http
        with patch.dict(os.environ, {"MCP_TRANSPORT": "http"}):
            config = TaigaConfig()
            assert config.transport == "http"

    def test_validate_transport_invalid_value(self) -> None:
        """Verifica rechazo de valores inválidos para transport."""
        with patch.dict(os.environ, {"MCP_TRANSPORT": "invalid"}):
            with pytest.raises(ValidationError) as exc:
                TaigaConfig()
            assert "Invalid transport" in str(exc.value)

    def test_validate_port_valid_range(self) -> None:
        """Verifica rango válido de puertos."""
        # Puerto mínimo
        with patch.dict(os.environ, {"MCP_PORT": "1"}):
            config = TaigaConfig()
            assert config.port == 1

        # Puerto máximo
        with patch.dict(os.environ, {"MCP_PORT": "65535"}):
            config = TaigaConfig()
            assert config.port == 65535

    def test_validate_port_invalid_range(self) -> None:
        """Verifica rechazo de puertos fuera de rango."""
        # Puerto 0
        with patch.dict(os.environ, {"MCP_PORT": "0"}):
            with pytest.raises(ValidationError) as exc:
                TaigaConfig()
            assert "Invalid port" in str(exc.value)

        # Puerto > 65535
        with patch.dict(os.environ, {"MCP_PORT": "70000"}):
            with pytest.raises(ValidationError) as exc:
                TaigaConfig()
            assert "Invalid port" in str(exc.value)

    def test_has_credentials_with_token(self) -> None:
        """Verifica detección de credenciales con token."""
        with patch.dict(os.environ, {"TAIGA_AUTH_TOKEN": "test_token"}):
            config = TaigaConfig(_env_file=None)
            assert config.has_credentials() is True

    def test_has_credentials_with_username_password(self) -> None:
        """Verifica detección de credenciales con usuario y contraseña."""
        with patch.dict(os.environ, {"TAIGA_USERNAME": "user", "TAIGA_PASSWORD": "pass"}):
            config = TaigaConfig(_env_file=None)
            assert config.has_credentials() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_has_credentials_without_credentials(self) -> None:
        """Verifica detección de ausencia de credenciales."""
        config = TaigaConfig(_env_file=None)
        assert config.has_credentials() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_has_credentials_only_username(self) -> None:
        """Verifica que solo username no es suficiente."""
        config = TaigaConfig(username="user", _env_file=None)
        assert config.has_credentials() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_has_credentials_only_password(self) -> None:
        """Verifica que solo password no es suficiente."""
        config = TaigaConfig(password="pass", _env_file=None)
        assert config.has_credentials() is False

    def test_validate_for_authentication_with_token(self) -> None:
        """Verifica validación exitosa con token."""
        with patch.dict(os.environ, {"TAIGA_AUTH_TOKEN": "test_token"}):
            config = TaigaConfig(_env_file=None)
            config.validate_for_authentication()  # No debe lanzar excepción

    def test_validate_for_authentication_with_credentials(self) -> None:
        """Verifica validación exitosa con usuario y contraseña."""
        with patch.dict(os.environ, {"TAIGA_USERNAME": "user", "TAIGA_PASSWORD": "pass"}):
            config = TaigaConfig(_env_file=None)
            config.validate_for_authentication()  # No debe lanzar excepción

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_for_authentication_without_credentials(self) -> None:
        """Verifica que falla sin credenciales."""
        config = TaigaConfig(_env_file=None)
        with pytest.raises(ConfigurationError) as exc:
            config.validate_for_authentication()
        assert "No authentication credentials provided" in str(exc.value)


class TestLoadConfig:
    """Tests para la función load_config."""

    @patch("src.infrastructure.config.load_dotenv")
    @patch("src.infrastructure.config.Path")
    def test_load_config_with_env_file(self, mock_path_cls, mock_load_dotenv) -> None:
        """Verifica carga con archivo .env específico."""
        # Setup
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        # Act
        config = load_config("custom.env")

        # Assert
        mock_path_cls.assert_called_once_with("custom.env")
        mock_load_dotenv.assert_called_once_with(mock_path)
        assert isinstance(config, TaigaConfig)

    @patch("src.infrastructure.config.load_dotenv")
    @patch("src.infrastructure.config.Path")
    def test_load_config_without_env_file(self, mock_path_cls, mock_load_dotenv) -> None:
        """Verifica búsqueda automática de .env."""
        # Setup
        mock_cwd = MagicMock()
        mock_env_path = MagicMock()
        mock_env_path.exists.return_value = True
        mock_cwd.__truediv__.return_value = mock_env_path
        mock_path_cls.cwd.return_value = mock_cwd
        mock_cwd.parents = []

        # Act
        config = load_config()

        # Assert
        mock_load_dotenv.assert_called_once_with(mock_env_path)
        assert isinstance(config, TaigaConfig)

    @patch("src.infrastructure.config.load_dotenv")
    @patch("src.infrastructure.config.Path")
    def test_load_config_no_env_found(self, mock_path_cls, mock_load_dotenv) -> None:
        """Verifica comportamiento cuando no se encuentra .env."""
        # Setup
        mock_cwd = MagicMock()
        mock_env_path = MagicMock()
        mock_env_path.exists.return_value = False
        mock_cwd.__truediv__.return_value = mock_env_path
        mock_path_cls.cwd.return_value = mock_cwd
        mock_cwd.parents = []

        # Act
        config = load_config()

        # Assert
        mock_load_dotenv.assert_not_called()
        assert isinstance(config, TaigaConfig)

    @patch("src.infrastructure.config.load_dotenv")
    @patch("src.infrastructure.config.Path")
    def test_load_config_finds_env_in_parent(self, mock_path_cls, mock_load_dotenv) -> None:
        """Verifica búsqueda de .env en directorio padre."""
        # Setup
        mock_cwd = MagicMock()
        mock_parent = MagicMock()

        # .env no existe en cwd
        mock_cwd_env = MagicMock()
        mock_cwd_env.exists.return_value = False
        mock_cwd.__truediv__.return_value = mock_cwd_env

        # .env existe en parent
        mock_parent_env = MagicMock()
        mock_parent_env.exists.return_value = True
        mock_parent.__truediv__.return_value = mock_parent_env

        mock_cwd.parents = [mock_parent]
        mock_path_cls.cwd.return_value = mock_cwd

        # Act
        config = load_config()

        # Assert
        mock_load_dotenv.assert_called_once_with(mock_parent_env)
        assert isinstance(config, TaigaConfig)


class TestGlobalConfig:
    """Tests para funciones de configuración global."""

    def test_get_config_creates_instance(self) -> None:
        """Verifica que get_config crea instancia si no existe."""
        # Reset global
        import src.infrastructure.config

        src.infrastructure.config._config = None

        config = get_config()
        assert isinstance(config, TaigaConfig)
        assert src.infrastructure.config._config is config

    @patch.dict(os.environ, {}, clear=True)
    def test_get_config_returns_existing(self) -> None:
        """Verifica que get_config retorna instancia existente."""
        # Setup
        import src.infrastructure.config

        with patch.dict(os.environ, {"MCP_SERVER_NAME": "existing"}):
            existing_config = TaigaConfig()
        src.infrastructure.config._config = existing_config

        # Act
        config = get_config()

        # Assert
        assert config is existing_config
        assert config.server_name == "existing"

    @patch.dict(os.environ, {}, clear=True)
    def test_set_config(self) -> None:
        """Verifica set_config actualiza la configuración global."""
        # Setup
        import src.infrastructure.config

        with patch.dict(os.environ, {"MCP_SERVER_NAME": "new-server"}):
            new_config = TaigaConfig()

        # Act
        set_config(new_config)

        # Assert
        assert src.infrastructure.config._config is new_config
        assert get_config().server_name == "new-server"

    def test_set_config_overrides_existing(self) -> None:
        """Verifica que set_config sobrescribe configuración existente."""
        # Setup
        import src.infrastructure.config

        old_config = TaigaConfig(server_name="old")
        src.infrastructure.config._config = old_config

        new_config = TaigaConfig(server_name="new")

        # Act
        set_config(new_config)

        # Assert
        assert src.infrastructure.config._config is new_config
        assert src.infrastructure.config._config is not old_config
