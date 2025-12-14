"""
Fixtures específicas para tests E2E (End-to-End).

Proporciona configuración y mocks especializados para simular
flujos completos de usuario en el servidor MCP de Taiga.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from faker import Faker


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable


# ============================================================================
# CONFIGURACIÓN E2E
# ============================================================================


class E2ETestConfig:
    """Configuración para tests E2E."""

    # Timeouts específicos para E2E
    default_timeout: int = 60  # segundos máximo por test
    operation_timeout: int = 5  # segundos por operación

    # Prefijos para datos de prueba
    project_prefix: str = "E2E_TEST_"
    milestone_prefix: str = "E2E_Sprint_"
    epic_prefix: str = "E2E_Epic_"

    # IDs base para mocks consistentes
    base_project_id: int = 999000
    base_user_id: int = 888000


@pytest.fixture(scope="module")
def e2e_config() -> E2ETestConfig:
    """Configuración global para tests E2E."""
    return E2ETestConfig()


@pytest.fixture
def faker_e2e() -> Faker:
    """Instancia de Faker con seed fijo para reproducibilidad E2E."""
    fake = Faker()
    Faker.seed(42)
    return fake


# ============================================================================
# STATEFUL MOCKS PARA E2E
# ============================================================================


class StatefulTaigaMock:
    """
    Mock con estado para simular una instancia real de Taiga.

    Mantiene estado interno para simular operaciones CRUD reales,
    permitiendo que los tests E2E validen flujos completos.
    """

    def __init__(self, faker: Faker, config: E2ETestConfig) -> None:
        self.faker = faker
        self.config = config
        self._reset_state()

    def _reset_state(self) -> None:
        """Reinicia el estado interno del mock."""
        # Contadores para IDs únicos
        self._next_project_id = self.config.base_project_id
        self._next_milestone_id = 1000
        self._next_epic_id = 2000
        self._next_userstory_id = 3000
        self._next_task_id = 4000
        self._next_issue_id = 5000
        self._next_wiki_id = 6000
        self._next_membership_id = 7000

        # Almacenes de datos
        self.projects: dict[int, dict[str, Any]] = {}
        self.milestones: dict[int, dict[str, Any]] = {}
        self.epics: dict[int, dict[str, Any]] = {}
        self.userstories: dict[int, dict[str, Any]] = {}
        self.tasks: dict[int, dict[str, Any]] = {}
        self.issues: dict[int, dict[str, Any]] = {}
        self.wiki_pages: dict[int, dict[str, Any]] = {}
        self.memberships: dict[int, dict[str, Any]] = {}

        # Relaciones
        self.epic_userstories: dict[int, list[int]] = {}

    def _get_next_id(self, entity_type: str) -> int:
        """Obtiene el siguiente ID único para una entidad."""
        id_map = {
            "project": "_next_project_id",
            "milestone": "_next_milestone_id",
            "epic": "_next_epic_id",
            "userstory": "_next_userstory_id",
            "task": "_next_task_id",
            "issue": "_next_issue_id",
            "wiki": "_next_wiki_id",
            "membership": "_next_membership_id",
        }
        attr = id_map.get(entity_type, "_next_project_id")
        current_id = getattr(self, attr)
        setattr(self, attr, current_id + 1)
        return current_id

    # === Proyectos ===
    async def create_project(self, **kwargs: Any) -> dict[str, Any]:
        """Crea un proyecto simulado."""
        project_id = self._get_next_id("project")
        project = {
            "id": project_id,
            "name": kwargs.get("name", f"Project {project_id}"),
            "description": kwargs.get("description", ""),
            "slug": kwargs.get("name", "project").lower().replace(" ", "-"),
            "is_private": kwargs.get("is_private", True),
            "is_backlog_activated": kwargs.get("is_backlog_activated", True),
            "is_kanban_activated": kwargs.get("is_kanban_activated", False),
            "is_wiki_activated": kwargs.get("is_wiki_activated", True),
            "is_issues_activated": kwargs.get("is_issues_activated", True),
            "created_date": date.today().isoformat(),
            "members": [],
            "owner": self.config.base_user_id,
            "version": 1,
        }
        self.projects[project_id] = project
        return project

    async def get_project(self, project_id: int) -> dict[str, Any]:
        """Obtiene un proyecto por ID."""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        return self.projects[project_id]

    async def update_project(self, project_id: int, **kwargs: Any) -> dict[str, Any]:
        """Actualiza un proyecto."""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        project = self.projects[project_id]
        project.update(kwargs)
        project["version"] += 1
        return project

    async def delete_project(self, project_id: int) -> None:
        """Elimina un proyecto y sus datos relacionados (cascade delete)."""
        if project_id in self.projects:
            del self.projects[project_id]
            # Limpiar datos relacionados (cascade delete)
            self.milestones = {
                k: v for k, v in self.milestones.items() if v.get("project") != project_id
            }
            self.epics = {k: v for k, v in self.epics.items() if v.get("project") != project_id}
            self.userstories = {
                k: v for k, v in self.userstories.items() if v.get("project") != project_id
            }
            self.issues = {k: v for k, v in self.issues.items() if v.get("project") != project_id}
            self.wiki_pages = {
                k: v for k, v in self.wiki_pages.items() if v.get("project") != project_id
            }
            self.memberships = {
                k: v for k, v in self.memberships.items() if v.get("project") != project_id
            }

    async def list_projects(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista todos los proyectos."""
        return list(self.projects.values())

    # === Milestones (Sprints) ===
    async def create_milestone(self, **kwargs: Any) -> dict[str, Any]:
        """Crea un milestone/sprint."""
        milestone_id = self._get_next_id("milestone")
        project_id = kwargs.get("project_id", self.config.base_project_id)
        milestone = {
            "id": milestone_id,
            "name": kwargs.get("name", f"Sprint {milestone_id}"),
            "project": project_id,
            "estimated_start": kwargs.get("estimated_start", date.today().isoformat()),
            "estimated_finish": kwargs.get(
                "estimated_finish",
                (date.today() + timedelta(days=14)).isoformat(),
            ),
            "closed": False,
            "created_date": date.today().isoformat(),
            "version": 1,
            "user_stories": [],
        }
        self.milestones[milestone_id] = milestone
        return milestone

    async def get_milestone(self, milestone_id: int) -> dict[str, Any]:
        """Obtiene un milestone por ID."""
        if milestone_id not in self.milestones:
            raise ValueError(f"Milestone {milestone_id} not found")
        milestone = self.milestones[milestone_id]
        # Incluir user stories del milestone
        milestone["user_stories"] = [
            us for us in self.userstories.values() if us.get("milestone") == milestone_id
        ]
        return milestone

    async def update_milestone(self, milestone_id: int, **kwargs: Any) -> dict[str, Any]:
        """Actualiza un milestone."""
        if milestone_id not in self.milestones:
            raise ValueError(f"Milestone {milestone_id} not found")
        milestone = self.milestones[milestone_id]
        milestone.update(kwargs)
        milestone["version"] += 1
        return milestone

    async def delete_milestone(self, milestone_id: int) -> None:
        """Elimina un milestone."""
        if milestone_id in self.milestones:
            del self.milestones[milestone_id]

    async def list_milestones(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista milestones con filtros opcionales."""
        result = list(self.milestones.values())
        if kwargs.get("project_id"):
            result = [m for m in result if m["project"] == kwargs["project_id"]]
        if "closed" in kwargs and kwargs["closed"] is not None:
            result = [m for m in result if m["closed"] == kwargs["closed"]]
        return result

    async def get_milestone_stats(self, milestone_id: int) -> dict[str, Any]:
        """Obtiene estadísticas de un milestone."""
        if milestone_id not in self.milestones:
            raise ValueError(f"Milestone {milestone_id} not found")
        stories = [us for us in self.userstories.values() if us.get("milestone") == milestone_id]
        completed = [s for s in stories if s.get("is_closed", False)]
        return {
            "total_userstories": len(stories),
            "completed_userstories": len(completed),
            "total_points": len(stories) * 5.0,
            "completed_points": len(completed) * 5.0,
        }

    # === Épicas ===
    async def create_epic(self, **kwargs: Any) -> dict[str, Any]:
        """Crea una épica."""
        epic_id = self._get_next_id("epic")
        project_id = kwargs.get("project_id", self.config.base_project_id)
        epic = {
            "id": epic_id,
            "ref": epic_id % 1000,
            "subject": kwargs.get("subject", f"Epic {epic_id}"),
            "description": kwargs.get("description", ""),
            "project": project_id,
            "color": kwargs.get("color", "#A5694F"),
            "status": kwargs.get("status", 1),
            "assigned_to": kwargs.get("assigned_to"),
            "tags": kwargs.get("tags", []),
            "created_date": date.today().isoformat(),
            "version": 1,
        }
        self.epics[epic_id] = epic
        self.epic_userstories[epic_id] = []
        return epic

    async def get_epic(self, epic_id: int) -> dict[str, Any]:
        """Obtiene una épica por ID."""
        if epic_id not in self.epics:
            raise ValueError(f"Epic {epic_id} not found")
        return self.epics[epic_id]

    async def update_epic(self, epic_id: int, **kwargs: Any) -> dict[str, Any]:
        """Actualiza una épica."""
        if epic_id not in self.epics:
            raise ValueError(f"Epic {epic_id} not found")
        epic = self.epics[epic_id]
        epic.update(kwargs)
        epic["version"] += 1
        return epic

    async def delete_epic(self, epic_id: int) -> None:
        """Elimina una épica."""
        if epic_id in self.epics:
            del self.epics[epic_id]
            if epic_id in self.epic_userstories:
                del self.epic_userstories[epic_id]

    async def list_epics(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista épicas con filtros opcionales."""
        result = list(self.epics.values())
        if kwargs.get("project_id"):
            result = [e for e in result if e["project"] == kwargs["project_id"]]
        return result

    # === User Stories ===
    async def create_userstory(self, **kwargs: Any) -> dict[str, Any]:
        """Crea una user story."""
        us_id = self._get_next_id("userstory")
        project_id = kwargs.get("project_id", self.config.base_project_id)
        userstory = {
            "id": us_id,
            "ref": us_id % 1000,
            "subject": kwargs.get("subject", f"User Story {us_id}"),
            "description": kwargs.get("description", ""),
            "project": project_id,
            "milestone": kwargs.get("milestone"),
            "status": kwargs.get("status", 1),
            "is_closed": False,
            "assigned_to": kwargs.get("assigned_to"),
            "tags": kwargs.get("tags", []),
            "created_date": date.today().isoformat(),
            "version": 1,
        }
        self.userstories[us_id] = userstory
        return userstory

    async def get_userstory(self, userstory_id: int) -> dict[str, Any]:
        """Obtiene una user story por ID."""
        if userstory_id not in self.userstories:
            raise ValueError(f"User Story {userstory_id} not found")
        return self.userstories[userstory_id]

    async def update_userstory(self, userstory_id: int, **kwargs: Any) -> dict[str, Any]:
        """Actualiza una user story."""
        if userstory_id not in self.userstories:
            raise ValueError(f"User Story {userstory_id} not found")
        userstory = self.userstories[userstory_id]
        userstory.update(kwargs)
        userstory["version"] += 1
        return userstory

    async def delete_userstory(self, userstory_id: int) -> None:
        """Elimina una user story."""
        if userstory_id in self.userstories:
            del self.userstories[userstory_id]

    async def list_userstories(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista user stories con filtros."""
        result = list(self.userstories.values())
        if kwargs.get("project_id"):
            result = [us for us in result if us["project"] == kwargs["project_id"]]
        if kwargs.get("milestone_id"):
            result = [us for us in result if us["milestone"] == kwargs["milestone_id"]]
        return result

    # === Issues ===
    async def create_issue(self, **kwargs: Any) -> dict[str, Any]:
        """Crea un issue."""
        issue_id = self._get_next_id("issue")
        project_id = kwargs.get("project_id", self.config.base_project_id)
        issue = {
            "id": issue_id,
            "ref": issue_id % 1000,
            "subject": kwargs.get("subject", f"Issue {issue_id}"),
            "description": kwargs.get("description", ""),
            "project": project_id,
            "type": kwargs.get("type", 1),
            "priority": kwargs.get("priority", 3),
            "severity": kwargs.get("severity", 3),
            "status": kwargs.get("status", 1),
            "is_closed": False,
            "assigned_to": kwargs.get("assigned_to"),
            "tags": kwargs.get("tags", []),
            "created_date": date.today().isoformat(),
            "version": 1,
        }
        self.issues[issue_id] = issue
        return issue

    async def get_issue(self, issue_id: int) -> dict[str, Any]:
        """Obtiene un issue por ID."""
        if issue_id not in self.issues:
            raise ValueError(f"Issue {issue_id} not found")
        return self.issues[issue_id]

    async def update_issue(self, issue_id: int, **kwargs: Any) -> dict[str, Any]:
        """Actualiza un issue."""
        if issue_id not in self.issues:
            raise ValueError(f"Issue {issue_id} not found")
        issue = self.issues[issue_id]
        issue.update(kwargs)
        issue["version"] += 1
        return issue

    async def delete_issue(self, issue_id: int) -> None:
        """Elimina un issue."""
        if issue_id in self.issues:
            del self.issues[issue_id]

    async def list_issues(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista issues con filtros."""
        result = list(self.issues.values())
        if kwargs.get("project_id"):
            result = [i for i in result if i["project"] == kwargs["project_id"]]
        if "is_closed" in kwargs and kwargs["is_closed"] is not None:
            result = [i for i in result if i["is_closed"] == kwargs["is_closed"]]
        return result

    # === Wiki ===
    async def create_wiki_page(self, **kwargs: Any) -> dict[str, Any]:
        """Crea una página wiki."""
        wiki_id = self._get_next_id("wiki")
        project_id = kwargs.get("project_id", self.config.base_project_id)
        slug = kwargs.get("slug", f"page-{wiki_id}")
        wiki_page = {
            "id": wiki_id,
            "slug": slug,
            "content": kwargs.get("content", ""),
            "project": project_id,
            "created_date": date.today().isoformat(),
            "modified_date": date.today().isoformat(),
            "version": 1,
            "owner": self.config.base_user_id,
        }
        self.wiki_pages[wiki_id] = wiki_page
        # Devolver copia para que tests puedan comparar versiones antes/después
        return wiki_page.copy()

    async def get_wiki_page(self, wiki_id: int) -> dict[str, Any]:
        """Obtiene una página wiki por ID."""
        if wiki_id not in self.wiki_pages:
            raise ValueError(f"Wiki page {wiki_id} not found")
        return self.wiki_pages[wiki_id]

    async def get_wiki_page_by_slug(self, project_id: int, slug: str) -> dict[str, Any]:
        """Obtiene una página wiki por slug."""
        for page in self.wiki_pages.values():
            if page["project"] == project_id and page["slug"] == slug:
                return page
        raise ValueError(f"Wiki page with slug {slug} not found")

    async def update_wiki_page(self, wiki_id: int, **kwargs: Any) -> dict[str, Any]:
        """Actualiza una página wiki."""
        if wiki_id not in self.wiki_pages:
            raise ValueError(f"Wiki page {wiki_id} not found")
        page = self.wiki_pages[wiki_id]
        page.update(kwargs)
        page["modified_date"] = date.today().isoformat()
        page["version"] += 1
        # Devolver copia para que tests puedan comparar versiones antes/después
        return page.copy()

    async def delete_wiki_page(self, wiki_id: int) -> None:
        """Elimina una página wiki."""
        if wiki_id in self.wiki_pages:
            del self.wiki_pages[wiki_id]

    async def list_wiki_pages(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista páginas wiki."""
        result = list(self.wiki_pages.values())
        if kwargs.get("project_id"):
            result = [p for p in result if p["project"] == kwargs["project_id"]]
        return result

    # === Memberships (Team) ===
    async def create_membership(self, **kwargs: Any) -> dict[str, Any]:
        """Crea una membresía de proyecto."""
        membership_id = self._get_next_id("membership")
        project_id = kwargs.get("project_id", self.config.base_project_id)
        membership = {
            "id": membership_id,
            "project": project_id,
            "role": kwargs.get("role", 1),
            "user": kwargs.get("user_id"),
            "email": kwargs.get("email", f"user{membership_id}@test.com"),
            "is_admin": kwargs.get("is_admin", False),
            "created_at": date.today().isoformat(),
        }
        self.memberships[membership_id] = membership
        return membership

    async def get_membership(self, membership_id: int) -> dict[str, Any]:
        """Obtiene una membresía por ID."""
        if membership_id not in self.memberships:
            raise ValueError(f"Membership {membership_id} not found")
        return self.memberships[membership_id]

    async def update_membership(self, membership_id: int, **kwargs: Any) -> dict[str, Any]:
        """Actualiza una membresía."""
        if membership_id not in self.memberships:
            raise ValueError(f"Membership {membership_id} not found")
        membership = self.memberships[membership_id]
        membership.update(kwargs)
        return membership

    async def delete_membership(self, membership_id: int) -> None:
        """Elimina una membresía."""
        if membership_id in self.memberships:
            del self.memberships[membership_id]

    async def list_memberships(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Lista membresías de un proyecto."""
        result = list(self.memberships.values())
        if kwargs.get("project_id"):
            result = [m for m in result if m["project"] == kwargs["project_id"]]
        return result


@pytest_asyncio.fixture
async def stateful_mock(
    faker_e2e: Faker, e2e_config: E2ETestConfig
) -> AsyncGenerator[StatefulTaigaMock, None]:
    """Mock con estado para tests E2E."""
    mock = StatefulTaigaMock(faker_e2e, e2e_config)
    yield mock
    # Cleanup: reset state después del test
    mock._reset_state()


# ============================================================================
# CLIENTE TAIGA MOCK PARA E2E
# ============================================================================


@pytest_asyncio.fixture
async def e2e_taiga_client(
    stateful_mock: StatefulTaigaMock,
) -> AsyncGenerator[MagicMock, None]:
    """
    Cliente Taiga mock configurado para tests E2E.

    Usa el StatefulTaigaMock para simular comportamiento real.
    """
    client = MagicMock()

    # Configurar context manager
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    # === Proyectos ===
    client.create_project = AsyncMock(side_effect=stateful_mock.create_project)
    client.get_project = AsyncMock(side_effect=stateful_mock.get_project)
    client.update_project = AsyncMock(side_effect=stateful_mock.update_project)
    client.delete_project = AsyncMock(side_effect=stateful_mock.delete_project)
    client.list_projects = AsyncMock(side_effect=stateful_mock.list_projects)

    # === Milestones ===
    client.create_milestone = AsyncMock(side_effect=stateful_mock.create_milestone)
    client.get_milestone = AsyncMock(side_effect=stateful_mock.get_milestone)
    client.update_milestone = AsyncMock(side_effect=stateful_mock.update_milestone)
    client.delete_milestone = AsyncMock(side_effect=stateful_mock.delete_milestone)
    client.list_milestones = AsyncMock(side_effect=stateful_mock.list_milestones)
    client.get_milestone_stats = AsyncMock(side_effect=stateful_mock.get_milestone_stats)
    client.watch_milestone = AsyncMock(return_value={"id": 1, "total_watchers": 1})
    client.unwatch_milestone = AsyncMock(return_value={"id": 1, "total_watchers": 0})

    # === Épicas ===
    client.create_epic = AsyncMock(side_effect=stateful_mock.create_epic)
    client.get_epic = AsyncMock(side_effect=stateful_mock.get_epic)
    client.update_epic = AsyncMock(side_effect=stateful_mock.update_epic)
    client.delete_epic = AsyncMock(side_effect=stateful_mock.delete_epic)
    client.list_epics = AsyncMock(side_effect=stateful_mock.list_epics)

    # === User Stories ===
    client.create_userstory = AsyncMock(side_effect=stateful_mock.create_userstory)
    client.get_userstory = AsyncMock(side_effect=stateful_mock.get_userstory)
    client.update_userstory = AsyncMock(side_effect=stateful_mock.update_userstory)
    client.delete_userstory = AsyncMock(side_effect=stateful_mock.delete_userstory)
    client.list_userstories = AsyncMock(side_effect=stateful_mock.list_userstories)

    # === Issues ===
    client.create_issue = AsyncMock(side_effect=stateful_mock.create_issue)
    client.get_issue = AsyncMock(side_effect=stateful_mock.get_issue)
    client.update_issue = AsyncMock(side_effect=stateful_mock.update_issue)
    client.delete_issue = AsyncMock(side_effect=stateful_mock.delete_issue)
    client.list_issues = AsyncMock(side_effect=stateful_mock.list_issues)
    client.get_issue_history = AsyncMock(return_value=[])
    client.upvote_issue = AsyncMock(return_value={"id": 1, "total_voters": 1})
    client.downvote_issue = AsyncMock(return_value={"id": 1, "total_voters": 0})

    # === Wiki ===
    client.create_wiki_page = AsyncMock(side_effect=stateful_mock.create_wiki_page)
    client.get_wiki_page = AsyncMock(side_effect=stateful_mock.get_wiki_page)
    client.get_wiki_page_by_slug = AsyncMock(side_effect=stateful_mock.get_wiki_page_by_slug)
    client.update_wiki_page = AsyncMock(side_effect=stateful_mock.update_wiki_page)
    client.delete_wiki_page = AsyncMock(side_effect=stateful_mock.delete_wiki_page)
    client.list_wiki_pages = AsyncMock(side_effect=stateful_mock.list_wiki_pages)

    # === Memberships ===
    client.create_membership = AsyncMock(side_effect=stateful_mock.create_membership)
    client.get_membership = AsyncMock(side_effect=stateful_mock.get_membership)
    client.update_membership = AsyncMock(side_effect=stateful_mock.update_membership)
    client.delete_membership = AsyncMock(side_effect=stateful_mock.delete_membership)
    client.list_memberships = AsyncMock(side_effect=stateful_mock.list_memberships)

    # === Autenticación ===
    client.authenticate = AsyncMock(
        return_value={
            "auth_token": "e2e-test-token",
            "refresh_token": "e2e-refresh-token",
            "id": 888000,
            "username": "e2e_user",
        }
    )

    yield client


# ============================================================================
# CLEANUP MANAGER PARA E2E
# ============================================================================


class E2ECleanupManager:
    """Manager para registrar y ejecutar limpieza de recursos E2E."""

    def __init__(self) -> None:
        self._cleanup_actions: list[Callable[[], Any]] = []
        self._created_ids: dict[str, list[int]] = {
            "projects": [],
            "milestones": [],
            "epics": [],
            "userstories": [],
            "issues": [],
            "wiki_pages": [],
            "memberships": [],
        }

    def register(
        self,
        entity_type: str,
        entity_id: int,
        cleanup_func: Callable[[], Any] | None = None,
    ) -> None:
        """Registra una entidad para limpieza."""
        if entity_type in self._created_ids:
            self._created_ids[entity_type].append(entity_id)
        if cleanup_func:
            self._cleanup_actions.append(cleanup_func)

    async def cleanup_all(self) -> None:
        """Ejecuta todas las acciones de limpieza registradas."""
        for action in reversed(self._cleanup_actions):
            try:
                if asyncio.iscoroutinefunction(action):
                    await action()
                else:
                    action()
            except Exception:
                pass  # Ignorar errores de limpieza
        self._cleanup_actions.clear()
        for key in self._created_ids:
            self._created_ids[key].clear()

    def get_created_ids(self, entity_type: str) -> list[int]:
        """Obtiene los IDs creados de un tipo de entidad."""
        return self._created_ids.get(entity_type, [])


@pytest_asyncio.fixture
async def e2e_cleanup() -> AsyncGenerator[E2ECleanupManager, None]:
    """Manager de limpieza para tests E2E."""
    manager = E2ECleanupManager()
    yield manager
    await manager.cleanup_all()


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Configuración adicional de pytest para E2E."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow (deselect with '-m \"not slow\"')")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modificar items de tests durante la colección."""
    for item in items:
        # Agregar marker e2e a todos los tests en este directorio
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            # Agregar timeout para tests E2E
            item.add_marker(pytest.mark.timeout(60))

        # Agregar marker asyncio si es función async
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
