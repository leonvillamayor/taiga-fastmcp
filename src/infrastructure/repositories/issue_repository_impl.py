"""
Issue repository implementation for Taiga MCP Server.

Concrete implementation using TaigaAPIClient for issue persistence.
"""

from typing import Any

from src.domain.entities.issue import Issue
from src.domain.repositories.issue_repository import IssueRepository
from src.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl
from src.taiga_client import TaigaAPIClient


class IssueRepositoryImpl(BaseRepositoryImpl[Issue], IssueRepository):
    """
    Concrete implementation of Issue repository using Taiga API client.

    Extends BaseRepositoryImpl with issue-specific operations like
    reference lookup, type/severity/priority filtering, and bulk operations.
    """

    def __init__(self, client: TaigaAPIClient) -> None:
        """
        Initialize the issue repository.

        Args:
            client: TaigaAPIClient instance for API communication
        """
        super().__init__(client=client, entity_class=Issue, endpoint="issues")

    def _to_entity(self, data: dict[str, Any]) -> Issue:
        """
        Convert API response dictionary to Issue entity.

        Handles field mapping between API response and entity.

        Args:
            data: Dictionary from API response

        Returns:
            Issue entity instance
        """
        # Map API fields to entity fields
        mapped_data = dict(data)
        if "project" in mapped_data and "project_id" not in mapped_data:
            mapped_data["project_id"] = mapped_data.pop("project")
        if "assigned_to" in mapped_data and "assigned_to_id" not in mapped_data:
            mapped_data["assigned_to_id"] = mapped_data.pop("assigned_to")
        if "milestone" in mapped_data and "milestone_id" not in mapped_data:
            mapped_data["milestone_id"] = mapped_data.pop("milestone")
        return self.entity_class.model_validate(mapped_data)

    def _to_dict(self, entity: Issue, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert Issue entity to dictionary for API request.

        Maps entity fields to API field names.

        Args:
            entity: Issue entity instance
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary for API request
        """
        data = entity.model_dump(exclude_none=exclude_none)
        # Map entity fields to API fields
        if "project_id" in data:
            data["project"] = data.pop("project_id")
        if "assigned_to_id" in data:
            data["assigned_to"] = data.pop("assigned_to_id")
        if "milestone_id" in data:
            data["milestone"] = data.pop("milestone_id")
        return data

    async def get_by_ref(self, project_id: int, ref: int) -> Issue | None:
        """
        Get an issue by its reference number within a project.

        Args:
            project_id: Project ID
            ref: Reference number

        Returns:
            Issue if found, None otherwise
        """
        try:
            response = await self.client.get(
                f"{self.endpoint}/by_ref", params={"project": project_id, "ref": ref}
            )
            if response and isinstance(response, dict):
                return self._to_entity(response)
            return None
        except Exception:
            return None

    async def list_by_type(self, project_id: int, type_id: int) -> list[Issue]:
        """
        List issues of a specific type.

        Args:
            project_id: Project ID
            type_id: Type ID

        Returns:
            List of issues of that type
        """
        return await self.list(filters={"project": project_id, "type": type_id})

    async def list_by_severity(self, project_id: int, severity_id: int) -> list[Issue]:
        """
        List issues with a specific severity.

        Args:
            project_id: Project ID
            severity_id: Severity ID

        Returns:
            List of issues with that severity
        """
        return await self.list(filters={"project": project_id, "severity": severity_id})

    async def list_by_priority(self, project_id: int, priority_id: int) -> list[Issue]:
        """
        List issues with a specific priority.

        Args:
            project_id: Project ID
            priority_id: Priority ID

        Returns:
            List of issues with that priority
        """
        return await self.list(filters={"project": project_id, "priority": priority_id})

    async def list_by_milestone(self, milestone_id: int) -> list[Issue]:
        """
        List issues for a specific milestone.

        Args:
            milestone_id: Milestone ID

        Returns:
            List of issues in the milestone
        """
        return await self.list(filters={"milestone": milestone_id})

    async def list_open(self, project_id: int) -> list[Issue]:
        """
        List open issues for a project.

        Args:
            project_id: Project ID

        Returns:
            List of open issues
        """
        return await self.list(filters={"project": project_id, "is_closed": False})

    async def list_closed(self, project_id: int) -> list[Issue]:
        """
        List closed issues for a project.

        Args:
            project_id: Project ID

        Returns:
            List of closed issues
        """
        return await self.list(filters={"project": project_id, "is_closed": True})

    async def bulk_create(self, issues: list[Issue]) -> list[Issue]:
        """
        Create multiple issues in bulk.

        Args:
            issues: List of issues to create

        Returns:
            List of created issues with assigned IDs
        """
        if not issues:
            return []

        # Extract project_id from first issue
        project_id = issues[0].project_id

        # Prepare bulk data
        issues_data = [self._to_dict(issue) for issue in issues]
        for data in issues_data:
            data.pop("id", None)
            data.pop("version", None)

        try:
            response = await self.client.post(
                f"{self.endpoint}/bulk_create",
                data={"project_id": project_id, "bulk_issues": issues_data},
            )
            if isinstance(response, list):
                return [self._to_entity(item) for item in response]
            return []
        except Exception:
            return []

    async def get_filters(self, project_id: int) -> dict[str, Any]:
        """
        Get available filter options for issues.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with filter options (types, severities, priorities, etc.)
        """
        try:
            response = await self.client.get(
                f"{self.endpoint}/filters_data", params={"project": project_id}
            )
            if response and isinstance(response, dict):
                return dict(response)
            return {}
        except Exception:
            return {}
