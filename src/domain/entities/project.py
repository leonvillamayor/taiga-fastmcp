"""Entidad de proyecto."""

from datetime import datetime

from pydantic import Field, field_validator

from src.domain.entities.base import BaseEntity
from src.domain.value_objects.project_slug import ProjectSlug


class Project(BaseEntity):
    """
    Entidad de proyecto en Taiga.

    Representa un proyecto con sus configuraciones y estado.
    Un proyecto es la unidad principal de organización en Taiga.

    Attributes:
        name: Nombre del proyecto
        slug: Slug único del proyecto (URL-friendly)
        description: Descripción del proyecto
        is_private: Indica si el proyecto es privado
        is_backlog_activated: Indica si el módulo backlog está activado
        is_kanban_activated: Indica si el módulo kanban está activado
        is_wiki_activated: Indica si el módulo wiki está activado
        is_issues_activated: Indica si el módulo issues está activado
        owner_id: ID del propietario del proyecto
        created_date: Fecha de creación
        modified_date: Última modificación
        total_story_points: Total de story points en el proyecto
        total_milestones: Total de milestones
        tags: Lista de tags del proyecto

    Examples:
        >>> project = Project(name="Mi Proyecto", slug=ProjectSlug(value="mi-proyecto"))
        >>> project.activate_module("wiki")
        >>> project.is_wiki_activated
        True
    """

    name: str = Field(..., min_length=1, max_length=255, description="Nombre del proyecto")
    slug: ProjectSlug | None = Field(None, description="Slug único del proyecto")
    description: str = Field("", description="Descripción del proyecto")

    # Configuración
    is_private: bool = Field(True, description="¿Es proyecto privado?")
    is_backlog_activated: bool = Field(True, description="¿Módulo backlog activado?")
    is_kanban_activated: bool = Field(True, description="¿Módulo kanban activado?")
    is_wiki_activated: bool = Field(True, description="¿Módulo wiki activado?")
    is_issues_activated: bool = Field(True, description="¿Módulo issues activado?")

    # Metadatos
    owner_id: int | None = Field(None, description="ID del propietario")
    created_date: datetime | None = Field(None, description="Fecha de creación")
    modified_date: datetime | None = Field(None, description="Última modificación")

    # Estadísticas
    total_story_points: float | None = Field(None, ge=0, description="Total de story points")
    total_milestones: int | None = Field(None, ge=0, description="Total de milestones")

    # Tags
    tags: list[str] = Field(default_factory=list, description="Tags del proyecto")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Valida que el nombre no esté vacío ni sea solo espacios.

        Args:
            v: Nombre a validar

        Returns:
            Nombre validado y normalizado (sin espacios extras)

        Raises:
            ValueError: Si el nombre está vacío o solo contiene espacios
        """
        if isinstance(v, str) and not v.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return v

    @field_validator("slug", mode="before")
    @classmethod
    def convert_slug(cls, v: object) -> ProjectSlug | None:
        """
        Convierte string a ProjectSlug automáticamente.

        Permite crear proyectos desde datos del API que envían slug como string.

        Args:
            v: Valor del slug (string, ProjectSlug o None)

        Returns:
            ProjectSlug o None
        """
        if v is None:
            return None
        if isinstance(v, ProjectSlug):
            return v
        if isinstance(v, str):
            return ProjectSlug(value=v)
        # If it's not a recognized type, return None and let pydantic handle it
        return None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """
        Normaliza tags (minúsculas, sin duplicados).

        Args:
            v: Lista de tags a normalizar

        Returns:
            Lista de tags normalizados (minúsculas, sin duplicados, sin espacios extras)
        """
        return list({tag.lower().strip() for tag in v if tag.strip()})

    def activate_module(self, module: str) -> None:
        """
        Activa un módulo del proyecto.

        Args:
            module: Nombre del módulo ('backlog', 'kanban', 'wiki', 'issues')

        Raises:
            ValueError: Si el módulo no es reconocido
        """
        module_map = {
            "backlog": "is_backlog_activated",
            "kanban": "is_kanban_activated",
            "wiki": "is_wiki_activated",
            "issues": "is_issues_activated",
        }
        if module not in module_map:
            raise ValueError(f"Módulo desconocido: {module}")
        setattr(self, module_map[module], True)

    def deactivate_module(self, module: str) -> None:
        """
        Desactiva un módulo del proyecto.

        Args:
            module: Nombre del módulo ('backlog', 'kanban', 'wiki', 'issues')

        Raises:
            ValueError: Si el módulo no es reconocido
        """
        module_map = {
            "backlog": "is_backlog_activated",
            "kanban": "is_kanban_activated",
            "wiki": "is_wiki_activated",
            "issues": "is_issues_activated",
        }
        if module not in module_map:
            raise ValueError(f"Módulo desconocido: {module}")
        setattr(self, module_map[module], False)
