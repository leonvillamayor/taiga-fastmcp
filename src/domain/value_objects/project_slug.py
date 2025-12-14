"""Value object para slug de proyecto."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectSlug(BaseModel):
    """
    Slug de proyecto (identificador URL-friendly).

    Un slug es un identificador único amigable para URLs que sigue reglas específicas:
    - Solo minúsculas, números y guiones
    - No puede empezar ni terminar con guión
    - Mínimo 3 caracteres, máximo 50

    Este es un Value Object inmutable (frozen=True).

    Attributes:
        value: Cadena que contiene el slug validado

    Examples:
        >>> slug = ProjectSlug(value="mi-proyecto-2024")
        >>> str(slug)
        'mi-proyecto-2024'
        >>> slug.value = "otro"  # Lanza ValidationError (inmutable)
    """

    model_config = ConfigDict(
        frozen=True,  # Inmutable (value object)
        str_strip_whitespace=True,
    )

    value: str = Field(..., min_length=3, max_length=50, description="Slug del proyecto")

    @field_validator("value")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """
        Valida formato de slug.

        Args:
            v: Valor del slug a validar

        Returns:
            Slug validado en minúsculas

        Raises:
            ValueError: Si el slug no cumple con el formato requerido
        """
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(
                "Slug debe contener solo minúsculas, números y guiones (no al inicio/fin)"
            )
        return v

    def __str__(self) -> str:
        """Representación en string del slug."""
        return self.value

    def __repr__(self) -> str:
        """Representación detallada del slug."""
        return f"ProjectSlug('{self.value}')"
