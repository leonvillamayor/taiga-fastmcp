"""
Tests unitarios para la configuración del servidor MCP.
Verifica la carga de configuración desde .env según RF-036 a RF-041.
"""

import os
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from src.config import MCPConfig, ServerConfig, TaigaConfig


class TestEnvironmentConfiguration:
    """Tests para la configuración desde variables de entorno - RF-036 a RF-041."""

    @pytest.mark.unit
    def test_config_loads_from_env_file(self) -> None:
        """
        RF-036: El servidor DEBE leer credenciales desde archivo .env.
        Verifica que la configuración se carga desde .env.
        """
        # Arrange
        env_content = """
        TAIGA_API_URL=https://api.taiga.io/api/v1
        TAIGA_USERNAME=test@example.com
        TAIGA_PASSWORD=testpass123
        """

        with (
            patch("builtins.open", mock_open(read_data=env_content)),
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                    "TAIGA_USERNAME": "test@example.com",
                    "TAIGA_PASSWORD": "testpass123",
                },
            ),
        ):
            # Act
            config = TaigaConfig()

            # Assert
            assert config.taiga_api_url == "https://api.taiga.io/api/v1"
            assert config.taiga_username == "test@example.com"
            assert config.taiga_password == "testpass123"

    @pytest.mark.unit
    def test_config_uses_taiga_api_url(self) -> None:
        """
        RF-037: El servidor DEBE usar TAIGA_API_URL del .env.
        Verifica que se usa la URL correcta de la API.
        """
        # Arrange
        test_url = "https://custom.taiga.io/api/v2"

        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": test_url,
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act
            config = TaigaConfig()

            # Assert
            assert config.taiga_api_url == test_url
            assert config.get_api_endpoint("auth") == f"{test_url}/auth"
            assert config.get_api_endpoint("projects") == f"{test_url}/projects"

    @pytest.mark.unit
    def test_config_uses_taiga_username(self) -> None:
        """
        RF-038: El servidor DEBE usar TAIGA_USERNAME del .env.
        Verifica que se usa el username correcto.
        """
        # Arrange
        test_username = "javier@leonvillamayor.org"

        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": test_username,
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act
            config = TaigaConfig()

            # Assert
            assert config.taiga_username == test_username
            assert config.is_username_email() is True

    @pytest.mark.unit
    def test_config_uses_taiga_password(self) -> None:
        """
        RF-039: El servidor DEBE usar TAIGA_PASSWORD del .env.
        Verifica que se usa el password correcto.
        """
        # Arrange
        test_password = "#Actv2021"

        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": test_password,
            },
        ):
            # Act
            config = TaigaConfig()

            # Assert
            assert config.taiga_password == test_password
            # Password no debe ser expuesto en representaciones
            assert test_password not in str(config)
            assert test_password not in repr(config)

    @pytest.mark.unit
    def test_config_validates_required_credentials(self) -> None:
        """
        RF-040: El servidor DEBE validar que las credenciales existan.
        Verifica que se valida la presencia de credenciales requeridas.
        """
        # Arrange - Sin TAIGA_API_URL
        with patch.dict(
            os.environ,
            {
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
            clear=True,
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                TaigaConfig(_env_file=None)

            assert "TAIGA_API_URL" in str(exc_info.value)

        # Arrange - Sin TAIGA_USERNAME
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_PASSWORD": "password123",
            },
            clear=True,
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                TaigaConfig(_env_file=None)

            assert "TAIGA_USERNAME" in str(exc_info.value)

        # Arrange - Sin TAIGA_PASSWORD
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
            },
            clear=True,
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                TaigaConfig(_env_file=None)

            assert "TAIGA_PASSWORD" in str(exc_info.value)

    @pytest.mark.unit
    def test_config_handles_authentication_errors(self) -> None:
        """
        RF-041: El servidor DEBE manejar errores de autenticación.
        Verifica que la configuración prepara el manejo de errores de auth.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "invalid@user.com",
                "TAIGA_PASSWORD": "wrongpass",
            },
        ):
            # Act
            config = TaigaConfig()

            # Assert - La config debe tener métodos para manejar errores
            assert hasattr(config, "handle_auth_error")
            assert hasattr(config, "should_retry_auth")
            assert config.max_auth_retries == 3
            assert config.auth_timeout == 30

    @pytest.mark.unit
    def test_credentials_not_hardcoded(self) -> None:
        """
        RNF-007: Las credenciales NO DEBEN hardcodearse en el código.
        Verifica que no hay credenciales hardcodeadas.
        """
        # Arrange
        import inspect

        import src.config as config_module

        # Act - Inspeccionar el código fuente del módulo
        source_code = inspect.getsource(config_module)

        # Assert - No debe contener credenciales hardcodeadas
        assert "#Actv2021" not in source_code
        assert "javier@leonvillamayor.org" not in source_code
        # La URL de la API puede estar como default, es aceptable
        # pero credenciales de usuario no


class TestServerConfiguration:
    """Tests para la configuración del servidor MCP."""

    @pytest.mark.unit
    def test_mcp_server_name_configuration(self) -> None:
        """
        Verifica que el nombre del servidor MCP es configurable.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "MCP_SERVER_NAME": "Custom Taiga MCP",
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act
            config = ServerConfig()

            # Assert
            assert config.mcp_server_name == "Custom Taiga MCP"

    @pytest.mark.unit
    def test_mcp_transport_configuration(self) -> None:
        """
        Verifica que el transporte MCP es configurable.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "MCP_TRANSPORT": "http",
                "MCP_HOST": "192.168.1.100",
                "MCP_PORT": "3000",
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act
            config = ServerConfig()

            # Assert
            assert config.mcp_transport == "http"
            assert config.mcp_host == "192.168.1.100"
            assert config.mcp_port == 3000

    @pytest.mark.unit
    def test_default_configuration_values(self) -> None:
        """
        Verifica que se usan valores por defecto cuando no se especifican.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
            clear=True,
        ):
            # Act
            config = ServerConfig(_env_file=None)

            # Assert - Valores por defecto
            assert config.mcp_server_name == "Taiga MCP Server"
            assert config.mcp_transport == "stdio"
            assert config.mcp_host == "127.0.0.1"
            assert config.mcp_port == 8000


