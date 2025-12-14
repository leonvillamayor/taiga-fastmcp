"""
Test E2E 4.8.2: Flujo completo de sprint (milestone).

Valida el ciclo de vida completo de un sprint en Taiga:
crear sprint → añadir stories → seguir progreso → cerrar

Criterios de aceptación:
- Datos de prueba aislados
- Limpieza automática
- Ejecución < 60 segundos
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

import pytest


if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import E2ECleanupManager, E2ETestConfig, StatefulTaigaMock


@pytest.mark.e2e
@pytest.mark.asyncio
class TestSprintWorkflowE2E:
    """Tests E2E para el flujo completo de gestión de sprints."""

    async def test_complete_sprint_lifecycle(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test del ciclo de vida completo de un sprint.

        Flujo:
        1. Crear proyecto base
        2. Crear sprint
        3. Añadir user stories al sprint
        4. Verificar progreso
        5. Completar stories
        6. Cerrar sprint
        7. Verificar métricas finales
        """
        # === FASE 1: Crear proyecto base ===
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}Sprint_Lifecycle",
            description="Proyecto para test de ciclo de sprint",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register(
            "projects",
            project_id,
            lambda: e2e_taiga_client.delete_project(project_id),
        )

        # === FASE 2: Crear sprint ===
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint = await e2e_taiga_client.create_milestone(
            project_id=project_id,
            name=f"{e2e_config.milestone_prefix}Lifecycle_Test",
            estimated_start=start_date.isoformat(),
            estimated_finish=end_date.isoformat(),
        )

        assert sprint["id"] is not None
        assert sprint["name"].startswith(e2e_config.milestone_prefix)
        assert sprint["closed"] is False
        assert sprint["project"] == project_id

        sprint_id = sprint["id"]

        # === FASE 3: Añadir user stories al sprint ===
        created_stories: list[dict[str, Any]] = []
        for i in range(5):
            story = await e2e_taiga_client.create_userstory(
                project_id=project_id,
                subject=f"Sprint Story {i + 1}",
                description=f"Historia #{i + 1} del sprint",
                milestone=sprint_id,
            )
            created_stories.append(story)

        assert len(created_stories) == 5

        # Verificar que las stories están en el sprint
        sprint_stories = await e2e_taiga_client.list_userstories(
            project_id=project_id,
            milestone_id=sprint_id,
        )
        assert len(sprint_stories) == 5

        # === FASE 4: Verificar progreso inicial ===
        stats = await e2e_taiga_client.get_milestone_stats(sprint_id)
        assert stats["total_userstories"] == 5
        assert stats["completed_userstories"] == 0

        # === FASE 5: Completar algunas stories ===
        # Completar 3 de 5 stories
        for i in range(3):
            story_id = created_stories[i]["id"]
            await e2e_taiga_client.update_userstory(
                story_id,
                is_closed=True,
            )

        # Verificar progreso intermedio
        stats = await e2e_taiga_client.get_milestone_stats(sprint_id)
        assert stats["completed_userstories"] == 3

        # === FASE 6: Completar resto y cerrar sprint ===
        # Completar stories restantes
        for i in range(3, 5):
            story_id = created_stories[i]["id"]
            await e2e_taiga_client.update_userstory(
                story_id,
                is_closed=True,
            )

        # Cerrar sprint
        closed_sprint = await e2e_taiga_client.update_milestone(
            sprint_id,
            closed=True,
        )
        assert closed_sprint["closed"] is True

        # === FASE 7: Verificar métricas finales ===
        final_stats = await e2e_taiga_client.get_milestone_stats(sprint_id)
        assert final_stats["total_userstories"] == 5
        assert final_stats["completed_userstories"] == 5

    async def test_sprint_with_multiple_iterations(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de proyecto con múltiples sprints.

        Valida la gestión de sprints secuenciales.
        """
        # Crear proyecto
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}MultiSprint",
            description="Proyecto con múltiples sprints",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear 3 sprints consecutivos
        sprints: list[dict[str, Any]] = []
        base_date = date.today()

        for i in range(3):
            start = base_date + timedelta(days=i * 14)
            end = start + timedelta(days=13)
            sprint = await e2e_taiga_client.create_milestone(
                project_id=project_id,
                name=f"{e2e_config.milestone_prefix}Iteration_{i + 1}",
                estimated_start=start.isoformat(),
                estimated_finish=end.isoformat(),
            )
            sprints.append(sprint)

        assert len(sprints) == 3

        # Verificar listado de sprints
        all_sprints = await e2e_taiga_client.list_milestones(project_id=project_id)
        assert len(all_sprints) >= 3

        # Cerrar el primer sprint
        await e2e_taiga_client.update_milestone(
            sprints[0]["id"],
            closed=True,
        )

        # Verificar filtrado por estado
        open_sprints = await e2e_taiga_client.list_milestones(
            project_id=project_id,
            closed=False,
        )
        closed_sprints = await e2e_taiga_client.list_milestones(
            project_id=project_id,
            closed=True,
        )

        assert len(open_sprints) >= 2
        assert len(closed_sprints) >= 1

    async def test_story_movement_between_sprints(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de movimiento de stories entre sprints.

        Simula el escenario común de mover trabajo no completado
        al siguiente sprint.
        """
        # Crear proyecto
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}StoryMove",
            description="Proyecto para mover stories entre sprints",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear dos sprints
        sprint1 = await e2e_taiga_client.create_milestone(
            project_id=project_id,
            name=f"{e2e_config.milestone_prefix}Sprint_1",
            estimated_start=date.today().isoformat(),
            estimated_finish=(date.today() + timedelta(days=14)).isoformat(),
        )

        sprint2 = await e2e_taiga_client.create_milestone(
            project_id=project_id,
            name=f"{e2e_config.milestone_prefix}Sprint_2",
            estimated_start=(date.today() + timedelta(days=14)).isoformat(),
            estimated_finish=(date.today() + timedelta(days=28)).isoformat(),
        )

        # Crear story en sprint 1
        story = await e2e_taiga_client.create_userstory(
            project_id=project_id,
            subject="Story to move",
            milestone=sprint1["id"],
        )

        # Verificar que está en sprint 1
        assert story["milestone"] == sprint1["id"]

        # Mover story a sprint 2
        updated_story = await e2e_taiga_client.update_userstory(
            story["id"],
            milestone=sprint2["id"],
        )

        assert updated_story["milestone"] == sprint2["id"]

        # Verificar que ya no está en sprint 1
        sprint1_stories = await e2e_taiga_client.list_userstories(
            project_id=project_id,
            milestone_id=sprint1["id"],
        )
        sprint1_story_ids = [s["id"] for s in sprint1_stories]
        assert story["id"] not in sprint1_story_ids

        # Verificar que está en sprint 2
        sprint2_stories = await e2e_taiga_client.list_userstories(
            project_id=project_id,
            milestone_id=sprint2["id"],
        )
        sprint2_story_ids = [s["id"] for s in sprint2_stories]
        assert story["id"] in sprint2_story_ids


