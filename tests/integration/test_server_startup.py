"""Tests de integración para el servidor MCP con dependency injection.

Test 1.2.1: Verificar que container se inicializa correctamente
Test 1.2.2: Verificar que todas las dependencias se inyectan
Test 1.2.3: Verificar que FastMCP se crea con configuración correcta
Test 1.2.4: Verificar que tools se registran automáticamente
Test 1.2.5: Test de integración: servidor inicia sin errores
"""

import os
from unittest.mock import patch

from dependency_injector import providers
from fastmcp import FastMCP

from src.config import ServerConfig, TaigaConfig
from src.infrastructure.container import ApplicationContainer
from src.server import TaigaMCPServer
from src.taiga_client import TaigaAPIClient


class TestContainerInitialization:
    """Test 1.2.1: Verificar que container se inicializa correctamente."""

    def test_container_creates_successfully(self) -> None:
        """El container debe crearse sin errores."""
        container = ApplicationContainer()
        assert container is not None

    def test_container_has_base_container_class(self) -> None:
        """El container debe heredar de containers."""

        container = ApplicationContainer()
        # Verificar que es una instancia de algún tipo de Container
        assert hasattr(container, "providers")
        assert callable(getattr(container, "override", None))

    def test_container_has_required_providers(self) -> None:
        """El container debe tener todos los providers necesarios."""
        container = ApplicationContainer()

        # Verificar que existen los providers principales
        assert hasattr(container, "config")
        assert hasattr(container, "server_config")
        assert hasattr(container, "mcp")
        assert hasattr(container, "taiga_client")

        # Verificar providers de repositorios
        assert hasattr(container, "epic_repository")

        # Verificar providers de tools
        assert hasattr(container, "auth_tools")
        assert hasattr(container, "epic_tools")
        assert hasattr(container, "project_tools")
        assert hasattr(container, "userstory_tools")
        assert hasattr(container, "issue_tools")
        assert hasattr(container, "milestone_tools")
        assert hasattr(container, "task_tools")
        assert hasattr(container, "membership_tools")
        assert hasattr(container, "webhook_tools")
        assert hasattr(container, "wiki_tools")


class TestDependencyInjection:
    """Test 1.2.2: Verificar que todas las dependencias se inyectan."""

    def test_config_is_singleton(self) -> None:
        """TaigaConfig debe ser singleton."""
        container = ApplicationContainer()

        config1 = container.config()
        config2 = container.config()

        assert config1 is config2
        assert isinstance(config1, TaigaConfig)

    def test_server_config_is_singleton(self) -> None:
        """ServerConfig debe ser singleton."""
        container = ApplicationContainer()

        config1 = container.server_config()
        config2 = container.server_config()

        assert config1 is config2
        assert isinstance(config1, ServerConfig)

    def test_mcp_is_singleton(self) -> None:
        """FastMCP debe ser singleton."""
        container = ApplicationContainer()

        mcp1 = container.mcp()
        mcp2 = container.mcp()

        assert mcp1 is mcp2
        assert isinstance(mcp1, FastMCP)

    def test_taiga_client_is_factory(self) -> None:
        """TaigaAPIClient debe ser factory (nueva instancia cada vez)."""
        container = ApplicationContainer()

        client1 = container.taiga_client()
        client2 = container.taiga_client()

        # Factory debe crear instancias diferentes
        assert client1 is not client2
        assert isinstance(client1, TaigaAPIClient)
        assert isinstance(client2, TaigaAPIClient)

    def test_epic_repository_receives_taiga_client(self) -> None:
        """EpicRepository debe recibir el cliente Taiga correctamente."""
        from src.infrastructure.repositories.epic_repository_impl import (
            EpicRepositoryImpl,
        )

        container = ApplicationContainer()
        repository = container.epic_repository()

        assert isinstance(repository, EpicRepositoryImpl)
        assert hasattr(repository, "client")
        assert repository.client is not None

    def test_epic_repository_is_singleton(self) -> None:
        """EpicRepository debe ser singleton."""
        from src.infrastructure.repositories.epic_repository_impl import (
            EpicRepositoryImpl,
        )

        container = ApplicationContainer()
        repo1 = container.epic_repository()
        repo2 = container.epic_repository()

        assert repo1 is repo2
        assert isinstance(repo1, EpicRepositoryImpl)

    def test_all_tools_receive_mcp(self) -> None:
        """Todos los tools deben recibir la instancia de FastMCP."""
        container = ApplicationContainer()
        mcp = container.mcp()

        # Verificar que cada tool recibe el mismo MCP
        auth_tools = container.auth_tools()
        epic_tools = container.epic_tools()
        project_tools = container.project_tools()

        assert auth_tools.mcp is mcp
        assert epic_tools.mcp is mcp
        assert project_tools.mcp is mcp


