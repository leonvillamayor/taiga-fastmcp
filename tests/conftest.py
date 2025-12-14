"""
Configuración global de pytest y fixtures compartidas.
Define fixtures que se usan en múltiples tests del proyecto MCP Taiga.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from dotenv import load_dotenv
from faker import Faker
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Cargar variables de entorno para tests
load_dotenv()


# ============================================================================
# CONFIGURACIÓN
# ============================================================================


class TestConfig(BaseSettings):
    """Configuración para los tests."""

    # Credenciales de Taiga (del .env)
    taiga_api_url: str = Field(default="https://api.taiga.io/api/v1", alias="TAIGA_API_URL")
    taiga_username: str = Field(default="", alias="TAIGA_USERNAME")
    taiga_password: str = Field(default="", alias="TAIGA_PASSWORD")

    # Configuración del servidor MCP
    mcp_server_name: str = Field(default="Taiga MCP Server Test", alias="MCP_SERVER_NAME")
    mcp_transport: str = Field(default="stdio", alias="MCP_TRANSPORT")
    mcp_host: str = Field(default="127.0.0.1", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, alias="MCP_PORT")

    # Configuración de tests
    test_timeout: int = 30
    test_project_prefix: str = "TEST_"
    cleanup_after_tests: bool = True
    use_real_api: bool = False  # Para tests de integración

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# ============================================================================
# FIXTURES DE CONFIGURACIÓN
# ============================================================================


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Configuración global para tests."""
    return TestConfig()


@pytest.fixture
def project_root() -> Path:
    """Retorna el directorio raíz del proyecto."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def event_loop() -> None:
    """Crea un event loop para toda la sesión de tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()
        asyncio.set_event_loop(None)


# ============================================================================
# FIXTURES DE DATOS DE PRUEBA
# ============================================================================


@pytest.fixture
def faker_instance() -> Faker:
    """Instancia de Faker para generar datos aleatorios."""
    return Faker()


@pytest.fixture
def sample_project_data(faker_instance) -> dict[str, Any]:
    """Datos de ejemplo para un proyecto de Taiga."""
    return {
        "name": f"TEST_{faker_instance.company()}",
        "description": faker_instance.text(max_nb_chars=200),
        "is_private": False,
        "tags": [faker_instance.word() for _ in range(3)],
        "is_backlog_activated": True,
        "is_kanban_activated": True,
        "is_wiki_activated": True,
        "is_issues_activated": True,
    }


@pytest.fixture
def sample_user_story_data(faker_instance) -> dict[str, Any]:
    """Datos de ejemplo para una user story."""
    return {
        "subject": faker_instance.sentence(nb_words=6),
        "description": faker_instance.text(max_nb_chars=500),
        "tags": [faker_instance.word() for _ in range(2)],
        "points": {
            "1": faker_instance.random_int(1, 8),
            "2": faker_instance.random_int(1, 8),
            "3": faker_instance.random_int(1, 8),
        },
    }


@pytest.fixture
def sample_issue_data(faker_instance) -> dict[str, Any]:
    """Datos de ejemplo para un issue."""
    return {
        "subject": f"Bug: {faker_instance.sentence(nb_words=4)}",
        "description": faker_instance.text(max_nb_chars=300),
        "type": 1,  # Bug
        "priority": faker_instance.random_int(1, 5),
        "severity": faker_instance.random_int(1, 4),
        "tags": ["bug", faker_instance.word()],
    }


@pytest.fixture
def sample_epic_data(faker_instance) -> dict[str, Any]:
    """Datos de ejemplo para una epic."""
    return {
        "subject": f"Epic: {faker_instance.sentence(nb_words=5)}",
        "description": faker_instance.text(max_nb_chars=400),
        "color": "#A5694F",
        "tags": ["epic", faker_instance.word()],
    }


@pytest.fixture
def sample_task_data(faker_instance) -> dict[str, Any]:
    """Datos de ejemplo para una task."""
    return {
        "subject": faker_instance.sentence(nb_words=4),
        "description": faker_instance.text(max_nb_chars=200),
        "tags": [faker_instance.word()],
    }


@pytest.fixture
def sample_milestone_data(faker_instance) -> dict[str, Any]:
    """Datos de ejemplo para un milestone/sprint."""
    start_date = faker_instance.future_date(end_date="+7d")
    end_date = faker_instance.future_date(end_date="+21d")
    return {
        "name": f"Sprint {faker_instance.random_int(1, 20)}",
        "estimated_start": str(start_date),
        "estimated_finish": str(end_date),
    }


# ============================================================================
# FIXTURES DE AUTENTICACIÓN
# ============================================================================


@pytest.fixture
def mock_auth_token() -> str:
    """Token de autenticación mock para tests unitarios."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.mock_token_for_testing"


@pytest.fixture
def auth_token(mock_auth_token) -> str:
    """Alias para mock_auth_token para compatibilidad con tests de integración."""
    return mock_auth_token


@pytest.fixture
def mock_refresh_token() -> str:
    """Refresh token mock para tests unitarios."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.mock_refresh_token"


@pytest.fixture
async def auth_headers(mock_auth_token) -> dict[str, str]:
    """Headers de autenticación para tests."""
    return {
        "Authorization": f"Bearer {mock_auth_token}",
        "Content-Type": "application/json",
    }


# ============================================================================
# FIXTURES DE CLIENTE HTTP
# ============================================================================


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Cliente HTTP asíncrono para tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


# ============================================================================
# FIXTURES DE MOCKING (RESPX)
# ============================================================================


