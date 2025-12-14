"""Responses base para las herramientas MCP de Taiga.

Este módulo define las clases base de respuesta que proporcionan
configuración común y validación para todas las respuestas de la API.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Response base para todas las herramientas.

    Proporciona configuración común para todas las respuestas:
    - from_attributes: Permite crear instancias desde objetos con atributos
    - populate_by_name: Permite usar tanto el nombre del campo como el alias
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class SuccessResponse(BaseResponse):
    """Response para operaciones exitosas sin datos específicos.

    Se utiliza para operaciones que no devuelven datos específicos,
    como eliminaciones o actualizaciones de estado.

    Attributes:
        success: Indica si la operación fue exitosa (siempre True).
        message: Mensaje descriptivo del resultado de la operación.
    """

    success: bool = True
    message: str


class ErrorResponse(BaseResponse):
    """Response para operaciones fallidas.

    Se utiliza para indicar errores en las operaciones.

    Attributes:
        success: Indica si la operación fue exitosa (siempre False).
        error: Código o tipo de error.
        message: Mensaje descriptivo del error.
        details: Información adicional sobre el error.
    """

    success: bool = False
    error: str
    message: str
    details: dict[str, Any] | None = None
