"""
Tests unitarios para el servidor MCP de Taiga.
Verifica la creación y configuración del servidor según RF-001, RF-002.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp import FastMCP

from src.server import TaigaMCPServer  # El servidor que implementaremos


class TestServerCreation:
    """Tests para la creación del servidor MCP - RF-001, RF-002."""

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_creation_with_fastmcp(self) -> None:
        """
        RF-001: El sistema DEBE utilizar el framework FastMCP para crear el servidor.
        Verifica que el servidor se crea correctamente usando FastMCP.
        """
        # Act - Intentar crear el servidor
        server = TaigaMCPServer(name="Test Taiga Server")

        # Assert
        assert server is not None
        assert isinstance(server.mcp, FastMCP)
        assert server.mcp.name == "Test Taiga Server"

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_implements_mcp_protocol(self) -> None:
        """
        RF-002: El servidor DEBE implementar el protocolo MCP.
        Verifica que el servidor implementa correctamente MCP.
        """
        # Arrange
        server = TaigaMCPServer(name="Test Server")

        # Act & Assert
        assert hasattr(server.mcp, "tool")
        assert hasattr(server.mcp, "run")
        assert hasattr(server.mcp, "add_tool")

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_configuration_from_env(self, test_config) -> None:
        """
        RF-036, RF-037, RF-038, RF-039: El servidor DEBE leer credenciales desde archivo .env.
        Verifica que el servidor carga la configuración correctamente.
        """
        # Act
        server = TaigaMCPServer()

        # Assert
        assert server.config.taiga_api_url == test_config.taiga_api_url
        assert server.config.taiga_username is not None
        assert server.config.taiga_password is not None

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_validates_required_credentials(self) -> None:
        """
        RF-040: El servidor DEBE validar que las credenciales existan.
        Verifica que el servidor valida la presencia de credenciales requeridas.
        """
        # Arrange - Make sure no env vars are loaded
        import os

        # Save and remove the TAIGA_API_URL
        original_api_url = os.environ.pop("TAIGA_API_URL", None)

        # Mock load_dotenv to not load anything - patch at module level
        with patch("src.server.load_dotenv") as mock_load_dotenv:
            mock_load_dotenv.return_value = None

            try:
                # Act & Assert
                with pytest.raises(ValueError, match="TAIGA_API_URL is required"):
                    TaigaMCPServer()
            finally:
                # Restore original value if it existed
                if original_api_url:
                    os.environ["TAIGA_API_URL"] = original_api_url

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_name_configuration(self) -> None:
        """
        Verifica que el servidor puede configurar su nombre correctamente.
        """
        # Act
        server = TaigaMCPServer(name="Custom Taiga MCP")

        # Assert
        assert server.mcp.name == "Custom Taiga MCP"


class TestServerTransports:
    """Tests para los transportes del servidor - RF-005, RF-006, RF-007, RF-008."""

    @pytest.mark.unit
    @pytest.mark.transport
    def test_server_supports_stdio_transport(self) -> None:
        """
        RF-005: El servidor DEBE soportar transporte STDIO.
        Verifica que el servidor puede configurarse para usar STDIO.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act
        transport_config = server.get_transport_config("stdio")

        # Assert
        assert transport_config is not None
        assert transport_config["transport"] == "stdio"
        assert server.can_run_stdio() is True

    @pytest.mark.unit
    @pytest.mark.transport
    def test_server_supports_http_transport(self) -> None:
        """
        RF-006: El servidor DEBE soportar transporte HTTP (Streamable).
        Verifica que el servidor puede configurarse para usar HTTP.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act
        transport_config = server.get_transport_config("http")

        # Assert
        assert transport_config is not None
        assert transport_config["transport"] == "http"
        assert transport_config["host"] == "127.0.0.1"
        assert transport_config["port"] == 8000
        assert transport_config["path"] == "/mcp"
        assert server.can_run_http() is True

    @pytest.mark.unit
    @pytest.mark.transport
    def test_server_can_run_both_transports(self) -> None:
        """
        RF-007: El servidor DEBE permitir ejecutar AMBOS transportes.
        Verifica que el servidor soporta ejecución dual.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act
        stdio_support = server.can_run_stdio()
        http_support = server.can_run_http()
        dual_support = server.can_run_dual_transport()

        # Assert
        assert stdio_support is True
        assert http_support is True
        assert dual_support is True

    @pytest.mark.unit
    @pytest.mark.transport
    def test_server_can_run_transports_separately(self) -> None:
        """
        RF-008: El servidor DEBE permitir ejecutar transportes POR SEPARADO.
        Verifica que el servidor puede ejecutar solo un transporte.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act & Assert - STDIO solo
        with patch.object(server.mcp, "run") as mock_run:
            server.run_stdio_only()
            mock_run.assert_called_once_with(transport="stdio")

        # Act & Assert - HTTP solo
        with patch.object(server.mcp, "run") as mock_run:
            server.run_http_only(host="0.0.0.0", port=9000)
            mock_run.assert_called_once_with(
                transport="http", host="0.0.0.0", port=9000, path="/mcp"
            )

    @pytest.mark.unit
    @pytest.mark.transport
    def test_transport_configuration_is_flexible(self) -> None:
        """
        RNF-004: Los transportes DEBEN ser configurables.
        Verifica que la configuración de transportes es flexible.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act - Configurar HTTP con parámetros personalizados
        custom_config = server.configure_http_transport(
            host="192.168.1.100", port=3000, path="/custom/mcp"
        )

        # Assert
        assert custom_config["host"] == "192.168.1.100"
        assert custom_config["port"] == 3000
        assert custom_config["path"] == "/custom/mcp"