@pytest.fixture
def mock_taiga_api(respx_mock) -> respx.MockRouter:
    """Mock general de la API de Taiga."""
    base_url = "https://api.taiga.io/api/v1"

    # Mock de autenticación
    respx_mock.post(f"{base_url}/auth").mock(
        return_value=httpx.Response(
            200,
            json={
                "auth_token": "mock_token_123",
                "refresh": "refresh_token_456",
                "id": 12345,
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
            },
        )
    )

    # Mock de refresh token
    respx_mock.post(f"{base_url}/auth/refresh").mock(
        return_value=httpx.Response(
            200,
            json={
                "auth_token": "new_mock_token_789",
                "refresh": "new_refresh_token_012",
            },
        )
    )

    # Mock de current user
    respx_mock.get(f"{base_url}/users/me").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 12345,
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
            },
        )
    )

    return respx_mock


@pytest.fixture
def mock_taiga_projects(mock_taiga_api, sample_project_data) -> respx.MockRouter:
    """Mock de endpoints de proyectos."""
    base_url = "https://api.taiga.io/api/v1"

    # Lista de proyectos
    mock_taiga_api.get(f"{base_url}/projects").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "name": "Project 1", "slug": "project-1"},
                {"id": 2, "name": "Project 2", "slug": "project-2"},
            ],
        )
    )

    # Crear proyecto
    mock_taiga_api.post(f"{base_url}/projects").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 3,
                **sample_project_data,
                "slug": "test-project",
            },
        )
    )

    # Obtener proyecto por ID
    mock_taiga_api.get(url__regex=rf"{base_url}/projects/\d+").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "name": "Project 1",
                "slug": "project-1",
                **sample_project_data,
            },
        )
    )

    # Actualizar proyecto
    mock_taiga_api.patch(url__regex=rf"{base_url}/projects/\d+").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "name": "Updated Project",
                "slug": "project-1",
            },
        )
    )

    # Eliminar proyecto
    mock_taiga_api.delete(url__regex=rf"{base_url}/projects/\d+").mock(
        return_value=httpx.Response(204)
    )

    return mock_taiga_api


# ============================================================================
# FIXTURES DE SERVIDOR MCP
# ============================================================================


@pytest.fixture
def mcp_server_config(test_config) -> dict[str, Any]:
    """Configuración para el servidor MCP."""
    return {
        "name": test_config.mcp_server_name,
        "transport": test_config.mcp_transport,
        "host": test_config.mcp_host,
        "port": test_config.mcp_port,
    }


# ============================================================================
# FIXTURES DE REPOSITORIES MOCK
# ============================================================================


@pytest.fixture
def mock_mcp_server() -> None:
    """Mock del servidor MCP para tests funcionales."""
    from unittest.mock import Mock

    return Mock()


@pytest.fixture
def mock_taiga_client() -> None:
    """Mock del cliente Taiga para tests funcionales."""
    from unittest.mock import AsyncMock, Mock

    client = Mock()

    # Configurar el cliente como un context manager asíncrono
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    client.list_epics = AsyncMock()
    client.create_epic = AsyncMock()
    client.get_epic = AsyncMock()
    client.get_epic_by_ref = AsyncMock()
    client.update_epic = AsyncMock()
    client.update_epic_full = AsyncMock()
    client.delete_epic = AsyncMock()
    client.bulk_create_epics = AsyncMock()
    client.get_epic_filters = AsyncMock()
    client.upvote_epic = AsyncMock()
    client.downvote_epic = AsyncMock()
    client.watch_epic = AsyncMock()
    client.unwatch_epic = AsyncMock()
    client.list_epic_related_userstories = AsyncMock()
    client.create_epic_related_userstory = AsyncMock()
    client.get_epic_related_userstory = AsyncMock()
    client.update_epic_related_userstory = AsyncMock()
    client.delete_epic_related_userstory = AsyncMock()
    client.get_epic_voters = AsyncMock()
    client.get_epic_watchers = AsyncMock()
    client.list_epic_attachments = AsyncMock()
    client.create_epic_attachment = AsyncMock()
    client.get_epic_attachment = AsyncMock()
    client.update_epic_attachment = AsyncMock()
    client.delete_epic_attachment = AsyncMock()
    client.list_epic_custom_attributes = AsyncMock()
    client.create_epic_custom_attribute = AsyncMock()
    client.get_epic_custom_attribute_values = AsyncMock()
    client.bulk_create_epic_related_userstories = AsyncMock()
    client.bulk_create_related_userstories = AsyncMock()  # Alias without "epic"

    return client


@pytest.fixture
def mock_epic_repository() -> None:
    """Mock del repositorio de épicas para tests."""
    from unittest.mock import AsyncMock, Mock

    repository = Mock()
    repository.list = AsyncMock()
    repository.create = AsyncMock()
    repository.get = AsyncMock()
    repository.get_by_ref = AsyncMock()
    repository.update = AsyncMock()
    repository.update_partial = AsyncMock()  # Alias for update
    repository.update_full = AsyncMock()
    repository.delete = AsyncMock()
    repository.bulk_create = AsyncMock()
    repository.get_filters = AsyncMock()
    repository.upvote = AsyncMock()
    repository.downvote = AsyncMock()
    repository.watch = AsyncMock()
    repository.unwatch = AsyncMock()
    repository.project_exists = AsyncMock(return_value=True)
    repository.exists = AsyncMock(return_value=True)
    repository.has_voted = AsyncMock(return_value=False)
    repository.begin_transaction = AsyncMock()
    repository.commit = AsyncMock()
    repository.rollback = AsyncMock()

    return repository


@pytest.fixture
def mock_related_repository() -> None:
    """Mock del repositorio de user stories relacionadas para tests."""
    from unittest.mock import AsyncMock, Mock

    repository = Mock()
    repository.list_by_epic = AsyncMock()
    repository.delete_all_by_epic = AsyncMock()
    repository.delete_user_story = Mock()  # Not async, should not be called

    return repository


# ============================================================================
# FIXTURES DE LIMPIEZA
# ============================================================================


