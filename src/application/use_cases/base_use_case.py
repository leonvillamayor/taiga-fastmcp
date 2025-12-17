"""Use case base para la capa de aplicación."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class BaseUseCase(ABC, Generic[T, R]):
    """
    Caso de uso base abstracto.

    Define el contrato para todos los casos de uso de la aplicación.
    Cada caso de uso encapsula una operación de negocio específica.

    Type Parameters:
        T: Tipo del input (request/comando)
        R: Tipo del output (response/resultado)

    Example:
        >>> class GetProjectUseCase(BaseUseCase[int, Project]):
        ...     async def execute(self, project_id: int) -> Project:
        ...         return await self.repository.get_by_id(project_id)
    """

    @abstractmethod
    async def execute(self, request: T) -> R:
        """
        Ejecuta el caso de uso.

        Args:
            request: Datos de entrada para el caso de uso

        Returns:
            Resultado de la operación

        Raises:
            ValidationError: Si los datos de entrada son inválidos
            ResourceNotFoundError: Si el recurso no existe
            PermissionDeniedError: Si no hay permisos suficientes
        """