class TestServerBestPractices:
    """Tests para verificar buenas prácticas de FastMCP - RNF-001, RNF-002, RNF-003."""

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_follows_fastmcp_best_practices(self) -> None:
        """
        RNF-001: El servidor DEBE seguir las buenas prácticas de FastMCP.
        Verifica que el servidor sigue las mejores prácticas.
        """
        # Arrange
        server = TaigaMCPServer()

        # Assert - Verificar estructura correcta
        assert hasattr(server, "mcp")
        assert hasattr(server, "taiga_client")
        assert hasattr(server, "config")

        # Verificar que usa decoradores correctos
        assert server.uses_decorators() is True

        # Verificar que implementa async/await
        assert server.uses_async_await() is True

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_code_is_pythonic_and_clean(self) -> None:
        """
        RNF-002: El código DEBE ser Pythónico y limpio.
        Verifica que el código sigue estándares Python.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act & Assert
        # Verificar nombres siguiendo PEP 8
        assert hasattr(server, "get_transport_config")  # snake_case para métodos
        assert not hasattr(server, "getTransportConfig")  # No camelCase

        # Verificar que las clases siguen PascalCase
        assert server.__class__.__name__ == "TaigaMCPServer"

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_uses_type_hints(self) -> None:
        """
        RNF-005: El código DEBE usar type hints completos.
        Verifica que el servidor usa type hints.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act - Obtener anotaciones de tipo
        import inspect

        methods = inspect.getmembers(server, predicate=inspect.ismethod)

        # Assert - Verificar que los métodos tienen type hints
        for name, method in methods:
            if not name.startswith("_"):  # Métodos públicos
                sig = inspect.signature(method)
                # Debe tener anotación de retorno
                assert sig.return_annotation != inspect.Signature.empty, (
                    f"Method {name} missing return type hint"
                )

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_has_docstrings(self) -> None:
        """
        RNF-006: El código DEBE tener docstrings descriptivos.
        Verifica que el servidor tiene documentación adecuada.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act & Assert
        assert server.__doc__ is not None
        assert len(server.__doc__) > 50  # Docstring sustancial

        # Verificar que los métodos tienen docstrings
        import inspect

        methods = inspect.getmembers(server, predicate=inspect.ismethod)

        for name, method in methods:
            if not name.startswith("_"):  # Métodos públicos
                assert method.__doc__ is not None, f"Method {name} missing docstring"


class TestServerInitialization:
    """Tests para la inicialización del servidor."""

    @pytest.mark.unit
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_server_initializes_taiga_client(self) -> None:
        """
        Verifica que el servidor inicializa correctamente el cliente de Taiga.
        """
        # Arrange
        with patch("src.server.TaigaClient") as mock_client:
            mock_client.return_value = AsyncMock()

            # Act
            server = TaigaMCPServer()
            await server.initialize()

            # Assert
            mock_client.assert_called_once()
            assert server.taiga_client is not None

    @pytest.mark.unit
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_server_authenticates_on_initialization(self) -> None:
        """
        RF-041: El servidor DEBE manejar errores de autenticación.
        Verifica que el servidor se autentica al inicializar.
        """
        # Arrange
        server = TaigaMCPServer()
        server.taiga_client = AsyncMock()
        server.taiga_client.authenticate = AsyncMock(return_value={"auth_token": "token123"})

        # Act
        await server.initialize()

        # Assert
        server.taiga_client.authenticate.assert_called_once_with(
            server.config.taiga_username, server.config.taiga_password
        )
        assert server.auth_token == "token123"

    @pytest.mark.unit
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_server_handles_authentication_errors(self) -> None:
        """
        RF-041: El servidor DEBE manejar errores de autenticación.
        Verifica que el servidor maneja errores de auth correctamente.
        """
        # Arrange
        server = TaigaMCPServer()
        server.taiga_client = AsyncMock()
        server.taiga_client.authenticate = AsyncMock(side_effect=Exception("Invalid credentials"))

        # Act & Assert
        with pytest.raises(Exception, match="Invalid credentials"):
            await server.initialize()

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_registers_all_tools(self) -> None:
        """
        RF-030: TODAS las funcionalidades de Taiga DEBEN estar expuestas.
        Verifica que el servidor registra todas las herramientas necesarias.
        """
        # Arrange
        server = TaigaMCPServer()

        # Act
        server.register_all_tools()
        tools = server.get_registered_tools()

        # Assert - Verificar que se registraron todas las categorías de herramientas
        tool_names = [tool.name for tool in tools]

        # Herramientas de autenticación (con prefijo taiga_)
        assert "taiga_authenticate" in tool_names
        assert "taiga_refresh_token" in tool_names
        assert "taiga_get_current_user" in tool_names

        # Herramientas de proyectos (con prefijo taiga_)
        assert "taiga_list_projects" in tool_names
        assert "taiga_create_project" in tool_names
        assert "taiga_get_project" in tool_names
        assert "taiga_update_project" in tool_names
        assert "taiga_delete_project" in tool_names

        # Herramientas de user stories (con prefijo taiga_)
        assert "taiga_list_userstories" in tool_names
        assert "taiga_create_userstory" in tool_names

        # We have auth (6), projects (13), and user stories (15) tools minimum
        assert len(tools) >= 25, "Debe haber al menos 25 herramientas registradas"


class TestServerShutdown:
    """Tests para el cierre del servidor."""

    @pytest.mark.unit
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_server_cleanup_on_shutdown(self) -> None:
        """
        Verifica que el servidor limpia recursos al cerrar.
        """
        # Arrange
        server = TaigaMCPServer()
        server.taiga_client = AsyncMock()
        server.taiga_client.close = AsyncMock()

        # Act
        await server.shutdown()

        # Assert
        server.taiga_client.close.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.mcp
    def test_server_handles_shutdown_errors_gracefully(self) -> None:
        """
        Verifica que el servidor maneja errores de shutdown sin fallar.
        """
        # Arrange
        server = TaigaMCPServer()
        server.taiga_client = Mock()
        server.taiga_client.close = Mock(side_effect=Exception("Close error"))

        # Act & Assert - No debe lanzar excepción
        try:
            server.shutdown_sync()
        except Exception:
            pytest.fail("Shutdown should handle errors gracefully")