@pytest.fixture
def cleanup_manager() -> None:
    """Manager para registrar y ejecutar limpieza después de tests."""
    items_to_cleanup = []

    def register(item_type: str, item_id: Any, cleanup_func=None) -> None:
        """Registra un item para limpiar después del test."""
        items_to_cleanup.append({"type": item_type, "id": item_id, "cleanup_func": cleanup_func})

    yield register

    # Cleanup después del test
    for item in reversed(items_to_cleanup):
        if item["cleanup_func"]:
            try:
                item["cleanup_func"]()
            except Exception as e:
                print(f"Error cleaning up {item['type']} {item['id']}: {e}")


# ============================================================================
# MARKERS Y CONFIGURACIÓN DE PYTEST
# ============================================================================


def pytest_configure(config) -> None:
    """Configuración adicional de pytest."""
    # Registrar markers personalizados (ya definidos en pyproject.toml)


def pytest_collection_modifyitems(config, items) -> None:
    """Modificar items de tests durante la colección."""
    # Agregar markers automáticamente según la ubicación del test
    for item in items:
        # Agregar marker según directorio
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "functional" in str(item.fspath):
            item.add_marker(pytest.mark.functional)

        # Agregar marker asyncio si es función async
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ============================================================================
# HELPERS Y UTILIDADES
# ============================================================================


@pytest.fixture
def assert_mcp_response() -> None:
    """Helper para verificar respuestas MCP."""

    def _assert(response, expected_status=200, expected_content=None) -> None:
        assert hasattr(response, "status_code") or hasattr(response, "success")

        if hasattr(response, "status_code"):
            assert response.status_code == expected_status

        if expected_content is not None:
            content = response.json() if hasattr(response, "json") else response.content

            assert content == expected_content

    return _assert


@pytest.fixture
def wait_for_condition() -> None:
    """Helper para esperar una condición con timeout."""

    async def _wait(condition_func, timeout=10, interval=0.1) -> None:
        elapsed = 0
        while elapsed < timeout:
            if (
                await condition_func()
                if asyncio.iscoroutinefunction(condition_func)
                else condition_func()
            ):
                return True
            await asyncio.sleep(interval)
            elapsed += interval
        return False

    return _wait


# ============================================================================
# FIXTURES DE MOCKS PARA TAIGA Y MCP
# ============================================================================


