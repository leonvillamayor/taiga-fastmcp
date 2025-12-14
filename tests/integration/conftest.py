"""
Integration test specific fixtures.
Extends the base conftest with stateful mock behavior for integration tests.
"""

import pytest


@pytest.fixture
def setup_integration_mocks(taiga_client_mock) -> None:
    """
    Fixture that enhances the taiga_client_mock with stateful behavior
    for integration tests that need mocking.

    This is NOT auto-use. Tests that need real API calls should not use this fixture.
    Tests that need stateful mocks should explicitly request this fixture.
    """
    # Shared state management
    mock_user_stories_db = []  # Track user stories for milestone stats

    # Task state management
    mock_tasks_db = []
    task_id_counter = [1]

    async def mock_create_task(data=None, **kwargs) -> None:
        """Mock create_task with state management."""
        if data is not None:
            kwargs = data

        task_id = task_id_counter[0]
        task_id_counter[0] += 1
        task = {
            "id": task_id,
            "ref": task_id,
            "subject": kwargs.get("subject", f"Test Task {task_id}"),
            "project": kwargs.get("project", 1),
            "user_story": kwargs.get("user_story"),
            "version": 1,
            "status": kwargs.get("status", 1),
        }
        mock_tasks_db.append(task)
        return task

    async def mock_list_tasks(**kwargs) -> None:
        """Mock list_tasks with filtering support."""
        result = list(mock_tasks_db)
        if "project" in kwargs and kwargs["project"] is not None:
            result = [t for t in result if t.get("project") == kwargs["project"]]
        if "user_story" in kwargs and kwargs["user_story"] is not None:
            result = [t for t in result if t.get("user_story") == kwargs["user_story"]]
        if "status" in kwargs and kwargs["status"] is not None:
            result = [t for t in result if t.get("status") == kwargs["status"]]
        return result

    async def mock_get_task(task_id, **kwargs) -> None:
        """Mock get_task with state management."""
        task = next((t for t in mock_tasks_db if t["id"] == task_id), None)
        if task:
            return task
        return {
            "id": task_id,
            "ref": task_id,
            "subject": "Test Task",
            "project": 1,
            "user_story": 1,
            "version": 1,
            "status": 1,
        }

    async def mock_get_task_by_ref(ref, project, **kwargs) -> None:
        """Mock get_task_by_ref with state management."""
        task = next(
            (t for t in mock_tasks_db if t.get("ref") == ref and t.get("project") == project), None
        )
        if task:
            return task
        return {
            "id": 1,
            "ref": ref,
            "subject": "Test Task",
            "project": project,
            "user_story": 1,
            "version": 1,
            "status": 1,
        }

    async def mock_update_task(task_id, data=None, **kwargs) -> None:
        """Mock update_task with state management."""
        # Merge data dict and kwargs - support both old and new API styles
        update_data = {}
        if data is not None:
            update_data.update(data)
        update_data.update(kwargs)

        task = next((t for t in mock_tasks_db if t["id"] == task_id), None)
        if not task:
            task = {
                "id": task_id,
                "subject": "Test Task",
                "project": 1,
                "user_story": 1,
                "version": 1,
                "status": 1,
            }
            mock_tasks_db.append(task)

        # Update task with new data
        if "status" in update_data:
            task["status"] = update_data["status"]
        if "subject" in update_data:
            task["subject"] = update_data["subject"]
        task["version"] = update_data.get("version", task.get("version", 1)) + 1

        # Add voting/watching counters if needed
        task["total_voters"] = task.get("total_voters", 0)
        task["total_watchers"] = task.get("total_watchers", 0)

        return task

    async def mock_bulk_create_tasks(project_id=None, bulk_tasks=None, **kwargs) -> None:
        """Mock bulk_create_tasks with state management."""
        project_id = project_id or kwargs.get("project_id")
        bulk_tasks = bulk_tasks or kwargs.get("bulk_tasks")
        user_story_id = kwargs.get("user_story_id")

        tasks = []
        if isinstance(bulk_tasks, str):
            subjects = [line.strip() for line in bulk_tasks.strip().split("\n") if line.strip()]
        else:
            subjects = bulk_tasks if isinstance(bulk_tasks, list) else []

        for item in subjects:
            subject = item.get("subject", "Bulk Task") if isinstance(item, dict) else item

            task_id = task_id_counter[0]
            task_id_counter[0] += 1
            task = {
                "id": task_id,
                "ref": task_id,
                "subject": subject,
                "project": project_id,
                "user_story": user_story_id,
                "version": 1,
                "status": 1,
            }
            mock_tasks_db.append(task)
            tasks.append(task)

        return tasks

    async def mock_delete_task(task_id, **kwargs) -> None:
        """Mock delete_task with state management."""
        nonlocal mock_tasks_db
        mock_tasks_db = [t for t in mock_tasks_db if t["id"] != task_id]
        return

    # Override the mocks with stateful versions
    taiga_client_mock.create_task.side_effect = mock_create_task
    taiga_client_mock.list_tasks.side_effect = mock_list_tasks
    taiga_client_mock.get_task.side_effect = mock_get_task
    taiga_client_mock.get_task_by_ref.side_effect = mock_get_task_by_ref
    taiga_client_mock.update_task.side_effect = mock_update_task
    taiga_client_mock.bulk_create_tasks.side_effect = mock_bulk_create_tasks
    taiga_client_mock.delete_task.side_effect = mock_delete_task

    # Task attachments state
    mock_attachments_db = []
    attachment_id_counter = [1]

    async def mock_create_task_attachment(data=None, **kwargs) -> None:
        # Merge data dict and kwargs - support both old and new API styles
        create_data = {}
        if data is not None:
            create_data.update(data)
        create_data.update(kwargs)

        att_id = attachment_id_counter[0]
        attachment_id_counter[0] += 1
        attachment = {
            "id": att_id,
            "object_id": create_data.get("object_id"),
            "attached_file": create_data.get("attached_file"),
            "description": create_data.get("description", ""),
        }
        mock_attachments_db.append(attachment)
        return attachment

    async def mock_list_task_attachments(**kwargs) -> None:
        task_id = kwargs.get("task_id")
        if task_id:
            return [att for att in mock_attachments_db if att.get("object_id") == task_id]
        return list(mock_attachments_db)

    async def mock_update_task_attachment(attachment_id, data=None, **kwargs) -> None:
        update_data = {}
        if data is not None:
            update_data.update(data)
        update_data.update(kwargs)

        for att in mock_attachments_db:
            if att["id"] == attachment_id:
                if "description" in update_data:
                    att["description"] = update_data["description"]
                return att
        return {"id": attachment_id, "description": update_data.get("description", "Updated")}

    async def mock_delete_task_attachment(attachment_id, **kwargs) -> None:
        nonlocal mock_attachments_db
        mock_attachments_db = [att for att in mock_attachments_db if att["id"] != attachment_id]
        return

    taiga_client_mock.create_task_attachment.side_effect = mock_create_task_attachment
    taiga_client_mock.list_task_attachments.side_effect = mock_list_task_attachments
    taiga_client_mock.update_task_attachment.side_effect = mock_update_task_attachment
    taiga_client_mock.delete_task_attachment.side_effect = mock_delete_task_attachment

    # Task custom attributes state
    mock_custom_attrs_db = []
    custom_attr_id_counter = [1]

    async def mock_create_task_custom_attribute(data=None, **kwargs) -> None:
        # Merge data dict and kwargs - support both old and new API styles
        create_data = {}
        if data is not None:
            create_data.update(data)
        create_data.update(kwargs)

        attr_id = custom_attr_id_counter[0]
        custom_attr_id_counter[0] += 1
        attr = {
            "id": attr_id,
            "project": create_data.get("project"),
            "name": create_data.get("name"),
            "description": create_data.get("description", ""),
            "type": create_data.get("type", "text"),
            "order": create_data.get("order", 0),
        }
        mock_custom_attrs_db.append(attr)
        return attr

    async def mock_list_task_custom_attributes(**kwargs) -> None:
        project = kwargs.get("project")
        if project:
            return [attr for attr in mock_custom_attrs_db if attr.get("project") == project]
        return list(mock_custom_attrs_db)

    async def mock_update_task_custom_attribute(attribute_id, data=None, **kwargs) -> None:
        update_data = {}
        if data is not None:
            update_data.update(data)
        update_data.update(kwargs)

        for attr in mock_custom_attrs_db:
            if attr["id"] == attribute_id:
                if "name" in update_data:
                    attr["name"] = update_data["name"]
                if "description" in update_data:
                    attr["description"] = update_data["description"]
                return attr
        return {"id": attribute_id, "name": update_data.get("name", "Updated Name")}

    async def mock_delete_task_custom_attribute(attribute_id, **kwargs) -> None:
        nonlocal mock_custom_attrs_db
        mock_custom_attrs_db = [attr for attr in mock_custom_attrs_db if attr["id"] != attribute_id]
        return

    taiga_client_mock.create_task_custom_attribute.side_effect = mock_create_task_custom_attribute
    taiga_client_mock.list_task_custom_attributes.side_effect = mock_list_task_custom_attributes
    taiga_client_mock.update_task_custom_attribute.side_effect = mock_update_task_custom_attribute
    taiga_client_mock.delete_task_custom_attribute.side_effect = mock_delete_task_custom_attribute

    # User Story state management (for milestone integration)
    us_id_counter = [1]

    async def mock_create_userstory(data=None, **kwargs) -> None:
        """Mock create_userstory with state management."""
        if data is not None:
            kwargs = data

        us_id = us_id_counter[0]
        us_id_counter[0] += 1
        user_story = {
            "id": us_id,
            "project": kwargs.get("project") or kwargs.get("project_id"),
            "subject": kwargs.get("subject", f"Test User Story {us_id}"),
            "milestone": kwargs.get("milestone"),
            "status": kwargs.get("status", 1),
        }
        mock_user_stories_db.append(user_story)
        return user_story

    async def mock_delete_userstory(userstory_id, **kwargs) -> None:
        """Mock delete_userstory with state management."""
        nonlocal mock_user_stories_db
        mock_user_stories_db = [us for us in mock_user_stories_db if us["id"] != userstory_id]
        return

    taiga_client_mock.create_userstory.side_effect = mock_create_userstory
    taiga_client_mock.delete_userstory.side_effect = mock_delete_userstory

    # Also hook into client.post() to intercept user story creation via HTTP layer
    original_post = taiga_client_mock.post.side_effect

    async def mock_post_with_userstory(endpoint, **kwargs) -> None:
        """Intercept POST /userstories to use stateful mock."""
        if endpoint == "/userstories":
            # Extract data from kwargs
            data = kwargs.get("data", {})
            return await mock_create_userstory(data=data)
        # For other endpoints, use original behavior
        if original_post:
            return await original_post(endpoint, **kwargs)
        return {}

    taiga_client_mock.post.side_effect = mock_post_with_userstory

    # Milestone state management
    mock_milestones_db = []
    milestone_id_counter = [1]

    async def mock_create_milestone(data=None, **kwargs) -> None:
        """Mock create_milestone with state management."""
        if data is not None:
            kwargs = data

        milestone_id = milestone_id_counter[0]
        milestone_id_counter[0] += 1
        milestone = {
            "id": milestone_id,
            "name": kwargs.get("name", f"Test Milestone {milestone_id}"),
            "project": kwargs.get("project", 1),
            "estimated_start": kwargs.get("estimated_start"),
            "estimated_finish": kwargs.get("estimated_finish"),
            "closed": kwargs.get("closed", False),
            "total_watchers": 0,
            "user_stories": [],
        }
        mock_milestones_db.append(milestone)
        return milestone

    async def mock_get_milestone(milestone_id, **kwargs) -> None:
        """Mock get_milestone with state management."""
        milestone = next((m for m in mock_milestones_db if m["id"] == milestone_id), None)
        if milestone:
            return milestone
        return {
            "id": milestone_id,
            "name": "Test Milestone",
            "project": 1,
            "closed": False,
            "total_watchers": 0,
            "user_stories": [],
        }

    async def mock_update_milestone(milestone_id, data=None, **kwargs) -> None:
        """Mock update_milestone with state management."""
        update_data = data or kwargs
        milestone = next((m for m in mock_milestones_db if m["id"] == milestone_id), None)
        if not milestone:
            milestone = {
                "id": milestone_id,
                "name": "Test Milestone",
                "project": 1,
                "closed": False,
                "total_watchers": 0,
                "user_stories": [],
            }
            mock_milestones_db.append(milestone)

        if "name" in update_data:
            milestone["name"] = update_data["name"]
        if "closed" in update_data:
            milestone["closed"] = update_data["closed"]
        if "estimated_start" in update_data:
            milestone["estimated_start"] = update_data["estimated_start"]
        if "estimated_finish" in update_data:
            milestone["estimated_finish"] = update_data["estimated_finish"]

        return milestone

    async def mock_list_milestones(**kwargs) -> None:
        """Mock list_milestones with filtering."""
        result = list(mock_milestones_db)
        if "project" in kwargs and kwargs["project"] is not None:
            result = [m for m in result if m.get("project") == kwargs["project"]]
        if "closed" in kwargs and kwargs["closed"] is not None:
            result = [m for m in result if m.get("closed") == kwargs["closed"]]
        return result

    async def mock_delete_milestone(milestone_id, **kwargs) -> None:
        """Mock delete_milestone with state management."""
        nonlocal mock_milestones_db
        mock_milestones_db = [m for m in mock_milestones_db if m["id"] != milestone_id]
        return

    async def mock_get_milestone_stats(milestone_id, **kwargs) -> None:
        """Mock get_milestone_stats."""
        # Count user stories assigned to this milestone
        us_count = sum(1 for us in mock_user_stories_db if us.get("milestone") == milestone_id)

        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "total_userstories": us_count,
            "completed_userstories": 0,
            "total_points": 0.0,
            "completed_points": 0.0,
            "days": [],  # Burndown chart data
        }

    async def mock_watch_milestone(milestone_id, **kwargs) -> None:
        """Mock watch_milestone."""
        milestone = next((m for m in mock_milestones_db if m["id"] == milestone_id), None)
        if milestone:
            milestone["total_watchers"] = milestone.get("total_watchers", 0) + 1
            if "watchers" not in milestone:
                milestone["watchers"] = []
            if 1 not in milestone["watchers"]:  # User ID 1
                milestone["watchers"].append(1)
            return milestone
        return {"id": milestone_id, "total_watchers": 1, "watchers": [1]}

    async def mock_unwatch_milestone(milestone_id, **kwargs) -> None:
        """Mock unwatch_milestone."""
        milestone = next((m for m in mock_milestones_db if m["id"] == milestone_id), None)
        if milestone:
            milestone["total_watchers"] = max(0, milestone.get("total_watchers", 0) - 1)
            if "watchers" in milestone and 1 in milestone["watchers"]:
                milestone["watchers"].remove(1)
            return milestone
        return {"id": milestone_id, "total_watchers": 0, "watchers": []}

    async def mock_get_milestone_watchers(milestone_id, **kwargs) -> None:
        """Mock get_milestone_watchers."""
        milestone = next((m for m in mock_milestones_db if m["id"] == milestone_id), None)
        if milestone and "watchers" in milestone:
            return [{"id": uid, "username": f"user{uid}"} for uid in milestone["watchers"]]
        return []

    taiga_client_mock.create_milestone.side_effect = mock_create_milestone
    taiga_client_mock.get_milestone.side_effect = mock_get_milestone
    taiga_client_mock.update_milestone.side_effect = mock_update_milestone
    taiga_client_mock.list_milestones.side_effect = mock_list_milestones
    taiga_client_mock.delete_milestone.side_effect = mock_delete_milestone
    taiga_client_mock.get_milestone_stats.side_effect = mock_get_milestone_stats
    taiga_client_mock.watch_milestone.side_effect = mock_watch_milestone
    taiga_client_mock.unwatch_milestone.side_effect = mock_unwatch_milestone
    taiga_client_mock.get_milestone_watchers.side_effect = mock_get_milestone_watchers

    # Wiki state management
    mock_wiki_db = []
    wiki_id_counter = [1]

    async def mock_create_wiki_page(data=None, **kwargs) -> None:
        """Mock create_wiki_page with state management."""
        if data is not None:
            kwargs = data

        wiki_id = wiki_id_counter[0]
        wiki_id_counter[0] += 1
        content = kwargs.get("content", "")
        page = {
            "id": wiki_id,
            "project": kwargs.get("project", 1),
            "slug": kwargs.get("slug", f"test-page-{wiki_id}"),
            "content": content,
            "html": f"<p>{content}</p>",  # Simple HTML conversion
            "version": kwargs.get("version", 1),
            "is_deleted": False,
            "attachments": [],
            "created_date": None,
            "modified_date": None,
            "editions": None,
            "watchers": [],
            "total_watchers": 0,
            "is_watcher": False,
            "last_modifier": None,
            "owner": None,
        }
        mock_wiki_db.append(page)
        return page

    async def mock_get_wiki_page(page_id, **kwargs) -> None:
        """Mock get_wiki_page with state management."""
        page = next(
            (p for p in mock_wiki_db if p["id"] == page_id and not p.get("is_deleted", False)), None
        )
        if page:
            return page
        return None

    async def mock_get_wiki_page_by_slug(project, slug, **kwargs) -> None:
        """Mock get_wiki_page_by_slug."""
        page = next(
            (
                p
                for p in mock_wiki_db
                if p.get("project") == project
                and p.get("slug") == slug
                and not p.get("is_deleted", False)
            ),
            None,
        )
        if page:
            return page
        return None

    async def mock_list_wiki_pages(**kwargs) -> None:
        """Mock list_wiki_pages."""
        project = kwargs.get("project")
        result = [p for p in mock_wiki_db if not p.get("is_deleted", False)]
        if project is not None:
            result = [p for p in result if p.get("project") == project]
        return result

    async def mock_update_wiki_page(page_id, data=None, **kwargs) -> None:
        """Mock update_wiki_page with state management."""
        update_data = data or kwargs
        page = next((p for p in mock_wiki_db if p["id"] == page_id), None)
        if not page:
            return None

        if "content" in update_data:
            page["content"] = update_data["content"]
        if "version" in update_data:
            page["version"] = update_data["version"]
        else:
            page["version"] = page.get("version", 1) + 1

        return page

    async def mock_delete_wiki_page(page_id, **kwargs) -> None:
        """Mock delete_wiki_page by marking as deleted."""
        page = next((p for p in mock_wiki_db if p["id"] == page_id), None)
        if page:
            page["is_deleted"] = True
        return

    async def mock_restore_wiki_page(page_id, **kwargs) -> None:
        """Mock restore_wiki_page."""
        page = next((p for p in mock_wiki_db if p["id"] == page_id), None)
        if page:
            page["is_deleted"] = False
            page["version"] = page.get("version", 1) + 1
            return page
        return None

    async def mock_list_wiki_attachments(**kwargs) -> None:
        """Mock list_wiki_attachments."""
        return []

    async def mock_create_wiki_attachment(data, **kwargs) -> None:
        """Mock create_wiki_attachment."""
        return {"id": 1, "attached_file": data.get("attached_file", "test.txt")}

    async def mock_delete_wiki_attachment(attachment_id, **kwargs) -> None:
        """Mock delete_wiki_attachment."""
        return

    taiga_client_mock.create_wiki_page.side_effect = mock_create_wiki_page
    taiga_client_mock.get_wiki_page.side_effect = mock_get_wiki_page
    taiga_client_mock.get_wiki_page_by_slug.side_effect = mock_get_wiki_page_by_slug
    taiga_client_mock.list_wiki_pages.side_effect = mock_list_wiki_pages
    taiga_client_mock.update_wiki_page.side_effect = mock_update_wiki_page
    taiga_client_mock.delete_wiki_page.side_effect = mock_delete_wiki_page
    taiga_client_mock.restore_wiki_page.side_effect = mock_restore_wiki_page
    taiga_client_mock.list_wiki_attachments.side_effect = mock_list_wiki_attachments
    taiga_client_mock.create_wiki_attachment.side_effect = mock_create_wiki_attachment
    taiga_client_mock.delete_wiki_attachment.side_effect = mock_delete_wiki_attachment

    # Route client.get() calls to stateful mocks based on endpoint
    # This supports the new AutoPaginator pattern where tools call client.get()
    # instead of specific methods like client.list_milestones()
    original_get = taiga_client_mock.get.side_effect

    async def mock_get_router(endpoint, **kwargs):
        """Route GET requests to appropriate mock functions."""
        # Remove pagination params for routing
        params = kwargs.get("params", {})

        # Milestones
        if endpoint == "/milestones" or endpoint.startswith("/milestones?"):
            return await mock_list_milestones(**params)
        if endpoint.startswith("/milestones/") and "/stats" in endpoint:
            milestone_id = int(endpoint.split("/milestones/")[1].split("/")[0])
            return await mock_get_milestone_stats(milestone_id, **params)
        if endpoint.startswith("/milestones/") and "/watchers" in endpoint:
            milestone_id = int(endpoint.split("/milestones/")[1].split("/")[0])
            return await mock_get_milestone_watchers(milestone_id, **params)
        if endpoint.startswith("/milestones/"):
            milestone_id = int(endpoint.split("/milestones/")[1].split("?")[0])
            return await mock_get_milestone(milestone_id, **params)

        # Tasks
        if endpoint == "/tasks" or endpoint.startswith("/tasks?"):
            return await mock_list_tasks(**params)
        if endpoint.startswith("/tasks/") and "/attachments" not in endpoint:
            task_id = int(endpoint.split("/tasks/")[1].split("?")[0])
            return await mock_get_task(task_id, **params)

        # Wiki
        if endpoint == "/wiki" or endpoint.startswith("/wiki?"):
            return await mock_list_wiki_pages(**params)
        if endpoint.startswith("/wiki/attachments") or "/wiki/attachments" in endpoint:
            return await mock_list_wiki_attachments(**params)
        if endpoint.startswith("/wiki/"):
            page_id = int(endpoint.split("/wiki/")[1].split("?")[0])
            return await mock_get_wiki_page(page_id, **params)

        # Fallback to original mock
        if original_get:
            return await original_get(endpoint, **kwargs)
        return []

    taiga_client_mock.get.side_effect = mock_get_router

    return taiga_client_mock
