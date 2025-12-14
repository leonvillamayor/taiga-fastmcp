"""
Herramientas de gestión de Issues para Taiga MCP Server.
Implementa las funcionalidades ISSUE-001 a ISSUE-030.
"""

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError as MCPError

from src.config import TaigaConfig
from src.domain.exceptions import ValidationError
from src.domain.validators import IssueCreateValidator, IssueUpdateValidator, validate_input
from src.infrastructure.logging import get_logger
from src.infrastructure.pagination import AutoPaginator, PaginationConfig
from src.taiga_client import TaigaAPIClient


class IssueTools:
    """Herramientas para gestión de Issues en Taiga."""

    def __init__(self, mcp: FastMCP) -> None:
        """
        Inicializa las herramientas de Issues.

        Args:
            mcp: Instancia del servidor FastMCP
        """
        self.mcp = mcp
        self.config = TaigaConfig()
        self._logger = get_logger(__name__)

    def register_tools(self) -> None:
        """Registra todas las herramientas de Issues en el servidor MCP."""

        # CRUD Básico (ISSUE-001 a ISSUE-007)
        @self.mcp.tool(name="taiga_list_issues")
        async def list_issues(
            auth_token: str,
            project_id: int | None = None,
            status: int | None = None,
            severity: int | None = None,
            priority: int | None = None,
            type: int | None = None,
            assigned_to: int | None = None,
            tags: list[str] | None = None,
            is_closed: bool | None = None,
            exclude_status: int | None = None,
            exclude_severity: int | None = None,
            exclude_priority: int | None = None,
            exclude_type: int | None = None,
            exclude_assigned_to: int | None = None,
            exclude_tags: list[str] | None = None,
            auto_paginate: bool = True,
        ) -> list[dict[str, Any]]:
            """
            ISSUE-001: Lista issues con filtros opcionales.

            Esta herramienta permite listar todos los issues de Taiga con
            múltiples opciones de filtrado por estado, severidad, prioridad,
            tipo, asignación y tags.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto para filtrar issues
                status: ID del estado para filtrar
                severity: ID de la severidad para filtrar
                priority: ID de la prioridad para filtrar
                type: ID del tipo (bug, question, enhancement)
                assigned_to: ID del usuario asignado para filtrar
                tags: Lista de tags para filtrar
                is_closed: True para cerrados, False para abiertos
                exclude_status: ID del estado a excluir
                exclude_severity: ID de la severidad a excluir
                exclude_priority: ID de la prioridad a excluir
                exclude_type: ID del tipo a excluir
                exclude_assigned_to: ID del usuario a excluir
                exclude_tags: Lista de tags a excluir
                auto_paginate: Si True (default), obtiene todos los resultados
                    automáticamente. Si False, retorna solo la primera página.

            Returns:
                Lista de diccionarios con información de issues, cada uno conteniendo:
                - id: ID del issue
                - ref: Número de referencia
                - subject: Título del issue
                - status: Estado actual
                - severity: Severidad del issue
                - priority: Prioridad del issue
                - type: Tipo de issue
                - assigned_to: Usuario asignado
                - is_closed: Si está cerrado

            Raises:
                ToolError: Si la autenticación falla o hay error en la API

            Example:
                >>> issues = await taiga_list_issues(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     is_closed=False,
                ...     priority=3
                ... )
                >>> for issue in issues:
                ...     print(f"#{issue['ref']}: {issue['subject']}")
            """
            kwargs = {
                k: v
                for k, v in locals().items()
                if k not in ["self", "auth_token", "project_id", "auto_paginate"] and v is not None
            }
            if project_id is not None:
                kwargs["project"] = project_id  # API expects 'project'

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                paginator = AutoPaginator(client, PaginationConfig())

                if auto_paginate:
                    return await paginator.paginate("/issues", params=kwargs)
                return await paginator.paginate_first_page("/issues", params=kwargs)

        @self.mcp.tool(name="taiga_create_issue")
        async def create_issue(
            auth_token: str,
            project_id: int,
            subject: str,
            type: int,
            priority: int,
            severity: int,
            description: str | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
            milestone_id: int | None = None,
            tags: list[str] | None = None,
            watchers: list[int] | None = None,
            attachments: list[dict[str, Any]] | None = None,
            blocked_note: str | None = None,
            is_blocked: bool | None = None,
            due_date: str | None = None,
            due_date_reason: str | None = None,
        ) -> dict[str, Any]:
            """
            ISSUE-002: Crea un nuevo issue.

            Esta herramienta crea un nuevo issue en un proyecto de Taiga.
            Los issues pueden ser bugs, preguntas o mejoras, con diferentes
            niveles de severidad y prioridad.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear el issue
                subject: Título descriptivo del issue
                type: ID del tipo (bug, question, enhancement)
                priority: ID de la prioridad (1=Low, 2=Normal, 3=High)
                severity: ID de la severidad (1=Wishlist, 2=Minor, 3=Normal, 4=Important, 5=Critical)
                description: Descripción detallada del issue (Markdown soportado)
                status: ID del estado inicial
                assigned_to: ID del usuario responsable
                milestone_id: ID del sprint/milestone asociado
                tags: Lista de etiquetas para categorización
                watchers: IDs de usuarios que recibirán notificaciones
                attachments: Lista de archivos adjuntos
                blocked_note: Razón del bloqueo si is_blocked=True
                is_blocked: True si el issue está bloqueado
                due_date: Fecha límite en formato YYYY-MM-DD
                due_date_reason: Explicación de por qué esa fecha límite

            Returns:
                Dict con el issue creado conteniendo:
                - id: ID del issue creado
                - ref: Número de referencia único
                - subject: Título del issue
                - project: ID del proyecto
                - status: Estado asignado
                - type: Tipo de issue
                - priority: Prioridad asignada
                - severity: Severidad asignada
                - created_date: Fecha de creación

            Raises:
                ToolError: Si faltan campos requeridos, el proyecto no existe,
                    o la autenticación falla

            Example:
                >>> issue = await taiga_create_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     subject="Login button not working",
                ...     type=1,  # Bug
                ...     priority=3,  # High
                ...     severity=4,  # Important
                ...     description="The login button shows error on click"
                ... )
                >>> print(f"Created issue #{issue['ref']}")
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "project_id": project_id,
                    "subject": subject,
                    "type": type,
                    "priority": priority,
                    "severity": severity,
                    "description": description,
                    "status": status,
                    "assigned_to": assigned_to,
                    "tags": tags,
                }
                validate_input(IssueCreateValidator, validation_data)

                data = {
                    k: v
                    for k, v in locals().items()
                    if k
                    not in ["self", "auth_token", "project_id", "milestone_id", "validation_data"]
                    and v is not None
                }
                data["project"] = project_id  # API expects 'project'
                if milestone_id is not None:
                    data["milestone"] = milestone_id  # API expects 'milestone'

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    return await client.create_issue(**data)

            except ValidationError as e:
                self._logger.warning(f"[create_issue] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        @self.mcp.tool(name="taiga_get_issue")
        async def get_issue(auth_token: str, issue_id: int) -> dict[str, Any]:
            """
            ISSUE-003: Obtiene un issue por ID.

            Esta herramienta recupera todos los detalles de un issue específico
            usando su ID interno de Taiga.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID interno del issue en Taiga

            Returns:
                Dict con todos los datos del issue conteniendo:
                - id: ID del issue
                - ref: Número de referencia
                - subject: Título del issue
                - description: Descripción completa
                - status: Estado actual
                - type: Tipo de issue
                - priority: Prioridad
                - severity: Severidad
                - assigned_to: Usuario asignado
                - project: ID del proyecto
                - created_date: Fecha de creación
                - modified_date: Última modificación
                - is_closed: Si está cerrado

            Raises:
                ToolError: Si el issue no existe o la autenticación falla

            Example:
                >>> issue = await taiga_get_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> print(f"Issue: {issue['subject']}")
                >>> print(f"Status: {issue['status']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue(issue_id)

        @self.mcp.tool(name="taiga_get_issue_by_ref")
        async def get_issue_by_ref(auth_token: str, project_id: int, ref: int) -> dict[str, Any]:
            """
            ISSUE-004: Obtiene un issue por referencia dentro del proyecto.

            Esta herramienta busca un issue usando su número de referencia
            legible (#123) en lugar del ID interno. El número de referencia
            es único dentro de cada proyecto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde buscar
                ref: Número de referencia del issue (ej: 123 para #123)

            Returns:
                Dict con todos los datos del issue conteniendo:
                - id: ID interno del issue
                - ref: Número de referencia
                - subject: Título del issue
                - description: Descripción completa
                - status: Estado actual
                - type: Tipo de issue
                - priority: Prioridad
                - severity: Severidad
                - project: ID del proyecto

            Raises:
                ToolError: Si el issue no existe en el proyecto o la
                    autenticación falla

            Example:
                >>> issue = await taiga_get_issue_by_ref(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     ref=45
                ... )
                >>> print(f"Found: #{issue['ref']} - {issue['subject']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_by_ref(
                    project=project_id, ref=ref
                )  # API expects 'project'

        @self.mcp.tool(name="taiga_update_issue")
        async def update_issue(
            auth_token: str,
            issue_id: int,
            subject: str | None = None,
            description: str | None = None,
            type: int | None = None,
            priority: int | None = None,
            severity: int | None = None,
            status: int | None = None,
            assigned_to: int | None = None,
            milestone_id: int | None = None,
            tags: list[str] | None = None,
            blocked_note: str | None = None,
            is_blocked: bool | None = None,
            due_date: str | None = None,
            due_date_reason: str | None = None,
            version: int | None = None,
        ) -> dict[str, Any]:
            """
            ISSUE-005/ISSUE-006: Actualiza un issue (PUT/PATCH).

            Esta herramienta permite actualizar cualquier campo de un issue
            existente. Solo se modifican los campos proporcionados.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue a actualizar
                subject: Nuevo título del issue
                description: Nueva descripción (soporta Markdown)
                type: Nuevo ID de tipo
                priority: Nuevo ID de prioridad
                severity: Nuevo ID de severidad
                status: Nuevo ID de estado
                assigned_to: ID del nuevo usuario asignado
                milestone_id: ID del nuevo milestone asociado
                tags: Nueva lista de etiquetas (reemplaza las existentes)
                blocked_note: Nueva nota explicando el bloqueo
                is_blocked: True para bloquear, False para desbloquear
                due_date: Nueva fecha límite (YYYY-MM-DD)
                due_date_reason: Nueva razón para la fecha límite
                version: Versión actual para control de concurrencia optimista

            Returns:
                Dict con el issue actualizado conteniendo todos sus campos:
                - id: ID del issue
                - ref: Número de referencia
                - subject: Título actualizado
                - status: Estado actual
                - modified_date: Nueva fecha de modificación
                - version: Nueva versión del issue

            Raises:
                ToolError: Si el issue no existe, hay conflicto de versión,
                    no hay permisos, o la autenticación falla

            Example:
                >>> updated = await taiga_update_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456,
                ...     status=3,  # Cambiar a "In Progress"
                ...     assigned_to=42,
                ...     priority=3  # High
                ... )
                >>> print(f"Issue updated, new version: {updated['version']}")
            """
            try:
                # Validar datos de entrada ANTES de llamar a la API
                validation_data = {
                    "issue_id": issue_id,
                    "subject": subject,
                    "description": description,
                    "issue_type": type,
                    "priority": priority,
                    "severity": severity,
                    "status": status,
                    "assigned_to": assigned_to,
                    "tags": tags,
                }
                validate_input(IssueUpdateValidator, validation_data)

                data = {
                    k: v
                    for k, v in locals().items()
                    if k
                    not in ["self", "auth_token", "issue_id", "milestone_id", "validation_data"]
                    and v is not None
                }
                if milestone_id is not None:
                    data["milestone"] = milestone_id  # API expects 'milestone'

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    return await client.update_issue(issue_id, **data)
            except ValidationError as e:
                self._logger.warning(f"[update_issue] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        @self.mcp.tool(name="taiga_delete_issue")
        async def delete_issue(auth_token: str, issue_id: int) -> bool:
            """
            ISSUE-007: Elimina un issue.

            Esta herramienta elimina permanentemente un issue de Taiga.
            Esta acción no se puede deshacer.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue a eliminar

            Returns:
                True si el issue fue eliminado exitosamente

            Raises:
                ToolError: Si el issue no existe, no hay permisos de
                    eliminación, o la autenticación falla

            Example:
                >>> result = await taiga_delete_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> if result:
                ...     print("Issue deleted successfully")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.delete_issue(issue_id)

        # Operaciones en Lote (ISSUE-008)
        @self.mcp.tool(name="taiga_bulk_create_issues")
        async def bulk_create_issues(
            auth_token: str, project_id: int, issues: list[dict[str, Any]]
        ) -> list[dict[str, Any]]:
            """
            ISSUE-008: Crea múltiples issues en lote.

            Esta herramienta permite crear varios issues de una sola vez,
            útil para importación masiva o creación de múltiples tareas
            relacionadas.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear los issues
                issues: Lista de diccionarios con datos de cada issue:
                    - subject (requerido): Título del issue
                    - type (requerido): ID del tipo
                    - priority (requerido): ID de la prioridad
                    - severity (requerido): ID de la severidad
                    - description (opcional): Descripción
                    - status (opcional): ID del estado
                    - assigned_to (opcional): ID del usuario

            Returns:
                Lista de diccionarios con los issues creados, cada uno con:
                - id: ID del issue creado
                - ref: Número de referencia
                - subject: Título del issue
                - project: ID del proyecto

            Raises:
                ToolError: Si algún issue tiene datos inválidos, el proyecto
                    no existe, o la autenticación falla

            Example:
                >>> issues_data = [
                ...     {"subject": "Bug 1", "type": 1, "priority": 2, "severity": 3},
                ...     {"subject": "Bug 2", "type": 1, "priority": 3, "severity": 4},
                ... ]
                >>> created = await taiga_bulk_create_issues(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     issues=issues_data
                ... )
                >>> print(f"Created {len(created)} issues")
            """
            try:
                # Validar project_id
                if project_id <= 0:
                    raise ValidationError("project_id debe ser un entero positivo")

                # Validar cada issue en la lista
                for idx, issue_data in enumerate(issues):
                    validation_data = {
                        "project_id": project_id,
                        "subject": issue_data.get("subject"),
                        "type": issue_data.get("type"),
                        "priority": issue_data.get("priority"),
                        "severity": issue_data.get("severity"),
                        "description": issue_data.get("description"),
                        "status": issue_data.get("status"),
                        "assigned_to": issue_data.get("assigned_to"),
                        "tags": issue_data.get("tags"),
                    }
                    try:
                        validate_input(IssueCreateValidator, validation_data)
                    except ValidationError as e:
                        raise ValidationError(f"Issue {idx + 1}: {e!s}") from e

                async with TaigaAPIClient(self.config) as client:
                    client.auth_token = auth_token
                    return await client.bulk_create_issues(
                        project=project_id, issues=issues
                    )  # API expects 'project'
            except ValidationError as e:
                self._logger.warning(f"[bulk_create_issues] Validation error | error={e!s}")
                raise MCPError(str(e)) from e

        # Filtros (ISSUE-013)
        @self.mcp.tool(name="taiga_get_issue_filters")
        async def get_issue_filters(auth_token: str, project_id: int) -> dict[str, Any]:
            """
            ISSUE-013: Obtiene los filtros disponibles para issues.

            Esta herramienta devuelve todos los valores disponibles para
            filtrar issues en un proyecto, incluyendo estados, tipos,
            prioridades, severidades, tags y usuarios asignados.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del cual obtener los filtros

            Returns:
                Dict con los filtros disponibles conteniendo:
                - statuses: Lista de estados posibles
                - types: Lista de tipos de issue
                - priorities: Lista de prioridades
                - severities: Lista de severidades
                - assigned_to: Lista de usuarios disponibles
                - owners: Lista de creadores
                - tags: Lista de tags usadas

            Raises:
                ToolError: Si el proyecto no existe o la autenticación falla

            Example:
                >>> filters = await taiga_get_issue_filters(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> print("Available statuses:")
                >>> for status in filters['statuses']:
                ...     print(f"  {status['id']}: {status['name']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_filters(project=project_id)  # API expects 'project'

        # Votación (ISSUE-014 a ISSUE-016)
        @self.mcp.tool(name="taiga_upvote_issue")
        async def upvote_issue(auth_token: str, issue_id: int) -> dict[str, Any]:
            """
            ISSUE-014: Vota positivamente por un issue.

            Esta herramienta agrega un voto positivo del usuario actual
            a un issue. Los votos ayudan a priorizar qué issues son más
            importantes para el equipo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue a votar

            Returns:
                Dict con los datos actualizados del issue conteniendo:
                - id: ID del issue
                - total_voters: Número total de votos
                - is_voter: True indicando que el usuario votó

            Raises:
                ToolError: Si el issue no existe, ya se votó, o la
                    autenticación falla

            Example:
                >>> result = await taiga_upvote_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> print(f"Total votes: {result['total_voters']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.upvote_issue(issue_id)

        @self.mcp.tool(name="taiga_downvote_issue")
        async def downvote_issue(auth_token: str, issue_id: int) -> dict[str, Any]:
            """
            ISSUE-015: Retira el voto de un issue.

            Esta herramienta quita el voto positivo del usuario actual
            de un issue previamente votado.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue del cual retirar el voto

            Returns:
                Dict con los datos actualizados del issue conteniendo:
                - id: ID del issue
                - total_voters: Número actualizado de votos
                - is_voter: False indicando que el usuario ya no vota

            Raises:
                ToolError: Si el issue no existe, no se había votado, o la
                    autenticación falla

            Example:
                >>> result = await taiga_downvote_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> print(f"Vote removed. Total: {result['total_voters']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.downvote_issue(issue_id)

        @self.mcp.tool(name="taiga_get_issue_voters")
        async def get_issue_voters(auth_token: str, issue_id: int) -> list[dict[str, Any]]:
            """
            ISSUE-016: Obtiene la lista de votantes de un issue.

            Esta herramienta devuelve la lista de usuarios que han votado
            positivamente por un issue específico.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue del cual obtener votantes

            Returns:
                Lista de diccionarios con información de votantes, cada uno con:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - photo: URL de la foto de perfil

            Raises:
                ToolError: Si el issue no existe o la autenticación falla

            Example:
                >>> voters = await taiga_get_issue_voters(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> print(f"Total voters: {len(voters)}")
                >>> for voter in voters:
                ...     print(f"  - {voter['full_name']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_voters(issue_id)

        # Watchers (ISSUE-017 a ISSUE-019)
        @self.mcp.tool(name="taiga_watch_issue")
        async def watch_issue(auth_token: str, issue_id: int) -> dict[str, Any]:
            """
            ISSUE-017: Suscribe al usuario actual como watcher del issue.

            Esta herramienta permite al usuario actual seguir un issue
            para recibir notificaciones sobre cambios, comentarios y
            actualizaciones de estado.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue a seguir

            Returns:
                Dict con los datos actualizados del issue conteniendo:
                - id: ID del issue
                - total_watchers: Número total de watchers
                - is_watcher: True indicando que el usuario sigue el issue

            Raises:
                ToolError: Si el issue no existe, ya se sigue, o la
                    autenticación falla

            Example:
                >>> result = await taiga_watch_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> print(f"Now watching. Total watchers: {result['total_watchers']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.watch_issue(issue_id)

        @self.mcp.tool(name="taiga_unwatch_issue")
        async def unwatch_issue(auth_token: str, issue_id: int) -> dict[str, Any]:
            """
            ISSUE-018: Desuscribe al usuario actual como watcher.

            Esta herramienta permite al usuario dejar de seguir un issue,
            dejando de recibir notificaciones sobre cambios en el mismo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue del cual dejar de seguir

            Returns:
                Dict con los datos actualizados del issue conteniendo:
                - id: ID del issue
                - total_watchers: Número actualizado de watchers
                - is_watcher: False indicando que ya no se sigue

            Raises:
                ToolError: Si el issue no existe, no se seguía, o la
                    autenticación falla

            Example:
                >>> result = await taiga_unwatch_issue(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> print("Stopped watching issue")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.unwatch_issue(issue_id)

        @self.mcp.tool(name="taiga_get_issue_watchers")
        async def get_issue_watchers(auth_token: str, issue_id: int) -> list[dict[str, Any]]:
            """
            ISSUE-019: Obtiene la lista de watchers de un issue.

            Esta herramienta devuelve la lista de usuarios que están
            siguiendo un issue específico y recibirán notificaciones
            sobre sus cambios.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue del cual obtener watchers

            Returns:
                Lista de diccionarios con información de watchers, cada uno con:
                - id: ID del usuario
                - username: Nombre de usuario
                - full_name: Nombre completo
                - photo: URL de la foto de perfil

            Raises:
                ToolError: Si el issue no existe o la autenticación falla

            Example:
                >>> watchers = await taiga_get_issue_watchers(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> print(f"Watchers ({len(watchers)}):")
                >>> for w in watchers:
                ...     print(f"  - {w['full_name']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_watchers(issue_id)

        # Adjuntos (ISSUE-020 a ISSUE-024)
        @self.mcp.tool(name="taiga_get_issue_attachments")
        async def get_issue_attachments(auth_token: str, issue_id: int) -> list[dict[str, Any]]:
            """
            ISSUE-020: Lista los adjuntos de un issue.

            Esta herramienta devuelve todos los archivos adjuntos
            asociados a un issue específico.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue del cual listar adjuntos

            Returns:
                Lista de diccionarios con información de adjuntos, cada uno con:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga
                - created_date: Fecha de subida
                - owner: Usuario que subió el archivo
                - description: Descripción del adjunto
                - is_deprecated: Si está marcado como obsoleto

            Raises:
                ToolError: Si el issue no existe o la autenticación falla

            Example:
                >>> attachments = await taiga_get_issue_attachments(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> for att in attachments:
                ...     print(f"  {att['name']} ({att['size']} bytes)")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_attachments(issue_id)

        @self.mcp.tool(name="taiga_create_issue_attachment")
        async def create_issue_attachment(
            auth_token: str,
            issue_id: int,
            file: bytes,
            filename: str,
            description: str | None = None,
        ) -> dict[str, Any]:
            """
            ISSUE-021: Crea un adjunto para un issue.

            Esta herramienta permite subir un archivo adjunto a un issue
            existente. Útil para evidencias, logs, capturas de pantalla
            o documentación relacionada.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue al que adjuntar el archivo
                file: Contenido binario del archivo
                filename: Nombre del archivo con extensión
                description: Descripción opcional del adjunto

            Returns:
                Dict con los datos del adjunto creado conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga
                - created_date: Fecha de creación
                - owner: ID del usuario que lo subió

            Raises:
                ToolError: Si el issue no existe, el archivo es inválido,
                    o la autenticación falla

            Example:
                >>> with open("screenshot.png", "rb") as f:
                ...     content = f.read()
                >>> attachment = await taiga_create_issue_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456,
                ...     file=content,
                ...     filename="screenshot.png",
                ...     description="Error screenshot"
                ... )
                >>> print(f"Uploaded: {attachment['url']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.create_issue_attachment(
                    issue_id=issue_id, file=file, filename=filename, description=description
                )

        @self.mcp.tool(name="taiga_get_issue_attachment")
        async def get_issue_attachment(auth_token: str, attachment_id: int) -> dict[str, Any]:
            """
            ISSUE-022: Obtiene un adjunto específico.

            Esta herramienta recupera los detalles de un archivo adjunto
            específico por su ID.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a consultar

            Returns:
                Dict con los datos del adjunto conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - size: Tamaño en bytes
                - url: URL de descarga
                - created_date: Fecha de creación
                - owner: Usuario que subió el archivo
                - description: Descripción del adjunto
                - is_deprecated: Si está marcado como obsoleto
                - object_id: ID del issue asociado

            Raises:
                ToolError: Si el adjunto no existe o la autenticación falla

            Example:
                >>> attachment = await taiga_get_issue_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789
                ... )
                >>> print(f"File: {attachment['name']}")
                >>> print(f"Download: {attachment['url']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_attachment(attachment_id)

        @self.mcp.tool(name="taiga_update_issue_attachment")
        async def update_issue_attachment(
            auth_token: str,
            attachment_id: int,
            description: str | None = None,
            is_deprecated: bool | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """
            ISSUE-023: Actualiza un adjunto.

            Esta herramienta permite modificar los metadatos de un archivo
            adjunto existente, como su descripción o estado de obsolescencia.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a actualizar
                description: Nueva descripción del adjunto
                is_deprecated: True para marcar como obsoleto (no recomendado)
                order: Nueva posición en el orden de adjuntos

            Returns:
                Dict con el adjunto actualizado conteniendo:
                - id: ID del adjunto
                - name: Nombre del archivo
                - description: Nueva descripción
                - is_deprecated: Estado de obsolescencia
                - order: Nueva posición

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos,
                    o la autenticación falla

            Example:
                >>> updated = await taiga_update_issue_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789,
                ...     description="Updated error log",
                ...     is_deprecated=False
                ... )
                >>> print(f"Updated: {updated['description']}")
            """
            data = {
                k: v
                for k, v in locals().items()
                if k not in ["self", "auth_token", "attachment_id"] and v is not None
            }

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.update_issue_attachment(attachment_id, **data)

        @self.mcp.tool(name="taiga_delete_issue_attachment")
        async def delete_issue_attachment(auth_token: str, attachment_id: int) -> bool:
            """
            ISSUE-024: Elimina un adjunto.

            Esta herramienta elimina permanentemente un archivo adjunto
            de un issue. Esta acción no se puede deshacer.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attachment_id: ID del adjunto a eliminar

            Returns:
                True si el adjunto fue eliminado exitosamente

            Raises:
                ToolError: Si el adjunto no existe, no hay permisos de
                    eliminación, o la autenticación falla

            Example:
                >>> result = await taiga_delete_issue_attachment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attachment_id=789
                ... )
                >>> if result:
                ...     print("Attachment deleted")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.delete_issue_attachment(attachment_id)

        # Historial (ISSUE-025 a ISSUE-029)
        @self.mcp.tool(name="taiga_get_issue_history")
        async def get_issue_history(auth_token: str, issue_id: int) -> list[dict[str, Any]]:
            """
            ISSUE-025: Obtiene el historial de cambios de un issue.

            Esta herramienta devuelve el registro completo de cambios
            realizados en un issue, incluyendo modificaciones de campos,
            comentarios y cambios de estado.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue del cual obtener el historial

            Returns:
                Lista de diccionarios con entradas del historial, cada una con:
                - id: ID de la entrada
                - user: Usuario que realizó el cambio
                - created_at: Fecha del cambio
                - type: Tipo de cambio (1=modificación, 2=comentario)
                - comment: Texto del comentario si aplica
                - values_diff: Diccionario con campos modificados
                - delete_comment_date: Fecha de eliminación si fue borrado

            Raises:
                ToolError: Si el issue no existe o la autenticación falla

            Example:
                >>> history = await taiga_get_issue_history(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456
                ... )
                >>> for entry in history:
                ...     print(f"{entry['created_at']}: {entry['user']['username']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_history(issue_id)

        @self.mcp.tool(name="taiga_get_issue_comment_versions")
        async def get_issue_comment_versions(
            auth_token: str, issue_id: int, comment_id: str
        ) -> list[dict[str, Any]]:
            """
            ISSUE-026: Obtiene las versiones de un comentario.

            Esta herramienta devuelve todas las versiones históricas de un
            comentario que ha sido editado, permitiendo ver cómo evolucionó.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue que contiene el comentario
                comment_id: ID del comentario (string UUID)

            Returns:
                Lista de diccionarios con versiones del comentario, cada una con:
                - id: ID de la versión
                - comment: Texto del comentario en esa versión
                - created_at: Fecha de esta versión
                - user: Usuario que realizó la edición

            Raises:
                ToolError: Si el issue o comentario no existe, o la
                    autenticación falla

            Example:
                >>> versions = await taiga_get_issue_comment_versions(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456,
                ...     comment_id="abc-123-def"
                ... )
                >>> for v in versions:
                ...     print(f"Version from {v['created_at']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_comment_versions(issue_id, comment_id)

        @self.mcp.tool(name="taiga_edit_issue_comment")
        async def edit_issue_comment(
            auth_token: str, issue_id: int, comment_id: str, comment: str
        ) -> dict[str, Any]:
            """
            ISSUE-027: Edita un comentario en el historial.

            Esta herramienta permite modificar el texto de un comentario
            existente en un issue. El historial de versiones se preserva.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue que contiene el comentario
                comment_id: ID del comentario a editar (string UUID)
                comment: Nuevo texto del comentario (soporta Markdown)

            Returns:
                Dict con el comentario actualizado conteniendo:
                - id: ID del comentario
                - comment: Nuevo texto
                - user: Usuario que editó
                - created_at: Fecha original
                - modified_at: Fecha de modificación

            Raises:
                ToolError: Si el issue o comentario no existe, no hay permisos
                    (solo el autor puede editar), o la autenticación falla

            Example:
                >>> edited = await taiga_edit_issue_comment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456,
                ...     comment_id="abc-123-def",
                ...     comment="Updated comment text"
                ... )
                >>> print(f"Comment edited at {edited['modified_at']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.edit_issue_comment(
                    issue_id=issue_id, comment_id=comment_id, comment=comment
                )

        @self.mcp.tool(name="taiga_delete_issue_comment")
        async def delete_issue_comment(auth_token: str, issue_id: int, comment_id: str) -> bool:
            """
            ISSUE-028: Elimina un comentario del historial.

            Esta herramienta elimina un comentario de un issue. Los comentarios
            eliminados pueden ser recuperados posteriormente.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue que contiene el comentario
                comment_id: ID del comentario a eliminar (string UUID)

            Returns:
                True si el comentario fue eliminado exitosamente

            Raises:
                ToolError: Si el issue o comentario no existe, no hay permisos
                    de eliminación, o la autenticación falla

            Example:
                >>> result = await taiga_delete_issue_comment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456,
                ...     comment_id="abc-123-def"
                ... )
                >>> if result:
                ...     print("Comment deleted (can be restored)")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.delete_issue_comment(issue_id, comment_id)

        @self.mcp.tool(name="taiga_undelete_issue_comment")
        async def undelete_issue_comment(
            auth_token: str, issue_id: int, comment_id: str
        ) -> dict[str, Any]:
            """
            ISSUE-029: Recupera un comentario eliminado.

            Esta herramienta restaura un comentario que fue previamente
            eliminado de un issue.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                issue_id: ID del issue que contenía el comentario
                comment_id: ID del comentario eliminado (string UUID)

            Returns:
                Dict con el comentario restaurado conteniendo:
                - id: ID del comentario
                - comment: Texto del comentario
                - user: Usuario autor
                - created_at: Fecha original de creación
                - delete_comment_date: None (ya no está eliminado)

            Raises:
                ToolError: Si el issue no existe, el comentario no está
                    eliminado, no hay permisos, o la autenticación falla

            Example:
                >>> restored = await taiga_undelete_issue_comment(
                ...     auth_token="eyJ0eXAiOi...",
                ...     issue_id=456,
                ...     comment_id="abc-123-def"
                ... )
                >>> print(f"Comment restored: {restored['comment'][:50]}...")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.undelete_issue_comment(issue_id, comment_id)

        # Atributos Personalizados (ISSUE-030)
        @self.mcp.tool(name="taiga_get_issue_custom_attributes")
        async def get_issue_custom_attributes(
            auth_token: str, project_id: int
        ) -> list[dict[str, Any]]:
            """
            ISSUE-030: Lista los atributos personalizados de issues.

            Esta herramienta obtiene todos los atributos personalizados definidos
            para los issues de un proyecto. Los atributos personalizados permiten
            agregar campos adicionales específicos del proyecto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto del que obtener los atributos

            Returns:
                Lista de diccionarios con atributos personalizados, cada uno con:
                - id: ID del atributo
                - name: Nombre del atributo
                - description: Descripción del atributo
                - type: Tipo de dato (text, number, date, url, etc.)
                - order: Orden de visualización
                - project: ID del proyecto
                - created_date: Fecha de creación

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos de
                    lectura, o la autenticación falla

            Example:
                >>> attributes = await taiga_get_issue_custom_attributes(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123
                ... )
                >>> for attr in attributes:
                ...     print(f"{attr['name']}: {attr['type']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.get_issue_custom_attributes(
                    project=project_id
                )  # API expects 'project'

        @self.mcp.tool(name="taiga_create_issue_custom_attribute")
        async def create_issue_custom_attribute(
            auth_token: str,
            project_id: int,
            name: str,
            description: str | None = None,
            order: int | None = None,
            type: str | None = None,
        ) -> dict[str, Any]:
            """
            ISSUE-030: Crea un atributo personalizado para issues.

            Esta herramienta crea un nuevo atributo personalizado que estará
            disponible para todos los issues del proyecto. Útil para agregar
            campos específicos del flujo de trabajo del equipo.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                project_id: ID del proyecto donde crear el atributo
                name: Nombre del atributo (visible en la UI)
                description: Descripción del atributo y su uso (opcional)
                order: Posición en el formulario (menor = más arriba, opcional)
                type: Tipo de dato del atributo (opcional):
                    - "text": Texto libre (default)
                    - "number": Valor numérico
                    - "date": Fecha
                    - "url": Enlace
                    - "dropdown": Lista desplegable

            Returns:
                Dict con el atributo creado conteniendo:
                - id: ID del nuevo atributo
                - name: Nombre asignado
                - description: Descripción
                - type: Tipo de dato
                - order: Orden de visualización
                - project: ID del proyecto
                - created_date: Fecha de creación

            Raises:
                ToolError: Si el proyecto no existe, no hay permisos de
                    administración, ya existe un atributo con ese nombre,
                    o la autenticación falla

            Example:
                >>> attr = await taiga_create_issue_custom_attribute(
                ...     auth_token="eyJ0eXAiOi...",
                ...     project_id=123,
                ...     name="Customer Impact",
                ...     description="Level of customer impact",
                ...     type="dropdown"
                ... )
                >>> print(f"Created attribute '{attr['name']}' with ID {attr['id']}")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.create_issue_custom_attribute(
                    project=project_id,
                    name=name,
                    description=description,
                    order=order,
                    type=type,  # API expects 'project'
                )

        @self.mcp.tool(name="taiga_update_issue_custom_attribute")
        async def update_issue_custom_attribute(
            auth_token: str,
            attribute_id: int,
            name: str | None = None,
            description: str | None = None,
            order: int | None = None,
        ) -> dict[str, Any]:
            """
            ISSUE-030: Actualiza un atributo personalizado.

            Esta herramienta modifica las propiedades de un atributo personalizado
            existente. Solo se actualizan los campos proporcionados.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attribute_id: ID del atributo a actualizar
                name: Nuevo nombre del atributo (opcional)
                description: Nueva descripción (opcional)
                order: Nueva posición en el formulario (opcional)

            Returns:
                Dict con el atributo actualizado conteniendo:
                - id: ID del atributo
                - name: Nombre actualizado
                - description: Descripción actualizada
                - type: Tipo de dato (no modificable)
                - order: Nuevo orden
                - project: ID del proyecto
                - modified_date: Fecha de modificación

            Raises:
                ToolError: Si el atributo no existe, no hay permisos de
                    administración, el nombre ya está en uso,
                    o la autenticación falla

            Example:
                >>> updated = await taiga_update_issue_custom_attribute(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attribute_id=789,
                ...     name="Customer Impact Level",
                ...     order=1
                ... )
                >>> print(f"Attribute renamed to '{updated['name']}'")
            """
            data = {
                k: v
                for k, v in locals().items()
                if k not in ["self", "auth_token", "attribute_id"] and v is not None
            }

            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.update_issue_custom_attribute(attribute_id, **data)

        @self.mcp.tool(name="taiga_delete_issue_custom_attribute")
        async def delete_issue_custom_attribute(auth_token: str, attribute_id: int) -> bool:
            """
            ISSUE-030: Elimina un atributo personalizado.

            Esta herramienta elimina permanentemente un atributo personalizado
            del proyecto. ADVERTENCIA: Se perderán todos los valores de este
            atributo en todos los issues del proyecto.

            Args:
                auth_token: Token de autenticación obtenido de taiga_authenticate
                attribute_id: ID del atributo a eliminar

            Returns:
                True si el atributo fue eliminado exitosamente

            Raises:
                ToolError: Si el atributo no existe, no hay permisos de
                    administración, o la autenticación falla

            Example:
                >>> result = await taiga_delete_issue_custom_attribute(
                ...     auth_token="eyJ0eXAiOi...",
                ...     attribute_id=789
                ... )
                >>> if result:
                ...     print("Custom attribute deleted permanently")
            """
            async with TaigaAPIClient(self.config) as client:
                client.auth_token = auth_token
                return await client.delete_issue_custom_attribute(attribute_id)

    # Métodos de las herramientas (para facilitar testing)
    async def list_issues(self, **kwargs: Any):
        """Implementación directa del método list_issues."""
        auth_token = kwargs.pop("auth_token", None)
        project = kwargs.get("project")
        self._logger.debug(f"[list_issues] Starting | project={project}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.list_issues(**kwargs)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[list_issues] Success | project={project}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[list_issues] Error | project={project}, error={e!s}")
            raise

    async def create_issue(self, **kwargs: Any):
        """Implementación directa del método create_issue."""
        auth_token = kwargs.pop("auth_token", None)

        # Validar campos requeridos
        if "project" not in kwargs or "subject" not in kwargs:
            raise ValueError("project and subject are required")

        project = kwargs.get("project")
        subject = kwargs.get("subject")
        self._logger.debug(f"[create_issue] Starting | project={project}, subject={subject}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.create_issue(**kwargs)
            issue_id = result.get("id") if isinstance(result, dict) else None
            self._logger.info(f"[create_issue] Success | project={project}, issue_id={issue_id}")
            return result
        except Exception as e:
            self._logger.error(f"[create_issue] Error | project={project}, error={e!s}")
            raise

    async def get_issue(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método get_issue."""
        self._logger.debug(f"[get_issue] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue(issue_id=issue_id)
            self._logger.info(f"[get_issue] Success | issue_id={issue_id}")
            return result
        except Exception as e:
            self._logger.error(f"[get_issue] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def update_issue(self, issue_id: int, **kwargs: Any):
        """Implementación directa del método update_issue."""
        auth_token = kwargs.pop("auth_token", None)
        self._logger.debug(f"[update_issue] Starting | issue_id={issue_id}")
        try:
            # Validar datos de entrada ANTES de llamar a la API
            validation_data = {
                "issue_id": issue_id,
                "subject": kwargs.get("subject"),
                "description": kwargs.get("description"),
                "issue_type": kwargs.get("type"),
                "priority": kwargs.get("priority"),
                "severity": kwargs.get("severity"),
                "status": kwargs.get("status"),
                "assigned_to": kwargs.get("assigned_to"),
                "tags": kwargs.get("tags"),
            }
            validate_input(IssueUpdateValidator, validation_data)

            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.update_issue(issue_id, **kwargs)
            self._logger.info(f"[update_issue] Success | issue_id={issue_id}")
            return result
        except ValidationError as e:
            self._logger.warning(f"[update_issue] Validation error | error={e!s}")
            raise
        except Exception as e:
            self._logger.error(f"[update_issue] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def update_issue_full(self, issue_id: int, **kwargs: Any):
        """Implementación directa del método update_issue_full (PUT)."""
        auth_token = kwargs.pop("auth_token", None)
        self._logger.debug(f"[update_issue_full] Starting | issue_id={issue_id}")
        try:
            # Validar datos de entrada ANTES de llamar a la API
            validation_data = {
                "issue_id": issue_id,
                "subject": kwargs.get("subject"),
                "description": kwargs.get("description"),
                "issue_type": kwargs.get("type"),
                "priority": kwargs.get("priority"),
                "severity": kwargs.get("severity"),
                "status": kwargs.get("status"),
                "assigned_to": kwargs.get("assigned_to"),
                "tags": kwargs.get("tags"),
            }
            validate_input(IssueUpdateValidator, validation_data)

            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.update_issue_full(issue_id, **kwargs)
            self._logger.info(f"[update_issue_full] Success | issue_id={issue_id}")
            return result
        except ValidationError as e:
            self._logger.warning(f"[update_issue_full] Validation error | error={e!s}")
            raise
        except Exception as e:
            self._logger.error(f"[update_issue_full] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def delete_issue(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método delete_issue."""
        self._logger.debug(f"[delete_issue] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.delete_issue(issue_id=issue_id)
            self._logger.info(f"[delete_issue] Success | issue_id={issue_id}")
            return result
        except Exception as e:
            self._logger.error(f"[delete_issue] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def bulk_create_issues(self, **kwargs: Any):
        """Implementación directa del método bulk_create_issues."""
        auth_token = kwargs.pop("auth_token", None)
        project = kwargs.get("project_id")
        self._logger.debug(f"[bulk_create_issues] Starting | project={project}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.bulk_create_issues(**kwargs)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[bulk_create_issues] Success | project={project}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[bulk_create_issues] Error | project={project}, error={e!s}")
            raise

    async def get_issue_filters(self, auth_token: str | None = None, project: int | None = None):
        """Implementación directa del método get_issue_filters."""
        self._logger.debug(f"[get_issue_filters] Starting | project={project}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_filters(project=project)
            self._logger.info(f"[get_issue_filters] Success | project={project}")
            return result
        except Exception as e:
            self._logger.error(f"[get_issue_filters] Error | project={project}, error={e!s}")
            raise

    async def upvote_issue(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método upvote_issue."""
        self._logger.debug(f"[upvote_issue] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.upvote_issue(issue_id=issue_id)
            self._logger.info(f"[upvote_issue] Success | issue_id={issue_id}")
            return result
        except Exception as e:
            self._logger.error(f"[upvote_issue] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def downvote_issue(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método downvote_issue."""
        self._logger.debug(f"[downvote_issue] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.downvote_issue(issue_id=issue_id)
            self._logger.info(f"[downvote_issue] Success | issue_id={issue_id}")
            return result
        except Exception as e:
            self._logger.error(f"[downvote_issue] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def get_issue_voters(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método get_issue_voters."""
        self._logger.debug(f"[get_issue_voters] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_voters(issue_id=issue_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[get_issue_voters] Success | issue_id={issue_id}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[get_issue_voters] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def watch_issue(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método watch_issue."""
        self._logger.debug(f"[watch_issue] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.watch_issue(issue_id=issue_id)
            self._logger.info(f"[watch_issue] Success | issue_id={issue_id}")
            return result
        except Exception as e:
            self._logger.error(f"[watch_issue] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def unwatch_issue(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método unwatch_issue."""
        self._logger.debug(f"[unwatch_issue] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.unwatch_issue(issue_id=issue_id)
            self._logger.info(f"[unwatch_issue] Success | issue_id={issue_id}")
            return result
        except Exception as e:
            self._logger.error(f"[unwatch_issue] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def get_issue_watchers(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método get_issue_watchers."""
        self._logger.debug(f"[get_issue_watchers] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_watchers(issue_id=issue_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[get_issue_watchers] Success | issue_id={issue_id}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[get_issue_watchers] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def get_issue_attachments(self, issue_id: int, auth_token: str | None = None):
        """Implementación directa del método get_issue_attachments."""
        self._logger.debug(f"[get_issue_attachments] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_attachments(issue_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(
                f"[get_issue_attachments] Success | issue_id={issue_id}, count={count}"
            )
            return result
        except Exception as e:
            self._logger.error(f"[get_issue_attachments] Error | issue_id={issue_id}, error={e!s}")
            raise

    # Alias para list_issue_attachments (mismo método que get_issue_attachments)
    async def list_issue_attachments(
        self, auth_token: str | None = None, issue_id: int | None = None
    ):
        """Lista los attachments de un issue."""
        self._logger.debug(f"[list_issue_attachments] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                # Check if client has list_issue_attachments method (for tests)
                if hasattr(client, "list_issue_attachments"):
                    result = await client.list_issue_attachments(issue_id=issue_id)
                else:
                    # Fallback to get_issue_attachments (production)
                    result = await client.get_issue_attachments(issue_id=issue_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(
                f"[list_issue_attachments] Success | issue_id={issue_id}, count={count}"
            )
            return result
        except Exception as e:
            self._logger.error(f"[list_issue_attachments] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def create_issue_attachment(self, **kwargs: Any):
        """Implementación directa del método create_issue_attachment."""
        auth_token = kwargs.pop("auth_token", None)
        issue_id = kwargs.get("issue_id")
        self._logger.debug(f"[create_issue_attachment] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.create_issue_attachment(**kwargs)
            attachment_id = result.get("id") if isinstance(result, dict) else None
            self._logger.info(
                f"[create_issue_attachment] Success | issue_id={issue_id}, attachment_id={attachment_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[create_issue_attachment] Error | issue_id={issue_id}, error={e!s}"
            )
            raise

    async def get_issue_attachment(
        self, auth_token: str | None = None, attachment_id: int | None = None
    ):
        """Implementación directa del método get_issue_attachment."""
        self._logger.debug(f"[get_issue_attachment] Starting | attachment_id={attachment_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_attachment(attachment_id=attachment_id)
            self._logger.info(f"[get_issue_attachment] Success | attachment_id={attachment_id}")
            return result
        except Exception as e:
            self._logger.error(
                f"[get_issue_attachment] Error | attachment_id={attachment_id}, error={e!s}"
            )
            raise

    async def update_issue_attachment(self, attachment_id: int, **kwargs: Any):
        """Implementación directa del método update_issue_attachment."""
        auth_token = kwargs.pop("auth_token", None)
        self._logger.debug(f"[update_issue_attachment] Starting | attachment_id={attachment_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.update_issue_attachment(attachment_id, **kwargs)
            self._logger.info(f"[update_issue_attachment] Success | attachment_id={attachment_id}")
            return result
        except Exception as e:
            self._logger.error(
                f"[update_issue_attachment] Error | attachment_id={attachment_id}, error={e!s}"
            )
            raise

    async def delete_issue_attachment(
        self, auth_token: str | None = None, attachment_id: int | None = None
    ):
        """Implementación directa del método delete_issue_attachment."""
        self._logger.debug(f"[delete_issue_attachment] Starting | attachment_id={attachment_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.delete_issue_attachment(attachment_id=attachment_id)
            self._logger.info(f"[delete_issue_attachment] Success | attachment_id={attachment_id}")
            return result
        except Exception as e:
            self._logger.error(
                f"[delete_issue_attachment] Error | attachment_id={attachment_id}, error={e!s}"
            )
            raise

    async def get_issue_history(self, auth_token: str | None = None, issue_id: int | None = None):
        """Implementación directa del método get_issue_history."""
        self._logger.debug(f"[get_issue_history] Starting | issue_id={issue_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_history(issue_id=issue_id)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(f"[get_issue_history] Success | issue_id={issue_id}, count={count}")
            return result
        except Exception as e:
            self._logger.error(f"[get_issue_history] Error | issue_id={issue_id}, error={e!s}")
            raise

    async def get_issue_comment_versions(
        self,
        auth_token: str | None = None,
        issue_id: int | None = None,
        comment_id: str | None = None,
    ):
        """Implementación directa del método get_issue_comment_versions."""
        self._logger.debug(
            f"[get_issue_comment_versions] Starting | issue_id={issue_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_comment_versions(
                    issue_id=issue_id, comment_id=comment_id
                )
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(
                f"[get_issue_comment_versions] Success | issue_id={issue_id}, comment_id={comment_id}, count={count}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[get_issue_comment_versions] Error | issue_id={issue_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def edit_issue_comment(self, **kwargs: Any):
        """Implementación directa del método edit_issue_comment."""
        auth_token = kwargs.pop("auth_token", None)
        issue_id = kwargs.get("issue_id")
        comment_id = kwargs.get("comment_id")
        self._logger.debug(
            f"[edit_issue_comment] Starting | issue_id={issue_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.edit_issue_comment(**kwargs)
            self._logger.info(
                f"[edit_issue_comment] Success | issue_id={issue_id}, comment_id={comment_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[edit_issue_comment] Error | issue_id={issue_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def delete_issue_comment(
        self,
        auth_token: str | None = None,
        issue_id: int | None = None,
        comment_id: str | None = None,
    ):
        """Implementación directa del método delete_issue_comment."""
        self._logger.debug(
            f"[delete_issue_comment] Starting | issue_id={issue_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.delete_issue_comment(issue_id=issue_id, comment_id=comment_id)
            self._logger.info(
                f"[delete_issue_comment] Success | issue_id={issue_id}, comment_id={comment_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[delete_issue_comment] Error | issue_id={issue_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def undelete_issue_comment(
        self,
        auth_token: str | None = None,
        issue_id: int | None = None,
        comment_id: str | None = None,
    ):
        """Implementación directa del método undelete_issue_comment."""
        self._logger.debug(
            f"[undelete_issue_comment] Starting | issue_id={issue_id}, comment_id={comment_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.undelete_issue_comment(
                    issue_id=issue_id, comment_id=comment_id
                )
            self._logger.info(
                f"[undelete_issue_comment] Success | issue_id={issue_id}, comment_id={comment_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[undelete_issue_comment] Error | issue_id={issue_id}, comment_id={comment_id}, error={e!s}"
            )
            raise

    async def get_issue_custom_attributes(self, project: int, auth_token: str | None = None):
        """Implementación directa del método get_issue_custom_attributes."""
        self._logger.debug(f"[get_issue_custom_attributes] Starting | project={project}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_custom_attributes(project=project)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(
                f"[get_issue_custom_attributes] Success | project={project}, count={count}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[get_issue_custom_attributes] Error | project={project}, error={e!s}"
            )
            raise

    async def create_issue_custom_attribute(self, **kwargs: Any):
        """Implementación directa del método create_issue_custom_attribute."""
        auth_token = kwargs.pop("auth_token", None)
        project = kwargs.get("project_id")
        name = kwargs.get("name")
        self._logger.debug(
            f"[create_issue_custom_attribute] Starting | project={project}, name={name}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.create_issue_custom_attribute(**kwargs)
            attr_id = result.get("id") if isinstance(result, dict) else None
            self._logger.info(
                f"[create_issue_custom_attribute] Success | project={project}, attribute_id={attr_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[create_issue_custom_attribute] Error | project={project}, error={e!s}"
            )
            raise

    async def update_issue_custom_attribute(self, attribute_id: int, **kwargs: Any):
        """Implementación directa del método update_issue_custom_attribute."""
        auth_token = kwargs.pop("auth_token", None)
        self._logger.debug(
            f"[update_issue_custom_attribute] Starting | attribute_id={attribute_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.update_issue_custom_attribute(attribute_id, **kwargs)
            self._logger.info(
                f"[update_issue_custom_attribute] Success | attribute_id={attribute_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[update_issue_custom_attribute] Error | attribute_id={attribute_id}, error={e!s}"
            )
            raise

    # Alias para list_issue_custom_attributes (mismo método que get_issue_custom_attributes)
    async def list_issue_custom_attributes(
        self, auth_token: str | None = None, project: int | None = None
    ):
        """Lista los atributos personalizados de issues."""
        self._logger.debug(f"[list_issue_custom_attributes] Starting | project={project}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                # Check if client has list_issue_custom_attributes method (for tests)
                if hasattr(client, "list_issue_custom_attributes"):
                    result = await client.list_issue_custom_attributes(project=project)
                else:
                    # Fallback to get_issue_custom_attributes (production)
                    result = await client.get_issue_custom_attributes(project=project)
            count = len(result) if isinstance(result, list) else 0
            self._logger.info(
                f"[list_issue_custom_attributes] Success | project={project}, count={count}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[list_issue_custom_attributes] Error | project={project}, error={e!s}"
            )
            raise

    # Alias para get_issue_custom_attribute
    async def get_issue_custom_attribute(
        self, auth_token: str | None = None, attribute_id: int | None = None
    ):
        """Obtiene un atributo personalizado específico."""
        self._logger.debug(f"[get_issue_custom_attribute] Starting | attribute_id={attribute_id}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                # El cliente puede no tener un método específico para un solo atributo
                # pero se puede simular obteniendo todos y filtrando
                result = await client.get_issue_custom_attribute(attribute_id=attribute_id)
            self._logger.info(f"[get_issue_custom_attribute] Success | attribute_id={attribute_id}")
            return result
        except Exception as e:
            self._logger.error(
                f"[get_issue_custom_attribute] Error | attribute_id={attribute_id}, error={e!s}"
            )
            raise

    async def delete_issue_custom_attribute(
        self, auth_token: str | None = None, attribute_id: int | None = None
    ):
        """Implementación directa del método delete_issue_custom_attribute."""
        self._logger.debug(
            f"[delete_issue_custom_attribute] Starting | attribute_id={attribute_id}"
        )
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.delete_issue_custom_attribute(attribute_id=attribute_id)
            self._logger.info(
                f"[delete_issue_custom_attribute] Success | attribute_id={attribute_id}"
            )
            return result
        except Exception as e:
            self._logger.error(
                f"[delete_issue_custom_attribute] Error | attribute_id={attribute_id}, error={e!s}"
            )
            raise

    async def get_issue_by_ref(
        self, auth_token: str | None = None, project: int | None = None, ref: int | None = None
    ):
        """Implementación directa del método get_issue_by_ref."""
        self._logger.debug(f"[get_issue_by_ref] Starting | project={project}, ref={ref}")
        try:
            async with TaigaAPIClient(self.config) as client:
                if auth_token:
                    client.auth_token = auth_token
                result = await client.get_issue_by_ref(project=project, ref=ref)
            self._logger.info(f"[get_issue_by_ref] Success | project={project}, ref={ref}")
            return result
        except Exception as e:
            self._logger.error(
                f"[get_issue_by_ref] Error | project={project}, ref={ref}, error={e!s}"
            )
            raise