@pytest.fixture
def taiga_client_mock() -> None:
    """Mock del cliente de Taiga para tests unitarios."""
    from unittest.mock import AsyncMock, Mock

    client = Mock()

    # Configurar el cliente como un context manager asíncrono
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    # Configurar método post para manejar creación de user stories
    async def mock_post(endpoint, **kwargs) -> None:
        if endpoint == "/userstories":
            return {"id": 1, "subject": "Test US for Milestone", "project": 1, "milestone": 1}
        return {}

    client.post = AsyncMock(side_effect=mock_post)
    client.get = AsyncMock(return_value={})
    client.patch = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=True)
    client.put = AsyncMock(return_value={})

    # Métodos de autenticación
    client.authenticate = AsyncMock(
        return_value={
            "auth_token": "test-auth-token",
            "refresh_token": "test-refresh-token",
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
        }
    )
    client.refresh_token = AsyncMock()
    client.get_current_user = AsyncMock()

    # Métodos de proyectos
    client.list_projects = AsyncMock()
    client.create_project = AsyncMock()
    client.get_project = AsyncMock()
    client.update_project = AsyncMock()
    client.delete_project = AsyncMock()

    # Métodos de user stories
    client.list_userstories = AsyncMock()
    mock_userstory = {"id": 1, "subject": "Test US", "project": 1}
    client.create_userstory = AsyncMock(return_value=mock_userstory)
    client.get_userstory = AsyncMock(return_value=mock_userstory)
    client.update_userstory = AsyncMock(return_value=mock_userstory)
    client.delete_userstory = AsyncMock()

    # Métodos de issues
    client.list_issues = AsyncMock()
    client.create_issue = AsyncMock()
    client.get_issue = AsyncMock()
    client.update_issue = AsyncMock()
    client.update_issue_full = AsyncMock()
    client.delete_issue = AsyncMock()
    client.bulk_create_issues = AsyncMock()
    client.get_issue_filters = AsyncMock()
    client.upvote_issue = AsyncMock()
    client.downvote_issue = AsyncMock()
    client.get_issue_voters = AsyncMock()
    client.watch_issue = AsyncMock()
    client.unwatch_issue = AsyncMock()
    client.get_issue_watchers = AsyncMock()
    client.create_issue_attachment = AsyncMock()
    client.get_issue_attachments = AsyncMock()
    client.update_issue_attachment = AsyncMock()
    client.delete_issue_attachment = AsyncMock()
    client.get_issue_history = AsyncMock()
    client.create_issue_comment = AsyncMock()
    client.edit_issue_comment = AsyncMock()
    client.delete_issue_comment = AsyncMock()
    client.get_issue_custom_attributes = AsyncMock()
    client.create_issue_custom_attribute = AsyncMock()
    client.update_issue_custom_attribute = AsyncMock()
    client.delete_issue_custom_attribute = AsyncMock()

    # Métodos de user story attachments y otros
    client.list_userstory_attachments = AsyncMock()
    client.create_userstory_attachment = AsyncMock()
    client.get_userstory_attachment = AsyncMock()
    client.update_userstory_attachment = AsyncMock()
    client.delete_userstory_attachment = AsyncMock()
    client.get_userstory_history = AsyncMock()
    client.get_userstory_comment_versions = AsyncMock()
    client.edit_userstory_comment = AsyncMock()
    client.delete_userstory_comment = AsyncMock()
    client.undelete_userstory_comment = AsyncMock()
    client.get_userstory_by_ref = AsyncMock()
    client.update_userstory_full = AsyncMock()
    client.bulk_update_backlog_order = AsyncMock()
    client.bulk_update_kanban_order = AsyncMock()
    client.bulk_update_sprint_order = AsyncMock()
    client.get_userstory_filters = AsyncMock()
    client.get_userstory_watchers = AsyncMock()
    client.list_userstory_custom_attributes = AsyncMock()
    client.get_userstory_custom_attributes = AsyncMock()
    client.create_userstory_custom_attribute = AsyncMock()
    client.get_userstory_custom_attribute = AsyncMock()
    client.update_userstory_custom_attribute = AsyncMock()
    client.update_userstory_custom_attribute_full = AsyncMock()
    client.update_userstory_custom_attribute_partial = AsyncMock()
    client.delete_userstory_custom_attribute = AsyncMock()
    client.bulk_create_attachments = AsyncMock()
    client.update_userstory = AsyncMock()

    # Métodos de epics
    client.list_epics = AsyncMock()
    client.create_epic = AsyncMock()
    client.get_epic = AsyncMock()
    client.get_epic_by_ref = AsyncMock()
    client.update_epic = AsyncMock()
    client.update_epic_full = AsyncMock()
    client.delete_epic = AsyncMock()
    client.list_epic_related_userstories = AsyncMock()
    client.create_epic_related_userstory = AsyncMock()
    client.get_epic_related_userstory = AsyncMock()
    client.update_epic_related_userstory = AsyncMock()
    client.delete_epic_related_userstory = AsyncMock()
    client.bulk_create_epics = AsyncMock()
    client.bulk_create_epic_related_userstories = AsyncMock()
    client.bulk_create_related_userstories = AsyncMock()  # Alias sin "epic"
    client.get_epic_filters = AsyncMock()
    client.upvote_epic = AsyncMock()
    client.downvote_epic = AsyncMock()
    client.get_epic_voters = AsyncMock()
    client.watch_epic = AsyncMock()
    client.unwatch_epic = AsyncMock()
    client.get_epic_watchers = AsyncMock()
    client.list_epic_attachments = AsyncMock()
    client.create_epic_attachment = AsyncMock()
    client.get_epic_attachment = AsyncMock()
    client.update_epic_attachment = AsyncMock()
    client.delete_epic_attachment = AsyncMock()
    client.list_epic_custom_attributes = AsyncMock()
    client.create_epic_custom_attribute = AsyncMock()
    client.get_epic_custom_attribute_values = AsyncMock()

    # Métodos de Issues
    client.list_issues = AsyncMock()
    client.create_issue = AsyncMock(
        return_value={
            "id": 123,
            "subject": "Test Issue from Integration Test",
            "description": "This is a test issue created by integration tests",
            "project": 1,
            "type": 1,
            "severity": 2,
            "priority": 2,
            "tags": ["test", "integration"],
        }
    )
    client.get_issue = AsyncMock(
        return_value={
            "id": 123,
            "subject": "Test Issue from Integration Test",
            "description": "This is a test issue created by integration tests",
            "project": 1,
            "type": 1,
            "severity": 2,
            "priority": 2,
            "status": 1,
            "version": 1,
            "tags": ["test", "integration"],
        }
    )
    client.get_issue_by_ref = AsyncMock()
    client.update_issue = AsyncMock(
        return_value={
            "id": 123,
            "subject": "Updated Issue",
            "description": "This is an updated test issue",
            "status": 2,
            "severity": 3,
            "version": 2,
        }
    )
    client.update_issue_full = AsyncMock()
    client.delete_issue = AsyncMock(return_value=None)
    client.bulk_create_issues = AsyncMock(
        return_value=[
            {"id": 124, "subject": "Bulk Issue 1", "type": 1, "severity": 2},
            {"id": 125, "subject": "Bulk Issue 2", "type": 1, "severity": 3},
            {"id": 126, "subject": "Bulk Issue 3", "type": 2, "severity": 1},
        ]
    )
    client.get_issue_filters = AsyncMock(
        return_value={
            "statuses": [{"id": 1, "name": "New"}, {"id": 2, "name": "In Progress"}],
            "types": [{"id": 1, "name": "Bug"}, {"id": 2, "name": "Feature"}],
            "severities": [
                {"id": 1, "name": "Wishlist"},
                {"id": 2, "name": "Normal"},
                {"id": 3, "name": "Important"},
            ],
            "priorities": [
                {"id": 1, "name": "Low"},
                {"id": 2, "name": "Normal"},
                {"id": 3, "name": "High"},
            ],
        }
    )
    client.upvote_issue = AsyncMock(return_value={"id": 123, "total_voters": 1})
    client.downvote_issue = AsyncMock(return_value={"id": 123, "total_voters": 0})
    client.get_issue_voters = AsyncMock(return_value=[{"id": 1, "username": "voter1"}])
    client.watch_issue = AsyncMock(return_value={"id": 123, "total_watchers": 1})
    client.unwatch_issue = AsyncMock(return_value={"id": 123, "total_watchers": 0})
    client.get_issue_watchers = AsyncMock(return_value=[{"id": 1, "username": "watcher1"}])
    client.get_issue_attachments = AsyncMock(return_value=[])
    # Mock de attachments con datos coherentes
    mock_attachment = {
        "id": 1,
        "name": "attachment.txt",
        "size": 1024,
        "description": "Test attachment",
    }
    client.list_issue_attachments = AsyncMock(
        return_value=[mock_attachment]
    )  # Alias for get_issue_attachments
    client.create_issue_attachment = AsyncMock(return_value=mock_attachment)
    client.get_issue_attachment = AsyncMock(return_value=mock_attachment)
    client.update_issue_attachment = AsyncMock(
        return_value={
            "id": 1,
            "name": "attachment.txt",
            "size": 1024,
            "description": "Updated test attachment",
        }
    )
    client.delete_issue_attachment = AsyncMock()
    client.get_issue_history = AsyncMock(
        return_value=[
            {
                "id": 1,
                "comment": "Issue is being worked on",
                "user": {"id": 1, "username": "test_user"},
            },
            {"id": 2, "comment": "Status changed", "diff": {"status": [1, 2]}},
        ]
    )
    client.get_issue_comment_versions = AsyncMock()
    client.edit_issue_comment = AsyncMock()
    client.delete_issue_comment = AsyncMock()
    client.undelete_issue_comment = AsyncMock()
    client.get_issue_custom_attributes = AsyncMock(
        return_value=[{"id": 1, "name": "Custom Field 1", "value": "Value 1"}]
    )
    client.get_issue_custom_attribute_values = AsyncMock(return_value={"1": "Custom Value 1"})
    client.update_issue_custom_attribute_values = AsyncMock(
        return_value={"1": "Updated Custom Value 1"}
    )
    # Mock de custom attributes con datos coherentes
    mock_custom_attr = {
        "id": 99,
        "name": "Test Environment",
        "description": "Environment where issue was found",
        "type": "text",
        "order": 99,
    }
    client.list_issue_custom_attributes = AsyncMock(
        return_value=[
            {"id": 1, "name": "Custom Field 1", "value": "Value 1"},
            mock_custom_attr,  # Incluimos el atributo creado
        ]
    )  # Alias for get_issue_custom_attributes
    client.create_issue_custom_attribute = AsyncMock(return_value=mock_custom_attr)
    client.update_issue_custom_attribute = AsyncMock(
        return_value={
            "id": 99,
            "name": "Testing Environment",
            "description": "Updated description",
            "type": "text",
            "order": 99,
        }
    )
    client.delete_issue_custom_attribute = AsyncMock()

    # Métodos de tasks - simple return values for unit tests
    # Integration tests will override these with stateful mocks
    client.list_tasks = AsyncMock(return_value=[])
    client.create_task = AsyncMock(
        return_value={
            "id": 1,
            "ref": 1,
            "subject": "Test Task",
            "project": 1,
            "user_story": 1,
            "version": 1,
            "status": 1,
        }
    )
    client.get_task = AsyncMock(
        return_value={
            "id": 1,
            "ref": 1,
            "subject": "Implementar validación de email",
            "project": 309804,
            "user_story": 1,
            "version": 1,
            "status": 1,
        }
    )
    client.get_task_by_ref = AsyncMock(
        return_value={
            "id": 1,
            "ref": 1,
            "subject": "Task to get by ref",
            "project": 309804,
            "user_story": 1,
            "version": 1,
            "status": 1,
        }
    )
    client.update_task = AsyncMock(return_value={"id": 1, "status": 2, "version": 2})

    client.update_task_full = AsyncMock(return_value={"id": 1, "status": 2, "version": 2})
    client.patch_task = AsyncMock(
        return_value={
            "id": 1,
            "subject": "Test Task",
            "project": 1,
            "user_story": 1,
            "version": 1,
            "status": 1,
        }
    )
    client.delete_task = AsyncMock()
    client.bulk_create_tasks = AsyncMock(
        return_value=[
            {"id": 1, "ref": 1, "subject": "Bulk Task 1", "project": 1, "version": 1, "status": 1},
            {"id": 2, "ref": 2, "subject": "Bulk Task 2", "project": 1, "version": 1, "status": 1},
            {"id": 3, "ref": 3, "subject": "Bulk Task 3", "project": 1, "version": 1, "status": 1},
        ]
    )
    client.get_task_filters_data = AsyncMock()
    client.get_task_filters = AsyncMock(
        return_value={
            "statuses": [
                {"id": 1, "name": "New"},
                {"id": 2, "name": "In Progress"},
                {"id": 3, "name": "Ready for test"},
            ],
            "assigned_users": [{"id": 1, "username": "test_user"}],
            "tags": ["backend", "frontend"],
        }
    )
    client.upvote_task = AsyncMock(return_value={"id": 1, "total_voters": 1})
    client.downvote_task = AsyncMock(return_value={"id": 1, "total_voters": 0})
    client.get_task_voters = AsyncMock(return_value=[{"id": 1, "username": "test_user"}])
    client.watch_task = AsyncMock(return_value={"id": 1, "total_watchers": 1})
    client.unwatch_task = AsyncMock(return_value={"id": 1, "total_watchers": 0})
    client.get_task_watchers = AsyncMock(return_value=[{"id": 1, "username": "test_user"}])

    # Task attachments - simple mocks for unit tests
    client.list_task_attachments = AsyncMock(
        return_value=[
            {"id": 1, "object_id": 1, "attached_file": "file.txt", "description": "Test attachment"}
        ]
    )
    client.create_task_attachment = AsyncMock(
        return_value={
            "id": 2002,
            "object_id": 1,
            "attached_file": "file.txt",
            "description": "Test attachment",
        }
    )
    client.get_task_attachment = AsyncMock(
        return_value={"id": 1, "object_id": 1, "attached_file": "file.txt"}
    )
    client.update_task_attachment = AsyncMock(
        return_value={"id": 1, "description": "Updated attachment"}
    )
    client.delete_task_attachment = AsyncMock()
    client.get_task_history = AsyncMock(
        return_value=[
            {
                "id": 1,
                "user": {"username": "test_user"},
                "created_at": "2025-12-05T00:00:00Z",
                "values_diff": {"status": [1, 2]},
            }
        ]
    )
    client.get_task_comment_versions = AsyncMock(return_value=[])
    client.edit_task_comment = AsyncMock(return_value={"id": "1", "comment": "Updated comment"})
    client.delete_task_comment = AsyncMock()
    client.undelete_task_comment = AsyncMock(return_value={"id": "1"})

    # Task custom attributes - simple mocks for unit tests
    client.list_task_custom_attributes = AsyncMock(
        return_value=[
            {"id": 1, "project": 309804, "name": "Estimated Hours", "description": "Test attribute"}
        ]
    )
    client.create_task_custom_attribute = AsyncMock(
        return_value={
            "id": 1,
            "project": 309804,
            "name": "Estimated Hours",
            "description": "Estimated hours for completion",
            "type": "number",
            "order": 99,
        }
    )
    client.update_task_custom_attribute = AsyncMock(
        return_value={"id": 1, "name": "Updated Name", "description": "Updated description"}
    )
    client.delete_task_custom_attribute = AsyncMock()

    # Métodos de milestones/sprints
    mock_milestone = {
        "id": 1,
        "name": f"Test Sprint {date.today().isoformat()}",
        "estimated_start": (date.today() + timedelta(days=1)).isoformat(),
        "estimated_finish": (date.today() + timedelta(days=15)).isoformat(),
        "closed": False,
    }

    # Store milestones for filtering
    mock_milestones_db = [dict(mock_milestone)]

    async def mock_list_milestones(**kwargs) -> None:
        """Mock list milestones with filtering support."""
        result = list(mock_milestones_db)  # copy the list
        if "closed" in kwargs and kwargs["closed"] is not None:
            result = [m for m in result if m.get("closed", False) == kwargs["closed"]]
        return result

    async def mock_update_milestone(milestone_id, data) -> None:
        """Mock update milestone with state persistence."""
        for m in mock_milestones_db:
            if m.get("id") == milestone_id:
                m.update(data)
                return dict(m)  # return a copy
        return mock_milestone

    async def mock_get_milestone(milestone_id) -> None:
        """Mock get milestone with user stories support."""
        for m in mock_milestones_db:
            if m.get("id") == milestone_id:
                result = dict(m)
                # Add user_stories field if not present
                if "user_stories" not in result:
                    result["user_stories"] = []
                return result
        # Default milestone with user_stories
        return {**mock_milestone, "user_stories": []}

    # Use regular AsyncMock without side_effect by default
    # This allows tests to override with return_value or side_effect as needed
    client.list_milestones = AsyncMock()
    client.create_milestone = AsyncMock()
    client.get_milestone = AsyncMock()
    client.update_milestone = AsyncMock()
    client.update_milestone_full = AsyncMock(return_value=mock_milestone)
    client.delete_milestone = AsyncMock()
    client.get_milestone_stats = AsyncMock(
        return_value={
            "total_tasks": 10,
            "completed_tasks": 5,
            "total_points": 50.0,
            "completed_points": 25.0,
            "total_userstories": 3,
            "completed_userstories": 0,
            "days": [
                {
                    "day": "2025-12-06",
                    "name": "Day 1",
                    "open_points": 50.0,
                    "optimal_points": 50.0,
                    "completed_points": 0.0,
                },
                {
                    "day": "2025-12-07",
                    "name": "Day 2",
                    "open_points": 40.0,
                    "optimal_points": 45.0,
                    "completed_points": 10.0,
                },
            ],
        }
    )
    client.watch_milestone = AsyncMock(return_value={"id": 1, "total_watchers": 1})
    client.unwatch_milestone = AsyncMock(return_value={"id": 1, "total_watchers": 0})
    client.get_milestone_watchers = AsyncMock(return_value=[{"id": 1, "username": "test_user"}])

    # Métodos de wiki
    client.list_wiki_pages = AsyncMock()
    client.create_wiki_page = AsyncMock()
    client.get_wiki_page = AsyncMock()
    client.get_wiki_page_by_slug = AsyncMock()
    client.update_wiki_page = AsyncMock()
    client.delete_wiki_page = AsyncMock()
    client.get_wiki_page_history = AsyncMock()
    client.watch_wiki_page = AsyncMock()
    client.unwatch_wiki_page = AsyncMock()
    client.get_wiki_page_watchers = AsyncMock()
    client.create_wiki_link = AsyncMock()

    # Métodos de users
    client.list_users = AsyncMock()

    # Métodos de memberships
    client.list_memberships = AsyncMock()
    client.create_membership = AsyncMock()
    client.get_membership = AsyncMock()
    client.update_membership = AsyncMock()
    client.delete_membership = AsyncMock()

    # Métodos de webhooks
    client.list_webhooks = AsyncMock()
    client.create_webhook = AsyncMock()
    client.get_webhook = AsyncMock()
    client.update_webhook = AsyncMock()
    client.delete_webhook = AsyncMock()
    client.test_webhook = AsyncMock()
    client.list_webhook_logs = AsyncMock()
    client.resend_webhook_request = AsyncMock()

    return client