class TestConfigurationValidation:
    """Tests para validación de configuración."""

    @pytest.mark.unit
    def test_api_url_must_be_valid_url(self) -> None:
        """
        Verifica que TAIGA_API_URL debe ser una URL válida.
        """
        # Arrange - URL inválida
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "not-a-valid-url",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                TaigaConfig(_env_file=None)

            assert "URL" in str(exc_info.value)

    @pytest.mark.unit
    def test_username_must_not_be_empty(self) -> None:
        """
        Verifica que TAIGA_USERNAME no puede estar vacío.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                TaigaConfig(_env_file=None)

            assert "username" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_password_must_not_be_empty(self) -> None:
        """
        Verifica que TAIGA_PASSWORD no puede estar vacío.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "",
            },
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                TaigaConfig(_env_file=None)

            assert "password" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_port_must_be_valid_number(self) -> None:
        """
        Verifica que MCP_PORT debe ser un número válido.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "MCP_PORT": "not-a-number",
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                ServerConfig()

            assert "port" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_transport_must_be_valid_option(self) -> None:
        """
        Verifica que MCP_TRANSPORT debe ser stdio o http.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "MCP_TRANSPORT": "invalid-transport",
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                ServerConfig()

            assert "transport" in str(exc_info.value).lower()


class TestConfigurationUtilities:
    """Tests para utilidades de configuración."""

    @pytest.mark.unit
    def test_config_can_export_to_dict(self) -> None:
        """
        Verifica que la configuración puede exportarse como diccionario.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            # Act
            config = TaigaConfig()
            config_dict = config.to_dict()

            # Assert
            assert isinstance(config_dict, dict)
            assert config_dict["taiga_api_url"] == "https://api.taiga.io/api/v1"
            assert config_dict["taiga_username"] == "user@example.com"
            # Password no debe incluirse en export por seguridad
            assert "taiga_password" not in config_dict

    @pytest.mark.unit
    def test_config_can_reload_from_env(self) -> None:
        """
        Verifica que la configuración puede recargarse.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user1@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            config = TaigaConfig()
            original_username = config.taiga_username

            # Act - Cambiar env y recargar
            with patch.dict(
                os.environ,
                {
                    "TAIGA_USERNAME": "user2@example.com",
                },
            ):
                config.reload()

            # Assert
            assert config.taiga_username == "user2@example.com"
            assert config.taiga_username != original_username

    @pytest.mark.unit
    def test_config_validates_on_reload(self) -> None:
        """
        Verifica que la configuración se valida al recargar.
        """
        # Arrange
        with patch.dict(
            os.environ,
            {
                "TAIGA_API_URL": "https://api.taiga.io/api/v1",
                "TAIGA_USERNAME": "user@example.com",
                "TAIGA_PASSWORD": "password123",
            },
        ):
            config = TaigaConfig()

            # Act - Remover credencial requerida y recargar
            with (
                patch.dict(
                    os.environ,
                    {
                        "TAIGA_PASSWORD": "",
                    },
                ),
                pytest.raises(ValidationError),
            ):
                config.reload()


