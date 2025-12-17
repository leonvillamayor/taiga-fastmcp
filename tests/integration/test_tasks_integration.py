"""
Integration tests for Task functionality.
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
class TestTasksIntegration:
    """Integration tests for Tasks with real Taiga API."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Setup test environment."""
        self.username = os.getenv("TAIGA_USERNAME")
        self.password = os.getenv("TAIGA_PASSWORD")
        self.project_id = int(os.getenv("TAIGA_PROJECT_ID", "309804"))

    @pytest.mark.asyncio
    async def test_complete_task_workflow(self, mcp_server, setup_integration_mocks) -> None:
        """Test complete task workflow: create US, create task, update, vote, watch, delete."""
        # 1. Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # 2. First create a user story (required for tasks)
        user_story = await mcp_server.userstory_tools.create_userstory(
            auth_token=auth_token,
            project_id=self.project_id,
            subject="Test US for Task Integration Test",
        )
        us_id = user_story["id"]

        try:
            # 3. Create task
            task = await mcp_server.task_tools.create_task(
                auth_token=auth_token,
                project=self.project_id,
                user_story=us_id,
                subject="Test Task from Integration Test",
                description="This is a test task created by integration tests",
                status=1,
                tags=["test", "integration"],
            )

            assert task["id"] is not None
            task_id = task["id"]

            # 4. Get task
            fetched_task = await mcp_server.task_tools.get_task(
                auth_token=auth_token, task_id=task_id
            )
            assert fetched_task["subject"] == "Test Task from Integration Test"
            assert fetched_task["user_story"] == us_id

            # 5. Update task
            updated_task = await mcp_server.task_tools.update_task(
                auth_token=auth_token,
                task_id=task_id,
                version=fetched_task["version"],
                status=2,  # In Progress
                comment="Task is being worked on",
            )
            assert updated_task["status"] == 2

            # 6. Upvote task
            voted_task = await mcp_server.task_tools.upvote_task(
                auth_token=auth_token, task_id=task_id
            )
            assert voted_task["total_voters"] >= 1

            # 7. Watch task
            watched_task = await mcp_server.task_tools.watch_task(
                auth_token=auth_token, task_id=task_id
            )
            assert watched_task["total_watchers"] >= 1

            # 8. Get task history
            history = await mcp_server.task_tools.get_task_history(
                auth_token=auth_token, task_id=task_id
            )
            assert len(history) > 0

            # 9. Unwatch task
            await mcp_server.task_tools.unwatch_task(auth_token=auth_token, task_id=task_id)

            # 10. Downvote task
            await mcp_server.task_tools.downvote_task(auth_token=auth_token, task_id=task_id)

            # 11. Delete task
            await mcp_server.task_tools.delete_task(auth_token=auth_token, task_id=task_id)

        finally:
            # Cleanup: delete user story
            await mcp_server.userstory_tools.delete_userstory(
                auth_token=auth_token, userstory_id=us_id
            )

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, mcp_server, setup_integration_mocks) -> None:
        """Test listing tasks with various filters."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create a user story first
        user_story = await mcp_server.userstory_tools.create_userstory(
            auth_token=auth_token, project_id=self.project_id, subject="Test US for Task Filtering"
        )
        us_id = user_story["id"]

        try:
            # Create some tasks
            task1 = await mcp_server.task_tools.create_task(
                auth_token=auth_token,
                project=self.project_id,
                user_story=us_id,
                subject="Task 1",
                status=1,
            )

            task2 = await mcp_server.task_tools.create_task(
                auth_token=auth_token,
                project=self.project_id,
                user_story=us_id,
                subject="Task 2",
                status=2,
            )

            # List all tasks in project
            await mcp_server.task_tools.list_tasks(auth_token=auth_token, project=self.project_id)

            # List tasks for specific user story
            us_tasks = await mcp_server.task_tools.list_tasks(
                auth_token=auth_token, project=self.project_id, user_story=us_id
            )

            # Verify filtering worked
            assert len(us_tasks) >= 2
            assert all(task["user_story"] == us_id for task in us_tasks)

            # Cleanup
            await mcp_server.task_tools.delete_task(auth_token=auth_token, task_id=task1["id"])
            await mcp_server.task_tools.delete_task(auth_token=auth_token, task_id=task2["id"])

        finally:
            # Cleanup user story
            await mcp_server.userstory_tools.delete_userstory(
                auth_token=auth_token, userstory_id=us_id
            )

    @pytest.mark.asyncio
    async def test_bulk_create_tasks(self, mcp_server, setup_integration_mocks) -> None:
        """Test bulk creation of tasks."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create a user story first
        user_story = await mcp_server.userstory_tools.create_userstory(
            auth_token=auth_token, project_id=self.project_id, subject="Test US for Bulk Tasks"
        )
        us_id = user_story["id"]

        try:
            # Create multiple tasks
            bulk_tasks = await mcp_server.task_tools.bulk_create_tasks(
                auth_token=auth_token,
                project_id=self.project_id,
                user_story_id=us_id,
                bulk_tasks=[
                    {"subject": "Bulk Task 1"},
                    {"subject": "Bulk Task 2"},
                    {"subject": "Bulk Task 3"},
                ],
            )

            assert len(bulk_tasks) == 3

            # Cleanup: delete created tasks
            for task in bulk_tasks:
                await mcp_server.task_tools.delete_task(auth_token=auth_token, task_id=task["id"])

        finally:
            # Cleanup user story
            await mcp_server.userstory_tools.delete_userstory(
                auth_token=auth_token, userstory_id=us_id
            )

    @pytest.mark.asyncio
    async def test_task_attachments(self, mcp_server, setup_integration_mocks) -> None:
        """Test task attachment functionality."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create user story and task
        user_story = await mcp_server.userstory_tools.create_userstory(
            auth_token=auth_token,
            project_id=self.project_id,
            subject="Test US for Task Attachments",
        )
        us_id = user_story["id"]

        task = await mcp_server.task_tools.create_task(
            auth_token=auth_token,
            project=self.project_id,
            user_story=us_id,
            subject="Task with Attachments",
            description="Testing task attachments",
        )
        task_id = task["id"]

        try:
            # Create a test file
            test_file_path = "/tmp/test_task_attachment.txt"
            with open(test_file_path, "w") as f:
                f.write("This is a test attachment for task")

            # Create attachment
            attachment = await mcp_server.task_tools.create_task_attachment(
                auth_token=auth_token,
                project_id=self.project_id,
                task_id=task_id,
                attached_file=f"@{test_file_path}",
                description="Test task attachment",
            )

            assert attachment["id"] is not None
            attachment_id = attachment["id"]

            # List attachments
            attachments = await mcp_server.task_tools.list_task_attachments(
                auth_token=auth_token, task_id=task_id
            )
            assert len(attachments) > 0

            # Update attachment
            updated_attachment = await mcp_server.task_tools.update_task_attachment(
                auth_token=auth_token,
                attachment_id=attachment_id,
                description="Updated task attachment",
            )
            assert updated_attachment["description"] == "Updated task attachment"

            # Delete attachment
            await mcp_server.task_tools.delete_task_attachment(
                auth_token=auth_token, attachment_id=attachment_id
            )

            # Cleanup test file
            os.remove(test_file_path)

        finally:
            # Delete task and user story
            await mcp_server.task_tools.delete_task(auth_token=auth_token, task_id=task_id)
            await mcp_server.userstory_tools.delete_userstory(
                auth_token=auth_token, userstory_id=us_id
            )

    @pytest.mark.asyncio
    async def test_task_custom_attributes(self, mcp_server, setup_integration_mocks) -> None:
        """Test task custom attributes functionality."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create custom attribute
        custom_attr = await mcp_server.task_tools.create_task_custom_attribute(
            auth_token=auth_token,
            project=self.project_id,
            name="Estimated Hours",
            description="Estimated hours for completion",
            type="number",
            order=99,
        )

        assert custom_attr["id"] is not None
        attr_id = custom_attr["id"]

        try:
            # List custom attributes
            attributes = await mcp_server.task_tools.list_task_custom_attributes(
                auth_token=auth_token, project=self.project_id
            )
            assert any(attr["id"] == attr_id for attr in attributes)

            # Update custom attribute
            updated_attr = await mcp_server.task_tools.update_task_custom_attribute(
                auth_token=auth_token,
                attribute_id=attr_id,
                name="Hours Estimated",
                description="Updated description",
            )
            assert updated_attr["name"] == "Hours Estimated"

        finally:
            # Delete custom attribute
            await mcp_server.task_tools.delete_task_custom_attribute(
                auth_token=auth_token, attribute_id=attr_id
            )

    @pytest.mark.asyncio
    async def test_get_task_filters(self, mcp_server, setup_integration_mocks) -> None:
        """Test getting available task filters."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Get available filters
        filters = await mcp_server.task_tools.get_task_filters(
            auth_token=auth_token, project=self.project_id
        )

        # Verify filter structure
        assert "statuses" in filters
        assert len(filters["statuses"]) > 0
        assert "assigned_users" in filters
        assert "tags" in filters

    @pytest.mark.asyncio
    async def test_get_task_by_ref(self, mcp_server, setup_integration_mocks) -> None:
        """Test getting task by reference."""
        # Authenticate
        auth_result = await mcp_server.auth_tools.authenticate(
            username=self.username, password=self.password
        )
        auth_token = auth_result["auth_token"]

        # Create user story and task
        user_story = await mcp_server.userstory_tools.create_userstory(
            auth_token=auth_token, project_id=self.project_id, subject="Test US for Task by Ref"
        )
        us_id = user_story["id"]

        task = await mcp_server.task_tools.create_task(
            auth_token=auth_token,
            project=self.project_id,
            user_story=us_id,
            subject="Task to get by ref",
        )
        task_id = task["id"]
        task_ref = task["ref"]

        try:
            # Get task by reference
            fetched_task = await mcp_server.task_tools.get_task_by_ref(
                auth_token=auth_token, ref=task_ref, project=self.project_id
            )

            assert fetched_task["id"] == task_id
            assert fetched_task["ref"] == task_ref
            assert fetched_task["subject"] == "Task to get by ref"

        finally:
            # Cleanup
            await mcp_server.task_tools.delete_task(auth_token=auth_token, task_id=task_id)
            await mcp_server.userstory_tools.delete_userstory(
                auth_token=auth_token, userstory_id=us_id
            )