@pytest.fixture(scope="function")
def userstory_tools_fixture(taiga_client_mock) -> None:
    """
    Fixture específica para UserStoryTools con cliente mock.
    NOTA: Renombrado a userstory_tools_fixture para evitar conflictos.
    Los tests que necesiten este fixture deben solicitarlo explícitamente.
    """
    from unittest.mock import MagicMock, patch

    from fastmcp import FastMCP

    from src.application.tools.userstory_tools import UserStoryTools

    mcp = FastMCP("Test")
    tools = UserStoryTools(mcp)

    # Configurar el mock para retornar valores correctos
    mock_client = MagicMock()

    # Configurar métodos del mock con funcionalidad dinámica
    def mock_list_user_stories(**kwargs) -> None:
        # Filtrar por diferentes criterios
        if kwargs.get("milestone_id"):
            return [
                {"id": 100, "subject": "Story 1", "project": 1, "milestone": kwargs["milestone_id"]}
            ]
        if kwargs.get("status"):
            return [{"id": 100, "subject": "Story 1", "project": 1, "status": kwargs["status"]}]
        # Por defecto retorna 2
        return [
            {"id": 100, "subject": "Story 1", "project": 1},
            {"id": 101, "subject": "Story 2", "project": 1},
        ]

    mock_client.list_user_stories.side_effect = mock_list_user_stories

    mock_client.create_user_story.return_value = {"id": 100, "subject": "New Story", "project": 1}

    mock_client.get_user_story.return_value = {"id": 100, "ref": 25, "subject": "Test Story"}

    mock_client.get_userstory_by_ref.return_value = {
        "id": 100,
        "ref": 25,
        "subject": "Test Story by Ref",
    }

    mock_client.update_user_story.return_value = {
        "id": 100,
        "status": "completed",
        "subject": "Updated Story",
    }

    mock_client.delete_user_story.side_effect = lambda id: None

    # Métodos bulk
    mock_client.bulk_create_user_stories.return_value = [
        {"id": 100, "subject": "Bulk Story 1"},
        {"id": 101, "subject": "Bulk Story 2"},
        {"id": 102, "subject": "Bulk Story 3"},
    ]

    mock_client.bulk_update_user_stories.return_value = [
        {"id": 100, "status": "done"},
        {"id": 101, "status": "done"},
    ]

    # Otros métodos
    mock_client.move_to_milestone.return_value = {"id": 100, "milestone": 20}
    mock_client.get_user_story_history.return_value = [
        {"id": 1, "type": "change"},
        {"id": 2, "type": "comment"},
    ]

    # Crear un patcher para limpiar al final
    patcher = patch(
        "src.application.tools.userstory_tools.get_taiga_client", return_value=mock_client
    )
    patcher.start()

    tools.set_client(mock_client)
    tools.register_tools()

    yield tools

    # Limpieza: detener el patch
    patcher.stop()


