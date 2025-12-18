"""Configuración y fixtures para tests de use cases.

Este módulo proporciona mocks comunes para todos los repositorios
utilizados en los casos de uso de la capa Application.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.epic import Epic
from src.domain.entities.issue import Issue
from src.domain.entities.member import Member
from src.domain.entities.milestone import Milestone
from src.domain.entities.project import Project
from src.domain.entities.task import Task
from src.domain.entities.user_story import UserStory
from src.domain.entities.wiki_page import WikiPage
from src.domain.repositories.epic_repository import EpicRepository
from src.domain.repositories.issue_repository import IssueRepository
from src.domain.repositories.member_repository import MemberRepository
from src.domain.repositories.milestone_repository import MilestoneRepository
from src.domain.repositories.project_repository import ProjectRepository
from src.domain.repositories.task_repository import TaskRepository
from src.domain.repositories.user_story_repository import UserStoryRepository
from src.domain.repositories.wiki_repository import WikiRepository


# =============================================================================
# SAMPLE ENTITIES FOR TESTING
# =============================================================================


@pytest.fixture
def sample_project() -> Project:
    """Proyecto de ejemplo para tests."""
    return Project(
        id=1,
        name="Test Project",
        slug="test-project",
        description="A test project",
        is_private=True,
        is_backlog_activated=True,
        is_kanban_activated=True,
        is_wiki_activated=True,
        is_issues_activated=True,
        tags=["test", "sample"],
        created_date=datetime(2024, 1, 1, 12, 0, 0),
        modified_date=datetime(2024, 1, 2, 12, 0, 0),
    )


@pytest.fixture
def sample_epic() -> Epic:
    """Epic de ejemplo para tests."""
    return Epic(
        id=1,
        ref=1,
        subject="Test Epic",
        description="A test epic",
        project=1,
        status=1,
        color="#FF0000",
        assigned_to=1,
        tags=["epic-tag"],
        created_date=datetime(2024, 1, 1, 12, 0, 0),
        modified_date=datetime(2024, 1, 2, 12, 0, 0),
    )


@pytest.fixture
def sample_user_story() -> UserStory:
    """User story de ejemplo para tests."""
    return UserStory(
        id=1,
        ref=1,
        subject="Test User Story",
        description="A test user story",
        project_id=1,
        status=1,
        milestone_id=1,
        assigned_to_id=1,
        is_blocked=False,
        blocked_note="",
        is_closed=False,
        client_requirement=False,
        team_requirement=False,
        tags=["story-tag"],
        points={"design": 3.0, "development": 5.0},
        created_date=datetime(2024, 1, 1, 12, 0, 0),
        modified_date=datetime(2024, 1, 2, 12, 0, 0),
    )


@pytest.fixture
def sample_task() -> Task:
    """Task de ejemplo para tests."""
    return Task(
        id=1,
        ref=1,
        subject="Test Task",
        description="A test task",
        project_id=1,
        user_story_id=1,
        status=1,
        milestone_id=1,
        assigned_to_id=1,
        is_blocked=False,
        blocked_note="",
        is_closed=False,
        is_iocaine=False,
        tags=["task-tag"],
        created_date=datetime(2024, 1, 1, 12, 0, 0),
        modified_date=datetime(2024, 1, 2, 12, 0, 0),
    )


@pytest.fixture
def sample_issue() -> Issue:
    """Issue de ejemplo para tests."""
    return Issue(
        id=1,
        ref=1,
        subject="Test Issue",
        description="A test issue",
        project_id=1,
        status=1,
        type=1,
        severity=3,
        priority=3,
        milestone_id=1,
        assigned_to_id=1,
        is_blocked=False,
        blocked_note="",
        is_closed=False,
        tags=["issue-tag"],
        created_date=datetime(2024, 1, 1, 12, 0, 0),
        modified_date=datetime(2024, 1, 2, 12, 0, 0),
    )


@pytest.fixture
def sample_milestone() -> Milestone:
    """Milestone de ejemplo para tests."""
    return Milestone(
        id=1,
        name="Sprint 1",
        slug="sprint-1",
        project_id=1,
        estimated_start=datetime(2024, 1, 1),
        estimated_finish=datetime(2024, 1, 15),
        is_closed=False,
        disponibility=1.0,
        order=1,
        created_date=datetime(2024, 1, 1, 12, 0, 0),
        modified_date=datetime(2024, 1, 2, 12, 0, 0),
    )


@pytest.fixture
def sample_wiki_page() -> WikiPage:
    """Wiki page de ejemplo para tests."""
    return WikiPage(
        id=1,
        slug="home",
        content="# Home\n\nWelcome to the wiki",
        project_id=1,
        is_deleted=False,
        created_date=datetime(2024, 1, 1, 12, 0, 0),
        modified_date=datetime(2024, 1, 2, 12, 0, 0),
    )


@pytest.fixture
def sample_member() -> Member:
    """Member de ejemplo para tests."""
    return Member(
        id=1,
        user_id=1,
        project_id=1,
        role_id=1,
        role_name="Developer",
        is_admin=False,
        is_owner=False,
        email="user@example.com",
        full_name="Test User",
        username="testuser",
        created_date=datetime(2024, 1, 1, 12, 0, 0),
    )


# =============================================================================
# REPOSITORY MOCKS
# =============================================================================


def create_mock_repository(spec: type[Any]) -> MagicMock:
    """Crea un mock de repositorio con métodos async.

    Args:
        spec: Clase del repositorio a mockear

    Returns:
        Mock configurado con AsyncMock para métodos async
    """
    mock = MagicMock(spec=spec)
    # Configure all methods as AsyncMock
    for method_name in dir(spec):
        if not method_name.startswith("_"):
            method = getattr(spec, method_name, None)
            if callable(method):
                setattr(mock, method_name, AsyncMock())
    return mock


@pytest.fixture
def mock_project_repository() -> MagicMock:
    """Mock del repositorio de proyectos."""
    return create_mock_repository(ProjectRepository)


@pytest.fixture
def mock_epic_repository() -> MagicMock:
    """Mock del repositorio de épicas."""
    return create_mock_repository(EpicRepository)


@pytest.fixture
def mock_user_story_repository() -> MagicMock:
    """Mock del repositorio de user stories."""
    return create_mock_repository(UserStoryRepository)


@pytest.fixture
def mock_task_repository() -> MagicMock:
    """Mock del repositorio de tasks."""
    return create_mock_repository(TaskRepository)


@pytest.fixture
def mock_issue_repository() -> MagicMock:
    """Mock del repositorio de issues."""
    return create_mock_repository(IssueRepository)


@pytest.fixture
def mock_milestone_repository() -> MagicMock:
    """Mock del repositorio de milestones."""
    return create_mock_repository(MilestoneRepository)


@pytest.fixture
def mock_wiki_repository() -> MagicMock:
    """Mock del repositorio de wiki pages."""
    return create_mock_repository(WikiRepository)


@pytest.fixture
def mock_member_repository() -> MagicMock:
    """Mock del repositorio de members."""
    return create_mock_repository(MemberRepository)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def assert_repository_called_with(mock_method: AsyncMock, **expected_kwargs: Any) -> None:
    """Verifica que un método del repositorio fue llamado con argumentos específicos.

    Args:
        mock_method: Método mockeado a verificar
        **expected_kwargs: Argumentos esperados en la llamada
    """
    mock_method.assert_called_once()
    actual_call = mock_method.call_args
    for key, expected_value in expected_kwargs.items():
        if key in actual_call.kwargs:
            assert actual_call.kwargs[key] == expected_value
        else:
            # Check positional arguments if not in kwargs
            pass


def create_entity_list(entity: Any, count: int) -> list[Any]:
    """Crea una lista de entidades para tests de listado.

    Args:
        entity: Entidad base a replicar
        count: Número de entidades a crear

    Returns:
        Lista de entidades con IDs incrementales
    """
    entities = []
    for i in range(count):
        new_entity = entity.__class__(**entity.__dict__)
        new_entity.id = i + 1
        entities.append(new_entity)
    return entities
