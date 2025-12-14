"""
Tests de snapshot para respuestas de proyecto y epic.

Test 4.10.1: Snapshot de respuestas de proyecto
Test 4.10.2: Snapshot de respuestas de epic

Estos tests verifican que el formato de las respuestas no cambia
inesperadamente entre versiones.
"""

from typing import Any

from syrupy import SnapshotAssertion

from src.application.responses.epic_responses import (
    EpicListResponse,
    EpicResponse,
)
from src.application.responses.project_responses import (
    ProjectListResponse,
    ProjectResponse,
    ProjectStatsResponse,
)


class TestSnapshotProjectResponses:
    """Test 4.10.1: Snapshot de respuestas de proyecto."""

    def test_project_response_format(
        self,
        snapshot_json: SnapshotAssertion,
        sample_project: dict[str, Any],
    ) -> None:
        """Formato de respuesta de proyecto no cambia."""
        response = ProjectResponse.model_validate(sample_project)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="project_response")

    def test_project_list_response_format(
        self,
        snapshot_json: SnapshotAssertion,
        sample_project: dict[str, Any],
    ) -> None:
        """Formato de respuesta de lista de proyectos no cambia."""
        projects = [sample_project, {**sample_project, "id": 123457, "name": "Project 2"}]
        response = ProjectListResponse.from_api_response(projects)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="project_list_response")

    def test_project_stats_response_format(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de respuesta de estadísticas de proyecto no cambia."""
        stats_data = {
            "total_milestones": 5,
            "total_points": 150.0,
            "closed_points": 75.0,
            "defined_points": 150.0,
            "assigned_points": 120.0,
            "speed": 25.0,
            "total_userstories": 30,
            "total_issues": 10,
            "closed_issues": 5,
        }
        response = ProjectStatsResponse.model_validate(stats_data)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="project_stats_response")

    def test_project_response_with_minimal_data(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de respuesta de proyecto con datos mínimos."""
        minimal_project = {
            "id": 1,
            "name": "Minimal Project",
            "slug": "minimal-project",
        }
        response = ProjectResponse.model_validate(minimal_project)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="project_response_minimal")


class TestSnapshotEpicResponses:
    """Test 4.10.2: Snapshot de respuestas de epic."""

    def test_epic_response_format(
        self,
        snapshot_json: SnapshotAssertion,
        sample_epic: dict[str, Any],
    ) -> None:
        """Formato de respuesta de epic no cambia."""
        response = EpicResponse.model_validate(sample_epic)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="epic_response")

    def test_epic_list_response_format(
        self,
        snapshot_json: SnapshotAssertion,
        sample_epic: dict[str, Any],
    ) -> None:
        """Formato de respuesta de lista de epics no cambia."""
        epics = [
            sample_epic,
            {**sample_epic, "id": 456790, "ref": 6, "subject": "Epic 2"},
        ]
        response = EpicListResponse.from_api_response(epics)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="epic_list_response")

    def test_epic_response_with_minimal_data(
        self,
        snapshot_json: SnapshotAssertion,
    ) -> None:
        """Formato de respuesta de epic con datos mínimos."""
        minimal_epic = {
            "id": 1,
            "ref": 1,
            "subject": "Minimal Epic",
            "project": 123,
        }
        response = EpicResponse.model_validate(minimal_epic)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="epic_response_minimal")

    def test_epic_response_with_related_userstories(
        self,
        snapshot_json: SnapshotAssertion,
        sample_epic: dict[str, Any],
    ) -> None:
        """Formato de respuesta de epic con user stories relacionadas."""
        epic_with_stories = {
            **sample_epic,
            "user_stories": [
                {"id": 100, "ref": 1, "subject": "User Story 1"},
                {"id": 101, "ref": 2, "subject": "User Story 2"},
            ],
        }
        response = EpicResponse.model_validate(epic_with_stories)
        response_dict = response.model_dump(mode="json")

        assert response_dict == snapshot_json(name="epic_response_with_stories")
