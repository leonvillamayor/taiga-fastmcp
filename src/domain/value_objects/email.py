"""Value object para email."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Email(BaseModel):
    """
    Value object para direcciones de correo electrónico.

    Representa una dirección de email validada según formato RFC 5322 (simplificado).
    Este es un Value Object inmutable (frozen=True).

    Attributes:
        value: Dirección de email validada

    Examples:
        >>> email = Email(value="usuario@ejemplo.com")
        >>> str(email)
        'usuario@ejemplo.com'
        >>> email.value = "otro@example.com"  # Lanza ValidationError (inmutable)
    """

    model_config = ConfigDict(
        frozen=True,  # Inmutable (value object)
        str_strip_whitespace=True,
    )

    value: str = Field(..., min_length=3, max_length=254, description="Dirección de email")

    @field_validator("value")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """
        Valida formato de email.

        Implementa una validación simplificada de email basada en RFC 5322.

        Args:
            v: Email a validar

        Returns:
            Email validado en minúsculas

        Raises:
            ValueError: Si el email no cumple con el formato requerido
        """
        # Patrón simplificado para validar email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Formato de email inválido")
        return v.lower()

    def __str__(self) -> str:
        """Representación en string del email."""
        return self.value

    def __repr__(self) -> str:
        """Representación detallada del email."""
        return f"Email('{self.value}')"

    @property
    def domain(self) -> str:
        """
        Obtiene el dominio del email.

        Returns:
            Dominio del email (parte después de @)
        """
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """
        Obtiene la parte local del email.

        Returns:
            Parte local del email (parte antes de @)
        """
        return self.value.split("@")[0]
