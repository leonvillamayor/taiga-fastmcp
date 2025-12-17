"""Responses estructurados para las herramientas MCP de Taiga.

Este módulo contiene las clases de respuesta Pydantic que proporcionan
validación automática y tipado fuerte para todas las operaciones
de la API de Taiga.
"""

from src.application.responses.base import BaseResponse, SuccessResponse
from src.application.responses.epic_responses import (
    EpicAttachmentResponse,
    EpicCustomAttributeResponse,
    EpicCustomAttributeValuesResponse,
    EpicFiltersResponse,
    EpicListResponse,
    EpicRelatedUserstoryResponse,
    EpicResponse,
    EpicVoterResponse,
    EpicWatcherResponse,
)
from src.application.responses.project_responses import (
    ProjectListResponse,
    ProjectResponse,
    ProjectStatsResponse,
)

__all__ = [
    # Base
    "BaseResponse",
    "EpicAttachmentResponse",
    "EpicCustomAttributeResponse",
    "EpicCustomAttributeValuesResponse",
    "EpicFiltersResponse",
    "EpicListResponse",
    "EpicRelatedUserstoryResponse",
    # Epic
    "EpicResponse",
    "EpicVoterResponse",
    "EpicWatcherResponse",
    "ProjectListResponse",
    # Project
    "ProjectResponse",
    "ProjectStatsResponse",
    "SuccessResponse",
]
