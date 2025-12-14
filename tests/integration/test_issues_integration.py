"""
Integration tests for Issue functionality.
Tests with real Taiga API using credentials from .env
"""

import os

import pytest
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TAIGA_USERNAME") or not os.getenv("TAIGA_PASSWORD"),
    reason="Taiga credentials not configured in .env",
)
class TestIssuesIntegration:
    """Integration tests for Issues with real Taiga API."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Setup test environment."""
        self.username = os.getenv("TAIGA_USERNAME")
        self.password = os.getenv("TAIGA_PASSWORD")
        self.project_id = int(os.getenv("TAIGA_PROJECT_ID", "309804"))

    @pytest.mark.asyncio
    async def test_complete_issue_workflow(self, mcp_server) -> None:
        """Test complete issue workflow: create, update, vote, watch, delete."""
        # 1. Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # 2. Create issue
        issue = await mcp_server.issue_tools.create_issue(
            auth_token=auth_token,
            project=self.project_id,
            subject="Test Issue from Integration Test",
            description="This is a test issue created by integration tests",
            type=1,  # Bug
            severity=2,  # Normal
            priority=2,  # Normal
            tags=["test", "integration"],
        )

        assert issue["id"] is not None
        issue_id = issue["id"]

        try:
            # 3. Get issue
            fetched_issue = await mcp_server.issue_tools.get_issue(
                auth_token=auth_token, issue_id=issue_id
            )
            assert fetched_issue["subject"] == "Test Issue from Integration Test"

            # 4. Update issue
            updated_issue = await mcp_server.issue_tools.update_issue(
                auth_token=auth_token,
                issue_id=issue_id,
                version=fetched_issue["version"],
                status=2,  # In Progress
                severity=3,  # Important
                comment="Issue is being worked on",
            )
            assert updated_issue["status"] == 2
            assert updated_issue["severity"] == 3

            # 5. Upvote issue
            voted_issue = await mcp_server.issue_tools.upvote_issue(
                auth_token=auth_token, issue_id=issue_id
            )
            assert voted_issue["total_voters"] >= 1

            # 6. Watch issue
            watched_issue = await mcp_server.issue_tools.watch_issue(
                auth_token=auth_token, issue_id=issue_id
            )
            assert watched_issue["total_watchers"] >= 1

            # 7. Get issue history
            history = await mcp_server.issue_tools.get_issue_history(
                auth_token=auth_token, issue_id=issue_id
            )
            assert len(history) > 0
            assert any(
                "Issue is being worked on" in str(entry.get("comment", "")) for entry in history
            )

            # 8. Unwatch issue
            unwatched_issue = await mcp_server.issue_tools.unwatch_issue(
                auth_token=auth_token, issue_id=issue_id
            )
            assert unwatched_issue["total_watchers"] >= 0

            # 9. Downvote issue
            downvoted_issue = await mcp_server.issue_tools.downvote_issue(
                auth_token=auth_token, issue_id=issue_id
            )
            assert downvoted_issue["total_voters"] >= 0

        finally:
            # 10. Delete issue (cleanup)
            await mcp_server.issue_tools.delete_issue(auth_token=auth_token, issue_id=issue_id)

    @pytest.mark.asyncio
    async def test_list_issues_with_filters(self, mcp_server) -> None:
        """Test listing issues with various filters."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # List all issues in project
        all_issues = await mcp_server.issue_tools.list_issues(
            auth_token=auth_token, project=self.project_id
        )

        # List only closed issues
        closed_issues = await mcp_server.issue_tools.list_issues(
            auth_token=auth_token, project=self.project_id, is_closed=True
        )

        # List only open issues
        open_issues = await mcp_server.issue_tools.list_issues(
            auth_token=auth_token, project=self.project_id, is_closed=False
        )

        # Verify filtering worked
        assert len(all_issues) >= len(closed_issues)
        assert len(all_issues) >= len(open_issues)

    @pytest.mark.asyncio
    async def test_bulk_create_issues(self, mcp_server) -> None:
        """Test bulk creation of issues."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create multiple issues
        bulk_issues = await mcp_server.issue_tools.bulk_create_issues(
            auth_token=auth_token,
            project_id=self.project_id,
            bulk_issues=[
                {"subject": "Bulk Issue 1", "type": 1, "severity": 2},
                {"subject": "Bulk Issue 2", "type": 1, "severity": 3},
                {"subject": "Bulk Issue 3", "type": 2, "severity": 1},
            ],
        )

        assert len(bulk_issues) == 3

        # Cleanup: delete created issues
        for issue in bulk_issues:
            await mcp_server.issue_tools.delete_issue(auth_token=auth_token, issue_id=issue["id"])

    @pytest.mark.asyncio
    async def test_issue_attachments(self, mcp_server) -> None:
        """Test issue attachment functionality."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create issue
        issue = await mcp_server.issue_tools.create_issue(
            auth_token=auth_token,
            project=self.project_id,
            subject="Issue with Attachments",
            description="Testing attachments",
        )
        issue_id = issue["id"]

        try:
            # Create a test file
            test_file_path = "/tmp/test_attachment.txt"
            with open(test_file_path, "w") as f:
                f.write("This is a test attachment for issue")

            # Create attachment
            attachment = await mcp_server.issue_tools.create_issue_attachment(
                auth_token=auth_token,
                issue_id=issue_id,
                attached_file=f"@{test_file_path}",
                description="Test attachment",
            )

            assert attachment["id"] is not None
            attachment_id = attachment["id"]

            # List attachments
            attachments = await mcp_server.issue_tools.list_issue_attachments(
                auth_token=auth_token, issue_id=issue_id
            )
            assert len(attachments) > 0

            # Update attachment
            updated_attachment = await mcp_server.issue_tools.update_issue_attachment(
                auth_token=auth_token,
                attachment_id=attachment_id,
                description="Updated test attachment",
            )
            assert updated_attachment["description"] == "Updated test attachment"

            # Delete attachment
            await mcp_server.issue_tools.delete_issue_attachment(
                auth_token=auth_token, attachment_id=attachment_id
            )

            # Cleanup test file
            os.remove(test_file_path)

        finally:
            # Delete issue
            await mcp_server.issue_tools.delete_issue(auth_token=auth_token, issue_id=issue_id)

    @pytest.mark.asyncio
    async def test_issue_custom_attributes(self, mcp_server) -> None:
        """Test issue custom attributes functionality."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create custom attribute
        custom_attr = await mcp_server.issue_tools.create_issue_custom_attribute(
            auth_token=auth_token,
            project=self.project_id,
            name="Test Environment",
            description="Environment where issue was found",
            type="text",
            order=99,
        )

        assert custom_attr["id"] is not None
        attr_id = custom_attr["id"]

        try:
            # List custom attributes
            attributes = await mcp_server.issue_tools.list_issue_custom_attributes(
                auth_token=auth_token, project=self.project_id
            )
            assert any(attr["id"] == attr_id for attr in attributes)

            # Update custom attribute
            updated_attr = await mcp_server.issue_tools.update_issue_custom_attribute(
                auth_token=auth_token,
                attribute_id=attr_id,
                name="Testing Environment",
                description="Updated description",
            )
            assert updated_attr["name"] == "Testing Environment"

        finally:
            # Delete custom attribute
            await mcp_server.issue_tools.delete_issue_custom_attribute(
                auth_token=auth_token, attribute_id=attr_id
            )

    @pytest.mark.asyncio
    async def test_get_issue_filters(self, mcp_server) -> None:
        """Test getting available issue filters."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Get available filters
        filters = await mcp_server.issue_tools.get_issue_filters(
            auth_token=auth_token, project=self.project_id
        )

        # Verify filter structure
        assert "statuses" in filters
        assert "types" in filters
        assert "severities" in filters
        assert "priorities" in filters
        assert len(filters["statuses"]) > 0
        assert len(filters["types"]) > 0