@pytest.fixture
def mcp_server(taiga_client_mock) -> None:
    """Mock del servidor MCP con todas las herramientas."""
    from unittest.mock import Mock

    from fastmcp import FastMCP

    from src.application.tools.auth_tools import AuthTools
    from src.application.tools.issue_tools import IssueTools
    from src.application.tools.membership_tools import MembershipTools
    from src.application.tools.milestone_tools import MilestoneTools
    from src.application.tools.project_tools import ProjectTools
    from src.application.tools.task_tools import TaskTools
    from src.application.tools.user_tools import UserTools
    from src.application.tools.userstory_tools import UserStoryTools
    from src.application.tools.webhook_tools import WebhookTools
    from src.application.tools.wiki_tools import WikiTools

    server = Mock()

    # Crear instancia de FastMCP para las herramientas
    mcp = FastMCP("Test")

    # Patch TaigaAPIClient en los tools para usar el mock
    import unittest.mock as mock
    from unittest.mock import AsyncMock

    # Crear y configurar issue_tools (usa patching de TaigaAPIClient)
    mock_issue_patch = mock.patch("src.application.tools.issue_tools.TaigaAPIClient")
    mock_issue_cls = mock_issue_patch.start()
    mock_issue_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_issue_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    issue_tools = IssueTools(mcp)
    issue_tools.register_tools()
    server.issue_tools = issue_tools

    # Crear y configurar task_tools (usa patching de TaigaAPIClient)
    mock_task_patch = mock.patch("src.application.tools.task_tools.TaigaAPIClient")
    mock_task_cls = mock_task_patch.start()
    mock_task_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_task_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    task_tools = TaskTools(mcp)
    server.task_tools = task_tools

    # Crear y configurar milestone_tools (usa patching de TaigaAPIClient)
    mock_milestone_patch = mock.patch("src.application.tools.milestone_tools.TaigaAPIClient")
    mock_milestone_cls = mock_milestone_patch.start()
    mock_milestone_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_milestone_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    milestone_tools = MilestoneTools(mcp)
    server.milestone_tools = milestone_tools

    # Crear y configurar epic_tools (usa patching de TaigaAPIClient)
    from src.application.tools.epic_tools import EpicTools

    mock_epic_patch = mock.patch("src.application.tools.epic_tools.TaigaAPIClient")
    mock_epic_cls = mock_epic_patch.start()
    mock_epic_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_epic_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    epic_tools = EpicTools(mcp)
    server.epic_tools = epic_tools

    # Crear y configurar wiki_tools
    mock_wiki_patch = mock.patch("src.application.tools.wiki_tools.TaigaAPIClient")
    mock_wiki_cls = mock_wiki_patch.start()
    mock_wiki_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_wiki_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    wiki_tools = WikiTools(mcp)
    wiki_tools.register_tools()  # Register tools to make methods available
    server.wiki_tools = wiki_tools

    # Crear y configurar user_tools (usa patching de TaigaAPIClient)
    mock_user_patch = mock.patch("src.application.tools.user_tools.TaigaAPIClient")
    mock_user_cls = mock_user_patch.start()
    mock_user_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_user_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    user_tools = UserTools(mcp)
    server.user_tools = user_tools

    # Crear y configurar membership_tools
    mock_membership_patch = mock.patch("src.application.tools.membership_tools.TaigaAPIClient")
    mock_membership_cls = mock_membership_patch.start()
    mock_membership_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_membership_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    membership_tools = MembershipTools(mcp)
    membership_tools.register_tools()  # Register tools to make methods available
    server.membership_tools = membership_tools

    # Crear y configurar webhook_tools
    mock_webhook_patch = mock.patch("src.application.tools.webhook_tools.TaigaAPIClient")
    mock_webhook_cls = mock_webhook_patch.start()
    mock_webhook_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_webhook_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    webhook_tools = WebhookTools(mcp)
    webhook_tools.register_tools()  # Register tools to make methods available
    server.webhook_tools = webhook_tools

    # Crear y configurar userstory_tools
    mock_userstory_patch = mock.patch("src.application.tools.userstory_tools.TaigaAPIClient")
    mock_userstory_cls = mock_userstory_patch.start()
    mock_userstory_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_userstory_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    userstory_tools = UserStoryTools(mcp)
    userstory_tools.set_client(taiga_client_mock)  # Configure the client for tests
    userstory_tools.register_tools()  # Register tools to make methods available
    server.userstory_tools = userstory_tools

    # Crear otros objetos de herramientas con el cliente mock
    mock_auth_patch = mock.patch("src.application.tools.auth_tools.TaigaAPIClient")
    mock_auth_cls = mock_auth_patch.start()
    mock_auth_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_auth_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    auth_tools = AuthTools(mcp)
    auth_tools.register_tools()  # Register tools to make methods available
    server.auth_tools = auth_tools

    mock_project_patch = mock.patch("src.application.tools.project_tools.TaigaAPIClient")
    mock_project_cls = mock_project_patch.start()
    mock_project_cls.return_value.__aenter__ = AsyncMock(return_value=taiga_client_mock)
    mock_project_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    project_tools = ProjectTools(mcp)
    project_tools.register_tools()  # Register tools to make methods available
    server.project_tools = project_tools

    yield server

    # Limpieza: detener TODOS los patches de módulos que importan TaigaAPIClient
    mock_issue_patch.stop()
    mock_task_patch.stop()
    mock_milestone_patch.stop()
    mock_epic_patch.stop()
    mock_wiki_patch.stop()
    mock_user_patch.stop()
    mock_membership_patch.stop()
    mock_webhook_patch.stop()
    mock_userstory_patch.stop()
    mock_auth_patch.stop()
    mock_project_patch.stop()