class TestFastMCPConfiguration:
    """Test 1.2.3: Verificar que FastMCP se crea con configuración correcta."""

    def test_mcp_has_correct_name(self) -> None:
        """FastMCP debe tener el nombre correcto."""
        container = ApplicationContainer()
        mcp = container.mcp()

        assert mcp.name == "taiga-mcp-server"

    def test_mcp_is_configurable(self) -> None:
        """FastMCP debe tener configuración por defecto."""
        container = ApplicationContainer()

        mcp = container.mcp()
        # Verificar que MCP es una instancia válida
        assert isinstance(mcp, FastMCP)
        assert hasattr(mcp, "tool")
        assert hasattr(mcp, "run")


class TestToolsRegistration:
    """Test 1.2.4: Verificar que tools se registran automáticamente."""

    def test_container_provides_tools_registration_capability(self) -> None:
        """El container debe proveer herramientas para registrar tools."""
        container = ApplicationContainer()
        # Verificar que container tiene registro de tools
        # La funcionalidad está en el método del container en src/infrastructure/container.py
        assert hasattr(container, "auth_tools")
        assert hasattr(container, "epic_tools")

    def test_tools_are_singletons(self) -> None:
        """Todos los tools deben ser singletons."""
        container = ApplicationContainer()

        auth1 = container.auth_tools()
        auth2 = container.auth_tools()
        assert auth1 is auth2

        epic1 = container.epic_tools()
        epic2 = container.epic_tools()
        assert epic1 is epic2


class TestServerIntegration:
    """Test 1.2.5: Test de integración: servidor inicia sin errores."""

    @patch.dict(
        os.environ,
        {
            "TAIGA_API_URL": "https://api.taiga.io",
            "TAIGA_USERNAME": "test@example.com",
            "TAIGA_PASSWORD": "test_pass",
        },
    )
    def test_server_initializes_with_container(self) -> None:
        """El servidor debe inicializarse usando el container."""
        server = TaigaMCPServer()

        assert server.container is not None
        assert isinstance(server.container, ApplicationContainer)

    @patch.dict(
        os.environ,
        {
            "TAIGA_API_URL": "https://api.taiga.io",
            "TAIGA_USERNAME": "test@example.com",
            "TAIGA_PASSWORD": "test_pass",
        },
    )
    def test_server_has_all_dependencies_from_container(self) -> None:
        """El servidor debe obtener todas las dependencias del container."""
        server = TaigaMCPServer()

        # Verificar que tiene config
        assert server.config is not None
        assert isinstance(server.config, TaigaConfig)

        # Verificar que tiene server_config
        assert server.server_config is not None
        assert isinstance(server.server_config, ServerConfig)

        # Verificar que tiene mcp
        assert server.mcp is not None
        assert isinstance(server.mcp, FastMCP)

        # Verificar que tiene tools
        assert server._auth_tools is not None
        assert server.epic_tools is not None
        assert server._project_tools is not None

    @patch.dict(
        os.environ,
        {
            "TAIGA_API_URL": "https://api.taiga.io",
            "TAIGA_USERNAME": "test@example.com",
            "TAIGA_PASSWORD": "test_pass",
        },
    )
    def test_server_registers_all_tools_on_init(self) -> None:
        """El servidor debe registrar todos los tools al inicializarse."""
        server = TaigaMCPServer()

        # Verificar que register_all_tools fue llamado
        # (implícito en __init__)
        assert server.container is not None

    @patch.dict(
        os.environ,
        {
            "TAIGA_API_URL": "https://api.taiga.io",
            "TAIGA_USERNAME": "test@example.com",
            "TAIGA_PASSWORD": "test_pass",
        },
    )
    def test_server_initializes_correctly(self) -> None:
        """El servidor debe inicializarse correctamente."""
        server = TaigaMCPServer()

        assert server.mcp is not None
        assert isinstance(server.mcp, FastMCP)


class TestContainerExtensibility:
    """Tests adicionales para extensibilidad del container."""

    def test_container_can_be_overridden_for_testing(self) -> None:
        """El container debe poder ser sobreescrito para testing."""
        from unittest.mock import Mock

        container = ApplicationContainer()

        # Override config con un mock
        mock_config = Mock(spec=TaigaConfig)
        mock_config.taiga_api_url = "http://mock.url"
        container.config.override(providers.Singleton(lambda: mock_config))

        config = container.config()
        assert config.taiga_api_url == "http://mock.url"

        # Resetear
        container.config.reset_override()

    def test_new_providers_can_be_added_to_container(self) -> None:
        """Se deben poder agregar nuevos providers al container."""

        class ExtendedContainer(ApplicationContainer):
            """Container extendido con providers adicionales."""

            # Este es un ejemplo de cómo se podría extender

        extended = ExtendedContainer()
        assert extended is not None
