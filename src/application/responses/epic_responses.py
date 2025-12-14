"""Responses estructurados para operaciones de épicas en Taiga.

Este módulo define las clases de respuesta Pydantic para todas las
operaciones relacionadas con épicas en la API de Taiga.
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from src.application.responses.base import BaseResponse


class EpicStatusResponse(BaseResponse):
    """Información del estado de la épica.

    Attributes:
        id: ID del estado.
        name: Nombre del estado.
        slug: Slug del estado.
        color: Color del estado.
        is_closed: Si el estado representa cierre.
    """

    id: int | None = None
    name: str | None = None
    slug: str | None = None
    color: str | None = None
    is_closed: bool | None = None


class EpicAssignedToResponse(BaseResponse):
    """Información del usuario asignado a la épica.

    Attributes:
        id: ID del usuario.
        username: Nombre de usuario.
        full_name: Nombre completo.
        photo: URL de la foto.
    """

    id: int | None = None
    username: str | None = None
    full_name: str | None = Field(default=None, alias="full_name_display")
    photo: str | None = None


class EpicUserStoriesCountsResponse(BaseResponse):
    """Contadores de historias de usuario de la épica.

    Attributes:
        total: Total de historias.
        progress: Porcentaje de progreso.
    """

    total: int | None = None
    progress: float | None = None


class EpicResponse(BaseResponse):
    """Response para una épica individual de Taiga.

    Contiene toda la información de una épica incluyendo
    metadatos y relaciones.

    Attributes:
        id: ID único de la épica.
        ref: Número de referencia.
        subject: Título de la épica.
        description: Descripción detallada.
        project: ID del proyecto.
        status: Estado de la épica.
        status_extra_info: Información adicional del estado.
        color: Color de la épica.
        assigned_to: Usuario asignado.
        assigned_to_extra_info: Información del usuario asignado.
        tags: Lista de tags.
        watchers: Lista de IDs de watchers.
        user_stories_counts: Contador de historias.
        created_date: Fecha de creación.
        modified_date: Fecha de modificación.
        version: Versión para control de concurrencia.
        owner: ID del propietario.
        epics_order: Orden de la épica.
        client_requirement: Si es requerimiento de cliente.
        team_requirement: Si es requerimiento de equipo.
    """

    id: int
    ref: int | None = None
    subject: str
    description: str | None = None
    project: int | None = None
    status: int | None = None
    status_extra_info: EpicStatusResponse | dict[str, Any] | None = None
    color: str | None = None
    assigned_to: int | None = None
    assigned_to_extra_info: EpicAssignedToResponse | dict[str, Any] | None = None
    tags: list[str | list[str | None]] | None = None
    watchers: list[int] | None = None
    user_stories_counts: EpicUserStoriesCountsResponse | dict[str, Any] | None = None
    created_date: datetime | str | None = None
    modified_date: datetime | str | None = None
    version: int | None = None
    owner: int | None = None
    epics_order: int | None = None
    client_requirement: bool | None = None
    team_requirement: bool | None = None
    is_blocked: bool | None = None
    blocked_note: str | None = None
    total_voters: int | None = None
    total_watchers: int | None = None
    is_voter: bool | None = None
    is_watcher: bool | None = None


class EpicListResponse(BaseResponse):
    """Response para una lista de épicas.

    Attributes:
        epics: Lista de épicas.
        count: Número total de épicas.
    """

    epics: list[EpicResponse]
    count: int

    @classmethod
    def from_api_response(cls, epics_data: list[dict[str, Any]]) -> "EpicListResponse":
        """Crea una respuesta de lista desde datos de la API.

        Args:
            epics_data: Lista de diccionarios con datos de épicas.

        Returns:
            EpicListResponse con las épicas validadas.
        """
        epics = [EpicResponse.model_validate(epic) for epic in epics_data]
        return cls(epics=epics, count=len(epics))


class EpicRelatedUserstoryResponse(BaseResponse):
    """Response para una historia de usuario relacionada con una épica.

    Attributes:
        id: ID de la relación (puede no estar presente en algunas respuestas).
        user_story: ID de la historia de usuario o diccionario completo.
        epic: ID de la épica.
        order: Orden dentro de la épica.
    """

    id: int | None = None
    user_story: int | dict[str, Any]
    epic: int
    order: int | None = None


class EpicFiltersResponse(BaseResponse):
    """Response para filtros disponibles de épicas.

    Attributes:
        statuses: Lista de estados disponibles.
        assigned_to: Lista de usuarios para filtrar.
        owners: Lista de propietarios.
        tags: Lista de tags disponibles (strings o dicts).
    """

    statuses: list[dict[str, Any]] | None = None
    assigned_to: list[dict[str, Any]] | None = None
    owners: list[dict[str, Any]] | None = None
    tags: list[str | dict[str, Any]] | None = None


class EpicVoterResponse(BaseResponse):
    """Response para un votante de épica.

    Attributes:
        id: ID del usuario.
        username: Nombre de usuario.
        full_name: Nombre completo.
        photo: URL de la foto de perfil.
    """

    id: int
    username: str | None = None
    full_name: str | None = None
    photo: str | None = None


class EpicWatcherResponse(BaseResponse):
    """Response para un watcher de épica.

    Attributes:
        id: ID del usuario.
        username: Nombre de usuario.
        full_name: Nombre completo.
        photo: URL de la foto de perfil.
    """

    id: int
    username: str | None = None
    full_name: str | None = None
    photo: str | None = None


class EpicAttachmentResponse(BaseResponse):
    """Response para un adjunto de épica.

    Attributes:
        id: ID del adjunto.
        name: Nombre del archivo.
        size: Tamaño en bytes.
        url: URL de descarga.
        created_date: Fecha de creación.
        owner: ID del usuario que subió el archivo.
        description: Descripción del adjunto.
        is_deprecated: Si está marcado como obsoleto.
    """

    id: int
    name: str | None = None
    size: int | None = None
    url: str | None = None
    created_date: datetime | str | None = None
    modified_date: datetime | str | None = None
    owner: int | None = None
    description: str | None = None
    is_deprecated: bool | None = None
    attached_file: str | None = None
    project: int | None = None
    object_id: int | None = None
    order: int | None = None
    sha1: str | None = None
    from_comment: bool | None = None


class EpicCustomAttributeResponse(BaseResponse):
    """Response para un atributo personalizado de épica.

    Attributes:
        id: ID del atributo.
        name: Nombre del atributo.
        description: Descripción del atributo.
        type: Tipo de dato.
        order: Orden de visualización.
        project: ID del proyecto.
        created_date: Fecha de creación.
    """

    id: int
    name: str
    description: str | None = None
    type: str | None = None
    order: int | None = None
    project: int | None = None
    created_date: datetime | str | None = None
    modified_date: datetime | str | None = None


class EpicCustomAttributeValuesResponse(BaseResponse):
    """Response para valores de atributos personalizados de una épica.

    Attributes:
        epic: ID de la épica.
        version: Versión para control de concurrencia.
        attributes_values: Diccionario de valores de atributos.
    """

    epic: int | None = None
    version: int | None = None
    attributes_values: dict[str, Any] | None = None