# ============================================================================
# FIXTURES ESPECÍFICAS PARA ÉPICAS (AGREGADAS PARA TDD)
# ============================================================================


@pytest.fixture
def valid_epic_data() -> dict[str, Any]:
    """Datos válidos para crear una épica."""
    return {
        "project": 309804,
        "subject": "Módulo de Autenticación",
        "description": "Epic para toda la funcionalidad de autenticación del sistema",
        "color": "#A5694F",
        "assigned_to": 888691,
        "status": 1,
        "tags": ["auth", "security", "v2"],
        "client_requirement": True,
        "team_requirement": False,
    }


@pytest.fixture
def epic_response_data() -> dict[str, Any]:
    """Respuesta simulada de la API al crear/obtener una épica."""
    return {
        "id": 456789,
        "ref": 5,
        "version": 1,
        "subject": "Módulo de Autenticación",
        "description": "Epic para toda la funcionalidad de autenticación del sistema",
        "status": 1,
        "color": "#A5694F",
        "project": 309804,
        "assigned_to": 888691,
        "owner": 888691,
        "tags": ["auth", "security", "v2"],
        "client_requirement": True,
        "team_requirement": False,
        "created_date": "2025-01-10T08:00:00Z",
        "modified_date": "2025-01-15T12:00:00Z",
        "watchers": [888691],
        "total_voters": 0,
    }


