"""Corrige nombres de herramientas en tests para usar prefijo 'taiga_'."""

import re
from pathlib import Path


# Lista de nombres de herramientas sin prefijo que necesitan corrección
TOOL_NAMES = [
    "authenticate",
    "refresh_token",
    "get_current_user",
    "logout",
    "check_auth",
    "list_projects",
    "create_project",
    "get_project",
    "update_project",
    "delete_project",
    "get_project_stats",
    "duplicate_project",
    "like_project",
    "unlike_project",
    "watch_project",
    "unwatch_project",
    "get_project_modules",
    "update_project_modules",
    "get_project_by_slug",
    "get_project_issues_stats",
    "get_project_tags",
    "create_project_tag",
    "edit_project_tag",
    "delete_project_tag",
    "mix_project_tags",
    "export_project",
    "bulk_update_projects_order",
    "list_userstories",
    "create_userstory",
    "get_userstory",
    "update_userstory",
    "delete_userstory",
    "bulk_create_userstories",
    "bulk_update_userstories",
    "bulk_delete_userstories",
    "move_to_milestone",
    "get_userstory_history",
    "watch_userstory",
    "unwatch_userstory",
    "upvote_userstory",
    "downvote_userstory",
    "get_userstory_voters",
    "list_tasks",
    "create_task",
    "get_task",
    "update_task",
    "delete_task",
    "bulk_create_tasks",
    "get_task_filters",
    "upvote_task",
    "downvote_task",
    "get_task_voters",
    "watch_task",
    "unwatch_task",
    "get_task_watchers",
    "list_task_attachments",
    "create_task_attachment",
    "get_task_attachment",
    "update_task_attachment",
    "delete_task_attachment",
    "get_task_history",
    "edit_task_comment",
    "delete_task_comment",
    "list_issues",
    "create_issue",
    "get_issue",
    "get_issue_by_ref",
    "update_issue",
    "delete_issue",
    "bulk_create_issues",
    "get_issue_filters",
    "upvote_issue",
    "downvote_issue",
    "get_issue_voters",
    "watch_issue",
    "unwatch_issue",
    "get_issue_watchers",
    "get_issue_attachments",
    "create_issue_attachment",
    "get_issue_attachment",
    "update_issue_attachment",
    "delete_issue_attachment",
    "get_issue_history",
    "get_issue_comment_versions",
    "edit_issue_comment",
    "delete_issue_comment",
    "undelete_issue_comment",
    "get_issue_custom_attributes",
    "create_issue_custom_attribute",
    "update_issue_custom_attribute",
    "delete_issue_custom_attribute",
    "list_epics",
    "create_epic",
    "get_epic",
    "get_epic_by_ref",
    "update_epic_full",
    "update_epic_partial",
    "delete_epic",
    "list_epic_related_userstories",
    "create_epic_related_userstory",
    "get_epic_related_userstory",
    "update_epic_related_userstory",
    "delete_epic_related_userstory",
    "bulk_create_epics",
    "get_epic_filters",
    "upvote_epic",
    "downvote_epic",
    "get_epic_voters",
    "watch_epic",
    "unwatch_epic",
    "get_epic_watchers",
    "list_epic_attachments",
    "create_epic_attachment",
    "get_epic_attachment",
    "update_epic_attachment",
    "delete_epic_attachment",
    "list_epic_custom_attributes",
    "create_epic_custom_attribute",
    "get_epic_custom_attribute_values",
    "list_milestones",
    "create_milestone",
    "get_milestone",
    "update_milestone",
    "delete_milestone",
    "get_milestone_stats",
    "watch_milestone",
    "unwatch_milestone",
    "get_milestone_watchers",
    "move_related_items_to_milestone",
    "list_memberships",
    "create_membership",
    "get_membership",
    "update_membership",
    "delete_membership",
    "list_webhooks",
    "create_webhook",
    "get_webhook",
    "update_webhook",
    "delete_webhook",
    "test_webhook",
    "list_wiki_pages",
    "create_wiki_page",
    "get_wiki_page",
    "get_wiki_page_by_slug",
    "update_wiki_page",
    "delete_wiki_page",
    "restore_wiki_page",
    "list_wiki_attachments",
    "create_wiki_attachment",
    "update_wiki_attachment",
    "watch_wiki_page",
    "unwatch_wiki_page",
    "create_wiki_link",
    "list_wiki_links",
    "delete_wiki_link",
    "get_user_stats",
    "list_users",
]


def fix_tool_names_in_file(file_path: Path) -> list[tuple[str, str]]:
    """
    Corrige nombres de herramientas en un archivo de test.

    Returns:
        Lista de tuplas (línea_original, línea_corregida)
    """
    content = file_path.read_text()
    changes: list[tuple[str, str]] = []

    for tool_name in TOOL_NAMES:
        # Patrón: assert "tool_name" in tool_names
        # Pero NO cambiar si ya tiene taiga_
        pattern = rf'(assert\s+")({re.escape(tool_name)})(" in tool_names)'

        def replacer(match: re.Match[str]) -> str:
            prefix = match.group(1)
            name = match.group(2)
            suffix = match.group(3)
            if not name.startswith("taiga_"):
                changes.append((name, f"taiga_{name}"))
                return f"{prefix}taiga_{name}{suffix}"
            return match.group(0)

        content = re.sub(pattern, replacer, content)

    if changes:
        file_path.write_text(content)
        print(f"✅ Actualizado: {file_path}")
        for old, new in changes:
            print(f"    {old} → {new}")

    return changes


def main() -> None:
    tests_dir = Path("tests")
    all_changes: list[tuple[str, str]] = []

    for py_file in tests_dir.rglob("*.py"):
        changes = fix_tool_names_in_file(py_file)
        all_changes.extend(changes)

    print(f"\n📊 Total de correcciones: {len(all_changes)}")


if __name__ == "__main__":
    main()
