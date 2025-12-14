"""Value object para token de autenticación."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuthToken(BaseModel):
    """
    Value object para tokens de autenticación.

    Representa un token JWT o similar usado para autenticación en la API de Taiga.
    Este es un Value Object inmutable (frozen=True).

    Attributes:
        value: Token de autenticación

    Examples:
        >>> token = AuthToken(value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        >>> str(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
        >>> token.is_bearer_format()
        False
        >>> bearer = AuthToken(value="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        >>> bearer.is_bearer_format()
        True
    """

    model_config = ConfigDict(
        frozen=True,  # Inmutable (value object)
        str_strip_whitespace=True,
    )

    value: str = Field(..., min_length=10, description="Token de autenticación")

    @field_validator("value")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """
        Valida formato básico del token.

        El strip se realiza automáticamente por str_strip_whitespace=True
        en model_config, y min_length=10 valida tokens vacíos.

        Args:
            v: Token a validar

        Returns:
            Token validado
        """
        return v

    def __str__(self) -> str:
        """Representación en string del token."""
        return self.value

    def __repr__(self) -> str:
        """Representación detallada del token (oculta el valor por seguridad)."""
        return f"AuthToken('***{self.value[-6:] if len(self.value) > 6 else '***'}')"

    def is_bearer_format(self) -> bool:
        """
        Verifica si el token tiene formato Bearer.

        Returns:
            True si el token comienza con 'Bearer ', False en caso contrario
        """
        return self.value.startswith("Bearer ")

    def get_bearer_token(self) -> str:
        """
        Obtiene el token en formato Bearer.

        Returns:
            Token en formato Bearer (añade 'Bearer ' si no lo tiene)
        """
        if self.is_bearer_format():
            return self.value
        return f"Bearer {self.value}"

    def get_raw_token(self) -> str:
        """
        Obtiene el token sin el prefijo Bearer.

        Returns:
            Token sin 'Bearer ' (lo elimina si lo tiene)
        """
        if self.is_bearer_format():
            return self.value[7:]  # Elimina 'Bearer '
        return self.value
