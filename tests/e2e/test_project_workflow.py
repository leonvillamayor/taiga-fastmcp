"""
Test E2E 4.8.1: Flujo completo de proyecto.

Valida el ciclo de vida completo de un proyecto en Taiga:
crear → configurar → modificar → archivar → eliminar

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


@pytest.mark.e2e
@pytest.mark.asyncio
class TestProjectWorkflowE2E:
    """Tests E2E para el flujo completo de gestión de proyectos."""

    async def test_complete_project_lifecycle(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test del ciclo de vida completo de un proyecto.

        Flujo:
        1. Crear proyecto
        2. Verificar creación
        3. Configurar módulos (backlog, kanban, wiki)
        4. Actualizar metadatos
        5. Listar proyectos
        6. Eliminar proyecto
        7. Verificar eliminación
        """
        # === FASE 1: Crear proyecto ===
        project_name = f"{e2e_config.project_prefix}Lifecycle_Test"
        project_data = await e2e_taiga_client.create_project(
            name=project_name,
            description="Proyecto de prueba E2E para ciclo de vida completo",
            is_private=True,
            is_backlog_activated=True,
            is_wiki_activated=True,
            is_issues_activated=True,
        )

        # Registrar para limpieza
        e2e_cleanup.register(
            "projects",
            project_data["id"],
            lambda: e2e_taiga_client.delete_project(project_data["id"]),
        )

        # Verificar creación
        assert project_data["id"] is not None
        assert project_data["name"] == project_name
        assert project_data["is_private"] is True
        assert project_data["is_backlog_activated"] is True

        project_id = project_data["id"]

        # === FASE 2: Verificar proyecto existe ===
        retrieved_project = await e2e_taiga_client.get_project(project_id)
        assert retrieved_project["id"] == project_id
        assert retrieved_project["name"] == project_name

        # === FASE 3: Configurar módulos ===
        # Activar Kanban
        updated_project = await e2e_taiga_client.update_project(
            project_id,
            is_kanban_activated=True,
        )
        assert updated_project["is_kanban_activated"] is True

        # === FASE 4: Actualizar metadatos ===
        new_description = "Descripción actualizada del proyecto E2E"
        updated_project = await e2e_taiga_client.update_project(
            project_id,
            description=new_description,
        )
        assert updated_project["description"] == new_description
        assert updated_project["version"] > 1  # Versión incrementada

        # === FASE 5: Listar proyectos ===
        all_projects = await e2e_taiga_client.list_projects()
        project_ids = [p["id"] for p in all_projects]
        assert project_id in project_ids

        # === FASE 6: Eliminar proyecto ===
        await e2e_taiga_client.delete_project(project_id)

        # === FASE 7: Verificar eliminación ===
        all_projects_after = await e2e_taiga_client.list_projects()
        project_ids_after = [p["id"] for p in all_projects_after]
        assert project_id not in project_ids_after

    async def test_project_with_multiple_modules(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de proyecto con múltiples módulos activados.

        Valida la configuración de todos los módulos disponibles.
        """
        project_name = f"{e2e_config.project_prefix}MultiModule_Test"

        # Crear proyecto con todos los módulos
        project = await e2e_taiga_client.create_project(
            name=project_name,
            description="Proyecto con múltiples módulos",
            is_private=False,
            is_backlog_activated=True,
            is_kanban_activated=True,
            is_wiki_activated=True,
            is_issues_activated=True,
        )

        e2e_cleanup.register(
            "projects",
            project["id"],
            lambda: e2e_taiga_client.delete_project(project["id"]),
        )

        # Verificar configuración de módulos
        assert project["is_backlog_activated"] is True
        assert project["is_wiki_activated"] is True
        assert project["is_issues_activated"] is True

        # Actualizar módulo kanban
        updated = await e2e_taiga_client.update_project(
            project["id"],
            is_kanban_activated=True,
        )
        assert updated["is_kanban_activated"] is True

    async def test_project_configuration_changes(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de cambios de configuración en proyecto.

        Valida múltiples actualizaciones secuenciales.
        """
        # Crear proyecto básico
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}ConfigChanges_Test",
            description="Test de cambios de configuración",
            is_private=True,
        )

        e2e_cleanup.register(
            "projects",
            project["id"],
            lambda: e2e_taiga_client.delete_project(project["id"]),
        )

        project_id = project["id"]
        initial_version = project["version"]

        # Cambio 1: Actualizar nombre
        updated = await e2e_taiga_client.update_project(
            project_id,
            name=f"{e2e_config.project_prefix}ConfigChanges_Updated",
        )
        assert updated["version"] > initial_version

        # Cambio 2: Cambiar privacidad
        updated = await e2e_taiga_client.update_project(
            project_id,
            is_private=False,
        )
        assert updated["is_private"] is False

        # Cambio 3: Actualizar descripción
        updated = await e2e_taiga_client.update_project(
            project_id,
            description="Nueva descripción después de cambios",
        )
        assert "Nueva descripción" in updated["description"]

        # Verificar versión final incrementada
        assert updated["version"] > initial_version

    async def test_multiple_projects_management(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de gestión de múltiples proyectos.

        Crea varios proyectos y valida operaciones entre ellos.
        """
        created_projects: list[dict[str, Any]] = []

        # Crear 3 proyectos
        for i in range(3):
            project = await e2e_taiga_client.create_project(
                name=f"{e2e_config.project_prefix}MultiProject_{i}",
                description=f"Proyecto múltiple #{i}",
                is_private=True,
            )
            created_projects.append(project)
            e2e_cleanup.register(
                "projects",
                project["id"],
                lambda pid=project["id"]: e2e_taiga_client.delete_project(pid),
            )

        # Verificar que todos fueron creados
        assert len(created_projects) == 3

        # Listar y verificar
        all_projects = await e2e_taiga_client.list_projects()
        created_ids = {p["id"] for p in created_projects}
        listed_ids = {p["id"] for p in all_projects}
        assert created_ids.issubset(listed_ids)

        # Actualizar uno de ellos
        target_project = created_projects[1]
        updated = await e2e_taiga_client.update_project(
            target_project["id"],
            name=f"{e2e_config.project_prefix}MultiProject_1_Updated",
        )
        assert "Updated" in updated["name"]

        # Eliminar uno y verificar que los otros siguen
        await e2e_taiga_client.delete_project(created_projects[0]["id"])

        remaining_projects = await e2e_taiga_client.list_projects()
        remaining_ids = {p["id"] for p in remaining_projects}
        assert created_projects[0]["id"] not in remaining_ids
        assert created_projects[1]["id"] in remaining_ids
        assert created_projects[2]["id"] in remaining_ids


@pytest.mark.e2e
@pytest.mark.asyncio
class TestProjectWithContentE2E:
    """Tests E2E de proyecto con contenido asociado."""

    async def test_project_with_epic_and_userstories(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de proyecto con épica y user stories.

        Flujo:
        1. Crear proyecto
        2. Crear épica
        3. Crear user stories
        4. Verificar estructura
        5. Eliminar proyecto (cascada)
        """
        # Crear proyecto
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}WithContent_Test",
            description="Proyecto con contenido E2E",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register(
            "projects",
            project_id,
            lambda: e2e_taiga_client.delete_project(project_id),
        )

        # Crear épica
        epic = await e2e_taiga_client.create_epic(
            project_id=project_id,
            subject=f"{e2e_config.epic_prefix}Main Epic",
            description="Épica principal del proyecto",
        )
        assert epic["project"] == project_id

        # Crear user stories
        for i in range(3):
            us = await e2e_taiga_client.create_userstory(
                project_id=project_id,
                subject=f"User Story {i + 1}",
                description=f"Historia de usuario #{i + 1}",
            )
            assert us["project"] == project_id

        # Verificar estructura
        epics = await e2e_taiga_client.list_epics(project_id=project_id)
        assert len(epics) >= 1

        userstories = await e2e_taiga_client.list_userstories(project_id=project_id)
        assert len(userstories) >= 3

        # Eliminar proyecto (debe eliminar contenido en cascada)
        await e2e_taiga_client.delete_project(project_id)

        # Verificar que el contenido fue eliminado
        remaining_epics = await e2e_taiga_client.list_epics(project_id=project_id)
        remaining_us = await e2e_taiga_client.list_userstories(project_id=project_id)
        assert len(remaining_epics) == 0
        assert len(remaining_us) == 0

    async def test_project_creation_validation(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de validación en creación de proyecto.

        Verifica que los campos obligatorios están presentes.
        """
        # Crear proyecto con datos mínimos
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}Minimal_Test",
        )

        e2e_cleanup.register(
            "projects",
            project["id"],
        )

        # Verificar campos por defecto
        assert project["id"] is not None
        assert project["name"] is not None
        assert "slug" in project
        assert "created_date" in project
        assert project["version"] == 1