class TestMCPConfigValidations:
    """Tests para validaciones de MCPConfig."""

    @pytest.mark.unit
    def test_mcp_transport_validation_invalid(self) -> None:
        """
        Verifica que se valida el transport correctamente.
        Cubre líneas 58-60 de config.py.
        """
        # Arrange
        with (
            patch.dict(
                os.environ,
                {
                    "MCP_TRANSPORT": "websocket",  # Invalid transport
                },
            ),
            pytest.raises(ValidationError, match="Invalid transport"),
        ):
            # Act & Assert
            MCPConfig()

    @pytest.mark.unit
    def test_mcp_transport_validation_valid(self) -> None:
        """
        Verifica que se aceptan transports válidos.
        """
        # Test stdio
        with patch.dict(
            os.environ,
            {
                "MCP_TRANSPORT": "stdio",
            },
        ):
            config = MCPConfig()
            assert config.mcp_transport == "stdio"

        # Test http
        with patch.dict(
            os.environ,
            {
                "MCP_TRANSPORT": "http",
            },
        ):
            config = MCPConfig()
            assert config.mcp_transport == "http"

    @pytest.mark.unit
    def test_mcp_port_validation_too_low(self) -> None:
        """
        Verifica que se valida el puerto mínimo.
        Cubre líneas 66-68 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "MCP_PORT": "0",  # Invalid port (too low)
                },
            ),
            pytest.raises(ValidationError, match="Invalid port"),
        ):
            MCPConfig()

    @pytest.mark.unit
    def test_mcp_port_validation_too_high(self) -> None:
        """
        Verifica que se valida el puerto máximo.
        Cubre líneas 66-68 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "MCP_PORT": "70000",  # Invalid port (too high)
                },
            ),
            pytest.raises(ValidationError, match="Invalid port"),
        ):
            MCPConfig()

    @pytest.mark.unit
    def test_mcp_port_validation_valid(self) -> None:
        """
        Verifica que se aceptan puertos válidos.
        """
        with patch.dict(
            os.environ,
            {
                "MCP_PORT": "8080",
            },
        ):
            config = MCPConfig()
            assert config.mcp_port == 8080

    @pytest.mark.unit
    def test_mcp_to_dict_method(self, monkeypatch) -> None:
        """
        Verifica el método to_dict de MCPConfig.
        Cubre línea 72 de config.py.
        """
        # Remove MCP_TRANSPORT from environment to ensure default value
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)

        # Mock open to return empty env file
        with patch("builtins.open", mock_open(read_data="")):
            config = MCPConfig()
            result = config.to_dict()

            assert isinstance(result, dict)
            assert "mcp_server_name" in result
            assert "mcp_transport" in result
            assert result["mcp_transport"] == "stdio"  # default value


class TestTaigaConfigAdvancedValidations:
    """Tests avanzados para validaciones de TaigaConfig."""

    @pytest.mark.unit
    def test_taiga_api_url_missing_protocol(self) -> None:
        """
        Verifica validación de URL sin protocolo.
        Cubre líneas 138-139 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "api.taiga.io/api/v1",  # Missing protocol
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                },
            ),
            pytest.raises(ValidationError, match="must start with http"),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_api_url_too_short(self) -> None:
        """
        Verifica validación de URL muy corta.
        Cubre líneas 142-143 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "http://x",  # Too short
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                },
            ),
            pytest.raises(ValidationError, match="Invalid URL"),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_username_invalid_email(self) -> None:
        """
        Verifica validación de formato de email en username.
        Cubre líneas 153-154 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io",
                    "TAIGA_USERNAME": "not-an-email",  # Invalid email format
                    "TAIGA_PASSWORD": "password123",
                },
            ),
            pytest.raises(ValidationError, match="Invalid email"),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_password_too_short(self) -> None:
        """
        Verifica validación de password muy corta.
        Cubre líneas 161-162 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "123",  # Too short (< 6 chars)
                },
            ),
            pytest.raises(ValidationError, match="at least 6 characters"),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_timeout_negative(self) -> None:
        """
        Verifica validación de timeout negativo.
        Cubre líneas 173-174 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                    "TAIGA_TIMEOUT": "-5",  # Negative timeout
                },
            ),
            pytest.raises(ValidationError, match="must be positive"),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_max_retries_negative(self) -> None:
        """
        Verifica validación de max_retries negativo.
        Cubre líneas 181-182 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                    "TAIGA_MAX_RETRIES": "-1",  # Negative retries
                },
            ),
            pytest.raises(ValidationError, match="must be non-negative"),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_max_retries_too_high(self) -> None:
        """
        Verifica validación de max_retries muy alto.
        Cubre líneas 183-185 de config.py.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                    "TAIGA_MAX_RETRIES": "15",  # Too high (> 10)
                },
            ),
            pytest.raises(ValidationError, match="cannot exceed 10"),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_auth_timeout_negative(self) -> None:
        """
        Verifica validación de auth_timeout negativo.
        Cubre validación de auth_timeout.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                    "TAIGA_AUTH_TIMEOUT": "-10",  # Negative auth timeout
                },
            ),
            pytest.raises(ValidationError),
        ):
            TaigaConfig()

    @pytest.mark.unit
    def test_taiga_max_auth_retries_negative(self) -> None:
        """
        Verifica validación de max_auth_retries negativo.
        Cubre validación de max_auth_retries.
        """
        with (
            patch.dict(
                os.environ,
                {
                    "TAIGA_API_URL": "https://api.taiga.io",
                    "TAIGA_USERNAME": "user@example.com",
                    "TAIGA_PASSWORD": "password123",
                    "TAIGA_MAX_AUTH_RETRIES": "-2",  # Negative auth retries
                },
            ),
            pytest.raises(ValidationError),
        ):
            TaigaConfig()