@pytest.mark.e2e
@pytest.mark.asyncio
class TestSprintProgressTrackingE2E:
    """Tests E2E para seguimiento de progreso de sprint."""

    async def test_sprint_progress_tracking(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de seguimiento de progreso del sprint.

        Valida las estadísticas del sprint conforme se completan stories.
        """
        # Setup proyecto y sprint
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}Progress_Track",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        sprint = await e2e_taiga_client.create_milestone(
            project_id=project_id,
            name=f"{e2e_config.milestone_prefix}Progress",
            estimated_start=date.today().isoformat(),
            estimated_finish=(date.today() + timedelta(days=14)).isoformat(),
        )
        sprint_id = sprint["id"]

        # Crear 10 stories
        stories: list[dict[str, Any]] = []
        for i in range(10):
            story = await e2e_taiga_client.create_userstory(
                project_id=project_id,
                subject=f"Progress Story {i + 1}",
                milestone=sprint_id,
            )
            stories.append(story)

        # Verificar progreso inicial: 0%
        stats = await e2e_taiga_client.get_milestone_stats(sprint_id)
        assert stats["total_userstories"] == 10
        assert stats["completed_userstories"] == 0

        # Completar 5 stories (50%)
        for i in range(5):
            await e2e_taiga_client.update_userstory(
                stories[i]["id"],
                is_closed=True,
            )

        stats = await e2e_taiga_client.get_milestone_stats(sprint_id)
        assert stats["completed_userstories"] == 5

        # Completar todas (100%)
        for i in range(5, 10):
            await e2e_taiga_client.update_userstory(
                stories[i]["id"],
                is_closed=True,
            )

        stats = await e2e_taiga_client.get_milestone_stats(sprint_id)
        assert stats["completed_userstories"] == 10

    async def test_sprint_configuration_updates(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de actualización de configuración de sprint.

        Valida cambios en fechas y otros parámetros del sprint.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}SprintConfig",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        original_start = date.today()
        original_end = original_start + timedelta(days=14)

        sprint = await e2e_taiga_client.create_milestone(
            project_id=project_id,
            name=f"{e2e_config.milestone_prefix}ConfigTest",
            estimated_start=original_start.isoformat(),
            estimated_finish=original_end.isoformat(),
        )
        sprint_id = sprint["id"]

        # Actualizar nombre
        updated = await e2e_taiga_client.update_milestone(
            sprint_id,
            name=f"{e2e_config.milestone_prefix}ConfigTest_Updated",
        )
        assert "Updated" in updated["name"]

        # Extender fechas (simular sprint extendido)
        new_end = original_end + timedelta(days=7)
        updated = await e2e_taiga_client.update_milestone(
            sprint_id,
            estimated_finish=new_end.isoformat(),
        )
        assert updated["estimated_finish"] == new_end.isoformat()

    async def test_sprint_deletion_cascade(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de eliminación de sprint.

        Verifica el comportamiento al eliminar un sprint con stories.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}SprintDelete",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        sprint = await e2e_taiga_client.create_milestone(
            project_id=project_id,
            name=f"{e2e_config.milestone_prefix}ToDelete",
            estimated_start=date.today().isoformat(),
            estimated_finish=(date.today() + timedelta(days=14)).isoformat(),
        )
        sprint_id = sprint["id"]

        # Crear stories en el sprint
        for i in range(3):
            await e2e_taiga_client.create_userstory(
                project_id=project_id,
                subject=f"Story in deleted sprint {i + 1}",
                milestone=sprint_id,
            )

        # Verificar que las stories están asignadas
        stories_before = await e2e_taiga_client.list_userstories(
            project_id=project_id,
            milestone_id=sprint_id,
        )
        assert len(stories_before) == 3

        # Eliminar sprint
        await e2e_taiga_client.delete_milestone(sprint_id)

        # Verificar que el sprint fue eliminado
        all_sprints = await e2e_taiga_client.list_milestones(project_id=project_id)
        sprint_ids = [s["id"] for s in all_sprints]
        assert sprint_id not in sprint_ids
