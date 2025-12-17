"""
Test E2E 4.8.5: Flujo de gestión de equipo.

Valida el ciclo completo de gestión de miembros del equipo en Taiga:
invitar → asignar roles → gestionar permisos

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


# Constantes para roles (IDs típicos de Taiga)
ROLE_ADMIN = 1
ROLE_DEVELOPER = 2
ROLE_DESIGNER = 3
ROLE_TESTER = 4
ROLE_VIEWER = 5


@pytest.mark.e2e
@pytest.mark.asyncio
class TestTeamWorkflowE2E:
    """Tests E2E para el flujo completo de gestión de equipo."""

    async def test_complete_team_management_lifecycle(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test del ciclo de vida completo de gestión de equipo.

        Flujo:
        1. Crear proyecto
        2. Invitar miembros al equipo
        3. Asignar roles
        4. Actualizar permisos
        5. Listar miembros
        6. Eliminar miembro
        """
        # === FASE 1: Crear proyecto ===
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}Team_Lifecycle",
            description="Proyecto para test de gestión de equipo",
            is_backlog_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register(
            "projects",
            project_id,
            lambda: e2e_taiga_client.delete_project(project_id),
        )

        # === FASE 2: Invitar miembros al equipo ===
        # Invitar desarrollador
        developer = await e2e_taiga_client.create_membership(
            project_id=project_id,
            email="developer@test.com",
            role=ROLE_DEVELOPER,
            is_admin=False,
        )
        assert developer["id"] is not None
        assert developer["role"] == ROLE_DEVELOPER
        assert developer["project"] == project_id

        # Invitar diseñador
        designer = await e2e_taiga_client.create_membership(
            project_id=project_id,
            email="designer@test.com",
            role=ROLE_DESIGNER,
            is_admin=False,
        )
        assert designer["role"] == ROLE_DESIGNER

        # Invitar tester
        tester = await e2e_taiga_client.create_membership(
            project_id=project_id,
            email="tester@test.com",
            role=ROLE_TESTER,
            is_admin=False,
        )
        assert tester["role"] == ROLE_TESTER

        # === FASE 3: Listar miembros ===
        all_members = await e2e_taiga_client.list_memberships(project_id=project_id)
        assert len(all_members) >= 3

        member_emails = [m["email"] for m in all_members]
        assert "developer@test.com" in member_emails
        assert "designer@test.com" in member_emails
        assert "tester@test.com" in member_emails

        # === FASE 4: Actualizar rol de un miembro ===
        # Promover desarrollador a admin
        updated_developer = await e2e_taiga_client.update_membership(
            developer["id"],
            role=ROLE_ADMIN,
            is_admin=True,
        )
        assert updated_developer["role"] == ROLE_ADMIN
        assert updated_developer["is_admin"] is True

        # === FASE 5: Verificar miembro actualizado ===
        retrieved_developer = await e2e_taiga_client.get_membership(developer["id"])
        assert retrieved_developer["role"] == ROLE_ADMIN

        # === FASE 6: Eliminar miembro ===
        await e2e_taiga_client.delete_membership(tester["id"])

        remaining_members = await e2e_taiga_client.list_memberships(project_id=project_id)
        remaining_ids = [m["id"] for m in remaining_members]
        assert tester["id"] not in remaining_ids

    async def test_team_role_assignments(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de asignación de roles a miembros.

        Valida diferentes combinaciones de roles.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}TeamRoles",
            description="Proyecto para test de roles",
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear miembros con diferentes roles
        roles_to_test = [
            ("admin@test.com", ROLE_ADMIN, True),
            ("developer1@test.com", ROLE_DEVELOPER, False),
            ("developer2@test.com", ROLE_DEVELOPER, False),
            ("designer@test.com", ROLE_DESIGNER, False),
            ("tester@test.com", ROLE_TESTER, False),
            ("viewer@test.com", ROLE_VIEWER, False),
        ]

        created_members: list[dict[str, Any]] = []
        for email, role, is_admin in roles_to_test:
            member = await e2e_taiga_client.create_membership(
                project_id=project_id,
                email=email,
                role=role,
                is_admin=is_admin,
            )
            created_members.append(member)
            assert member["role"] == role
            assert member["is_admin"] == is_admin

        assert len(created_members) == 6

        # Verificar listado
        all_members = await e2e_taiga_client.list_memberships(project_id=project_id)
        assert len(all_members) >= 6

    async def test_member_role_changes(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de cambios de rol de miembros.

        Valida promociones y degradaciones de roles.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}RoleChanges",
            description="Proyecto para test de cambios de rol",
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear miembro como viewer
        member = await e2e_taiga_client.create_membership(
            project_id=project_id,
            email="changeable@test.com",
            role=ROLE_VIEWER,
            is_admin=False,
        )
        member_id = member["id"]

        assert member["role"] == ROLE_VIEWER

        # Promoción 1: Viewer → Tester
        updated = await e2e_taiga_client.update_membership(
            member_id,
            role=ROLE_TESTER,
        )
        assert updated["role"] == ROLE_TESTER

        # Promoción 2: Tester → Developer
        updated = await e2e_taiga_client.update_membership(
            member_id,
            role=ROLE_DEVELOPER,
        )
        assert updated["role"] == ROLE_DEVELOPER

        # Promoción 3: Developer → Admin
        updated = await e2e_taiga_client.update_membership(
            member_id,
            role=ROLE_ADMIN,
            is_admin=True,
        )
        assert updated["role"] == ROLE_ADMIN
        assert updated["is_admin"] is True

        # Degradación: Admin → Developer
        updated = await e2e_taiga_client.update_membership(
            member_id,
            role=ROLE_DEVELOPER,
            is_admin=False,
        )
        assert updated["role"] == ROLE_DEVELOPER
        assert updated["is_admin"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
class TestTeamAdvancedFeaturesE2E:
    """Tests E2E de características avanzadas de gestión de equipo."""

    async def test_multiple_projects_team_management(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de gestión de equipo en múltiples proyectos.

        Un usuario puede tener diferentes roles en diferentes proyectos.
        """
        # Crear dos proyectos
        project1 = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}TeamMulti1",
        )
        project2 = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}TeamMulti2",
        )

        e2e_cleanup.register("projects", project1["id"])
        e2e_cleanup.register("projects", project2["id"])

        # Añadir mismo usuario con diferentes roles
        member_email = "multiproject@test.com"

        # Admin en proyecto 1
        member_p1 = await e2e_taiga_client.create_membership(
            project_id=project1["id"],
            email=member_email,
            role=ROLE_ADMIN,
            is_admin=True,
        )
        assert member_p1["role"] == ROLE_ADMIN

        # Viewer en proyecto 2
        member_p2 = await e2e_taiga_client.create_membership(
            project_id=project2["id"],
            email=member_email,
            role=ROLE_VIEWER,
            is_admin=False,
        )
        assert member_p2["role"] == ROLE_VIEWER

        # Verificar membresías independientes
        members_p1 = await e2e_taiga_client.list_memberships(project_id=project1["id"])
        members_p2 = await e2e_taiga_client.list_memberships(project_id=project2["id"])

        # El mismo email, pero diferentes roles
        p1_member = next((m for m in members_p1 if m["email"] == member_email), None)
        p2_member = next((m for m in members_p2 if m["email"] == member_email), None)

        assert p1_member is not None
        assert p2_member is not None
        assert p1_member["role"] != p2_member["role"]

    async def test_team_work_assignment(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de asignación de trabajo a miembros del equipo.

        Simula asignación de user stories e issues a miembros específicos.
        """
        # Setup proyecto y equipo
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}TeamWork",
            is_backlog_activated=True,
            is_issues_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear miembros del equipo
        dev1 = await e2e_taiga_client.create_membership(
            project_id=project_id,
            email="dev1@test.com",
            role=ROLE_DEVELOPER,
            user_id=1001,
        )

        dev2 = await e2e_taiga_client.create_membership(
            project_id=project_id,
            email="dev2@test.com",
            role=ROLE_DEVELOPER,
            user_id=1002,
        )

        # Crear user stories y asignar
        us1 = await e2e_taiga_client.create_userstory(
            project_id=project_id,
            subject="Story for Dev 1",
            assigned_to=dev1.get("user"),
        )

        us2 = await e2e_taiga_client.create_userstory(
            project_id=project_id,
            subject="Story for Dev 2",
            assigned_to=dev2.get("user"),
        )

        # Crear issues y asignar
        issue1 = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Bug for Dev 1",
            type=1,
            priority=2,
            severity=3,
            assigned_to=dev1.get("user"),
        )

        issue2 = await e2e_taiga_client.create_issue(
            project_id=project_id,
            subject="Bug for Dev 2",
            type=1,
            priority=2,
            severity=3,
            assigned_to=dev2.get("user"),
        )

        # Verificar asignaciones
        assert us1["assigned_to"] == dev1.get("user")
        assert us2["assigned_to"] == dev2.get("user")
        assert issue1["assigned_to"] == dev1.get("user")
        assert issue2["assigned_to"] == dev2.get("user")

    async def test_team_member_removal_impact(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test del impacto de eliminar un miembro del equipo.

        Verifica el comportamiento cuando se elimina un miembro.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}MemberRemoval",
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear varios miembros
        members: list[dict[str, Any]] = []
        for i in range(5):
            member = await e2e_taiga_client.create_membership(
                project_id=project_id,
                email=f"member{i}@test.com",
                role=ROLE_DEVELOPER,
            )
            members.append(member)

        # Verificar que todos existen
        all_members = await e2e_taiga_client.list_memberships(project_id=project_id)
        assert len(all_members) >= 5

        # Eliminar miembros alternos
        for i in range(0, 5, 2):  # Eliminar 0, 2, 4
            await e2e_taiga_client.delete_membership(members[i]["id"])

        # Verificar que solo quedan los miembros no eliminados
        remaining = await e2e_taiga_client.list_memberships(project_id=project_id)
        remaining_ids = {m["id"] for m in remaining}

        # Members 0, 2, 4 deberían estar eliminados
        assert members[0]["id"] not in remaining_ids
        assert members[2]["id"] not in remaining_ids
        assert members[4]["id"] not in remaining_ids

        # Members 1, 3 deberían seguir
        assert members[1]["id"] in remaining_ids
        assert members[3]["id"] in remaining_ids

    async def test_team_cascade_delete_with_project(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de eliminación en cascada de membresías al eliminar proyecto.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}TeamCascade",
        )
        project_id = project["id"]

        # Crear varios miembros
        for i in range(3):
            await e2e_taiga_client.create_membership(
                project_id=project_id,
                email=f"cascade{i}@test.com",
                role=ROLE_DEVELOPER,
            )

        # Verificar que existen
        members_before = await e2e_taiga_client.list_memberships(project_id=project_id)
        assert len(members_before) >= 3

        # Eliminar proyecto (no registrar cleanup ya que lo eliminaremos manualmente)
        await e2e_taiga_client.delete_project(project_id)

        # Verificar que no quedan membresías del proyecto
        members_after = await e2e_taiga_client.list_memberships(project_id=project_id)
        assert len(members_after) == 0