@pytest.fixture
def multiple_epics_data() -> list[dict[str, Any]]:
    """Lista de múltiples épicas para tests de bulk."""
    return [
        {
            "subject": "Sistema de Notificaciones",
            "color": "#B83A3A",
            "tags": ["notifications", "backend"],
        },
        {"subject": "Dashboard Analytics", "color": "#3AB83A", "tags": ["frontend", "analytics"]},
        {"subject": "API REST v2", "color": "#3A3AB8", "tags": ["api", "backend", "v2"]},
    ]


@pytest.fixture
def related_userstory_data() -> dict[str, Any]:
    """Datos de una user story relacionada con épica."""
    return {
        "id": 123,
        "user_story": {
            "id": 123456,
            "ref": 1,
            "subject": "Login de usuarios",
            "status": 2,
            "project": 309804,
        },
        "epic": 456789,
        "order": 1,
    }


@pytest.fixture
def bulk_userstories_ids() -> list[int]:
    """IDs de user stories para relacionar en bulk."""
    return [123456, 123457, 123458, 123459]


@pytest.fixture
def epic_attachment_data() -> dict[str, Any]:
    """Datos de un adjunto de épica."""
    return {
        "id": 789012,
        "name": "requirements.pdf",
        "size": 1048576,  # 1MB
        "url": "https://taiga.io/attachments/789012/requirements.pdf",
        "description": "Documento de requerimientos detallados",
        "is_deprecated": False,
        "created_date": "2025-01-10T09:00:00Z",
        "object_id": 456789,
        "project": 309804,
        "content_type": "application/pdf",
    }


@pytest.fixture
def epic_filters_data() -> dict[str, Any]:
    """Datos de filtros disponibles para épicas."""
    return {
        "statuses": [
            {"id": 1, "name": "New", "color": "#999999"},
            {"id": 2, "name": "Ready", "color": "#F57900"},
            {"id": 3, "name": "In Progress", "color": "#729FCF"},
            {"id": 4, "name": "Ready for Test", "color": "#4E9A06"},
            {"id": 5, "name": "Done", "color": "#5C3566"},
        ],
        "assigned_to": [
            {"id": 888691, "username": "john.doe", "full_name": "John Doe"},
            {"id": 888692, "username": "jane.smith", "full_name": "Jane Smith"},
        ],
        "tags": ["auth", "security", "frontend", "backend", "api", "v2"],
    }


@pytest.fixture
def epic_voters_data() -> list[dict[str, Any]]:
    """Lista de usuarios que han votado una épica."""
    return [
        {"id": 888691, "username": "john.doe", "full_name": "John Doe"},
        {"id": 888692, "username": "jane.smith", "full_name": "Jane Smith"},
        {"id": 888693, "username": "bob.wilson", "full_name": "Bob Wilson"},
    ]


@pytest.fixture
def epic_watchers_data() -> list[dict[str, Any]]:
    """Lista de usuarios observando una épica."""
    return [
        {"id": 888691, "username": "john.doe", "full_name": "John Doe"},
        {"id": 888694, "username": "alice.brown", "full_name": "Alice Brown"},
    ]


@pytest.fixture
def invalid_epic_colors() -> list[str]:
    """Lista de colores inválidos para testing."""
    return [
        "red",  # No es hex
        "#FF",  # Muy corto
        "#GGGGGG",  # Caracteres inválidos
        "FF0000",  # Sin #
        "#FF00000",  # Muy largo
        "",  # Vacío
    ]


@pytest.fixture
def invalid_epic_subjects() -> list[str]:
    """Lista de títulos inválidos para épicas."""
    return [
        "",  # Vacío
        " ",  # Solo espacios
        "a" * 501,  # Muy largo (>500 chars)
    ]


@pytest.fixture
def version_conflict_error() -> dict[str, Any]:
    """Respuesta de error de conflicto de versión."""
    return {
        "detail": "Version conflict. The epic has been modified by another user.",
        "status_code": 409,
    }
