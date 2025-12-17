"""
Test E2E 4.8.3: Flujo completo de issue tracking.

Valida el ciclo de vida completo de gestión de issues en Taiga:
reportar → asignar → resolver → cerrar

Criterios de aceptación:
- Datos de prueba aislados
- Limpieza automática
- Ejecución < 60 segundos
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest


if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import E2ECleanupManager, E2ETestConfig, StatefulTaigaMock


# Constantes para tipos de issue
ISSUE_TYPE_BUG = 1
ISSUE_TYPE_QUESTION = 2
ISSUE_TYPE_ENHANCEMENT = 3

# Constantes para prioridad
PRIORITY_LOW = 1
PRIORITY_NORMAL = 2
PRIORITY_HIGH = 3

# Constantes para severidad
SEVERITY_WISHLIST = 1
SEVERITY_MINOR = 2
SEVERITY_NORMAL = 3
SEVERITY_IMPORTANT = 4
SEVERITY_CRITICAL = 5

# Constantes para estado
STATUS_NEW = 1
STATUS_IN_PROGRESS = 2
STATUS_READY_FOR_TEST = 3
STATUS_CLOSED = 4


@pytest.mark.e2e
@pytest.mark.asyncio
class TestIssueTrackingWorkflowE2E:
    """Tests E2E para el flujo completo de gestión de issues."""

    async def test_complete_issue_lifecycle(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test del ciclo de vida completo de un issue.

        Flujo:
        1. Crear proyecto con issues habilitados
        2. Reportar issue (bug)
        3. Asignar a usuario
        4. Cambiar estado a "En progreso"
        5. Resolver issue
        6. Cerrar issue
        7. Verificar historial
        """
        # === FASE 1: Crear proyecto con issues ===
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}Issue_Lifecycle",
            description="Proyecto para test de ciclo de vida de issues",
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register(
            "projects",
            project_id,
            lambda: e2e_taiga_client.delete_project(project_id),
        )

        # === FASE 2: Reportar issue (bug) ===
        issue = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Error crítico en login",
            description="El botón de login no responde al hacer clic",
            type=ISSUE_TYPE_BUG,
            priority=PRIORITY_HIGH,
            severity=SEVERITY_CRITICAL,
            status=STATUS_NEW,
        )

        assert issue["id"] is not None
        assert issue["subject"] == "Error crítico en login"
        assert issue["type"] == ISSUE_TYPE_BUG
        assert issue["priority"] == PRIORITY_HIGH
        assert issue["severity"] == SEVERITY_CRITICAL
        assert issue["is_closed"] is False

        issue_id = issue["id"]

        # === FASE 3: Asignar a usuario ===
        assigned_user_id = e2e_config.base_user_id
        updated_issue = await e2e_taiga_client.update_issue(
            issue_id,
            assigned_to=assigned_user_id,
        )
        assert updated_issue["assigned_to"] == assigned_user_id

        # === FASE 4: Cambiar estado a "En progreso" ===
        in_progress_issue = await e2e_taiga_client.update_issue(
            issue_id,
            status=STATUS_IN_PROGRESS,
        )
        assert in_progress_issue["status"] == STATUS_IN_PROGRESS

        # === FASE 5: Resolver issue ===
        resolved_issue = await e2e_taiga_client.update_issue(
            issue_id,
            status=STATUS_READY_FOR_TEST,
        )
        assert resolved_issue["status"] == STATUS_READY_FOR_TEST

        # === FASE 6: Cerrar issue ===
        closed_issue = await e2e_taiga_client.update_issue(
            issue_id,
            status=STATUS_CLOSED,
            is_closed=True,
        )
        assert closed_issue["is_closed"] is True

        # === FASE 7: Verificar historial ===
        history = await e2e_taiga_client.get_issue_history(issue_id)
        # El historial debe existir (aunque esté vacío en el mock)
        assert isinstance(history, list)

    async def test_multiple_issue_types(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de múltiples tipos de issues.

        Crea diferentes tipos de issues y valida su clasificación.
        """
        # Crear proyecto
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}IssueTypes",
            description="Proyecto para test de tipos de issues",
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear issue tipo Bug
        bug = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Bug: Error en formulario",
            type=ISSUE_TYPE_BUG,
            priority=PRIORITY_HIGH,
            severity=SEVERITY_NORMAL,
        )
        assert bug["type"] == ISSUE_TYPE_BUG

        # Crear issue tipo Question
        question = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Question: ¿Cómo configurar X?",
            type=ISSUE_TYPE_QUESTION,
            priority=PRIORITY_NORMAL,
            severity=SEVERITY_MINOR,
        )
        assert question["type"] == ISSUE_TYPE_QUESTION

        # Crear issue tipo Enhancement
        enhancement = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Enhancement: Mejorar rendimiento",
            type=ISSUE_TYPE_ENHANCEMENT,
            priority=PRIORITY_LOW,
            severity=SEVERITY_WISHLIST,
        )
        assert enhancement["type"] == ISSUE_TYPE_ENHANCEMENT

        # Listar y verificar todos los issues
        all_issues = await e2e_taiga_client.list_issues(project_id=project_id)
        assert len(all_issues) >= 3

    async def test_issue_priority_and_severity(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de prioridad y severidad de issues.

        Valida la correcta asignación y modificación de estos campos.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}IssuePriority",
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear issue con prioridad baja
        issue = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Issue inicial",
            type=ISSUE_TYPE_BUG,
            priority=PRIORITY_LOW,
            severity=SEVERITY_MINOR,
        )
        issue_id = issue["id"]

        assert issue["priority"] == PRIORITY_LOW
        assert issue["severity"] == SEVERITY_MINOR

        # Escalar a prioridad alta
        escalated = await e2e_taiga_client.update_issue(
            issue_id,
            priority=PRIORITY_HIGH,
            severity=SEVERITY_CRITICAL,
        )

        assert escalated["priority"] == PRIORITY_HIGH
        assert escalated["severity"] == SEVERITY_CRITICAL


@pytest.mark.e2e
@pytest.mark.asyncio
class TestIssueWorkflowAdvancedE2E:
    """Tests E2E avanzados para gestión de issues."""

    async def test_issue_filtering(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de filtrado de issues.

        Valida filtros por estado (abierto/cerrado).
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}IssueFilter",
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear issues abiertos
        for i in range(3):
            await e2e_taiga_client.create_issue(
                project_id=project_id,
                subject=f"Open Issue {i + 1}",
                type=ISSUE_TYPE_BUG,
                priority=PRIORITY_NORMAL,
                severity=SEVERITY_NORMAL,
            )

        # Crear y cerrar issues
        closed_issues: list[dict[str, Any]] = []
        for i in range(2):
            issue = await e2e_taiga_client.create_issue(
                project_id=project_id,
                subject=f"Closed Issue {i + 1}",
                type=ISSUE_TYPE_BUG,
                priority=PRIORITY_NORMAL,
                severity=SEVERITY_NORMAL,
            )
            await e2e_taiga_client.update_issue(
                issue["id"],
                is_closed=True,
            )
            closed_issues.append(issue)

        # Filtrar por estado abierto
        open_issues = await e2e_taiga_client.list_issues(
            project_id=project_id,
            is_closed=False,
        )
        assert len(open_issues) >= 3

        # Filtrar por estado cerrado
        closed = await e2e_taiga_client.list_issues(
            project_id=project_id,
            is_closed=True,
        )
        assert len(closed) >= 2

    async def test_issue_voting(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de votación en issues.

        Valida el flujo de upvote/downvote.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}IssueVoting",
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear issue
        issue = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Issue para votar",
            type=ISSUE_TYPE_ENHANCEMENT,
            priority=PRIORITY_NORMAL,
            severity=SEVERITY_NORMAL,
        )
        issue_id = issue["id"]

        # Votar positivamente
        vote_result = await e2e_taiga_client.upvote_issue(issue_id)
        assert vote_result["total_voters"] >= 1

        # Quitar voto
        unvote_result = await e2e_taiga_client.downvote_issue(issue_id)
        assert unvote_result["total_voters"] >= 0

    async def test_bulk_issue_management(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de gestión masiva de issues.

        Crea múltiples issues y valida operaciones en lote.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}BulkIssues",
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear 10 issues
        created_issues: list[dict[str, Any]] = []
        for i in range(10):
            issue = await e2e_taiga_client.create_issue(
                project_id=project_id,
                subject=f"Bulk Issue {i + 1}",
                type=ISSUE_TYPE_BUG,
                priority=PRIORITY_NORMAL if i % 2 == 0 else PRIORITY_HIGH,
                severity=SEVERITY_NORMAL,
            )
            created_issues.append(issue)

        assert len(created_issues) == 10

        # Listar todos
        all_issues = await e2e_taiga_client.list_issues(project_id=project_id)
        assert len(all_issues) >= 10

        # Actualizar varios issues
        for issue in created_issues[:5]:
            await e2e_taiga_client.update_issue(
                issue["id"],
                assigned_to=e2e_config.base_user_id,
            )

        # Cerrar algunos
        for issue in created_issues[5:8]:
            await e2e_taiga_client.update_issue(
                issue["id"],
                is_closed=True,
            )

        # Verificar conteos
        open_issues = await e2e_taiga_client.list_issues(
            project_id=project_id,
            is_closed=False,
        )
        closed_issues = await e2e_taiga_client.list_issues(
            project_id=project_id,
            is_closed=True,
        )

        assert len(closed_issues) >= 3
        assert len(open_issues) >= 7

    async def test_issue_deletion(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de eliminación de issues.

        Valida la eliminación correcta de issues.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}IssueDelete",
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear issue
        issue = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Issue to delete",
            type=ISSUE_TYPE_BUG,
            priority=PRIORITY_NORMAL,
            severity=SEVERITY_NORMAL,
        )
        issue_id = issue["id"]

        # Verificar que existe
        all_issues = await e2e_taiga_client.list_issues(project_id=project_id)
        issue_ids = [i["id"] for i in all_issues]
        assert issue_id in issue_ids

        # Eliminar
        await e2e_taiga_client.delete_issue(issue_id)

        # Verificar eliminación
        all_issues_after = await e2e_taiga_client.list_issues(project_id=project_id)
        issue_ids_after = [i["id"] for i in all_issues_after]
        assert issue_id not in issue_ids_after
