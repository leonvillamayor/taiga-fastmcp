#!/usr/bin/env python3
"""Script to add annotations to MCP tools based on naming patterns.

This script analyzes tool names and adds appropriate MCP annotations:
- readOnlyHint: True for list_, get_, filters_, search_, voters_, watchers_ operations
- destructiveHint: True for delete_ operations
- idempotentHint: True for update_, upvote_, downvote_, watch_, unwatch_ operations
"""

import re
from pathlib import Path


def get_annotation_for_tool(tool_name: str) -> dict[str, bool]:
    """Determine appropriate annotations based on tool name."""
    name_lower = tool_name.lower()

    # Read-only operations
    read_only_patterns = [
        r"^taiga_list_",
        r"^taiga_get_",
        r"_filters$",
        r"^taiga_search_",
        r"_voters$",
        r"_watchers$",
        r"_attachments$",
        r"_custom_attributes$",
        r"_custom_attribute_values$",
    ]

    # Destructive operations
    delete_patterns = [
        r"^taiga_delete_",
    ]

    # Idempotent operations
    idempotent_patterns = [
        r"^taiga_update_",
        r"^taiga_upvote_",
        r"^taiga_downvote_",
        r"^taiga_watch_",
        r"^taiga_unwatch_",
    ]

    annotations = {}

    for pattern in read_only_patterns:
        if re.search(pattern, name_lower):
            annotations["readOnlyHint"] = True
            break

    for pattern in delete_patterns:
        if re.search(pattern, name_lower):
            annotations["destructiveHint"] = True
            break

    for pattern in idempotent_patterns:
        if re.search(pattern, name_lower):
            annotations["idempotentHint"] = True
            break

    return annotations


def add_annotations_to_file(file_path: Path) -> tuple[int, int]:
    """Add annotations to tools in a file.

    Returns:
        Tuple of (tools_found, tools_updated)
    """
    content = file_path.read_text()

    # Pattern to match @self.mcp.tool( with optional name parameter
    tool_pattern = re.compile(
        r'(@self\.mcp\.tool\()(\s*name\s*=\s*"([^"]+)")?([^)]*)\)',
        re.MULTILINE | re.DOTALL
    )

    tools_found = 0
    tools_updated = 0

    def replace_tool(match: re.Match) -> str:
        nonlocal tools_found, tools_updated
        tools_found += 1

        full_match = match.group(0)
        decorator_start = match.group(1)  # "@self.mcp.tool("
        name_part = match.group(2) or ""  # 'name="..."' or ""
        tool_name = match.group(3)  # The actual name
        rest = match.group(4) or ""  # Everything else before )

        # Skip if already has annotations
        if "annotations=" in full_match:
            return full_match

        # If no name, we can't determine annotations
        if not tool_name:
            return full_match

        annotations = get_annotation_for_tool(tool_name)
        if not annotations:
            return full_match

        tools_updated += 1

        # Build the new decorator
        # Format annotations as dict
        ann_str = ", ".join(f'"{k}": {str(v)}' for k, v in annotations.items())
        ann_param = f"annotations={{{ann_str}}}"

        # Reconstruct the decorator
        if name_part:
            # Has name parameter, add annotations after name
            if rest.strip():
                # Has other parameters
                if rest.strip().startswith(","):
                    return f'{decorator_start}{name_part}, {ann_param}{rest})'
                else:
                    return f'{decorator_start}{name_part}, {ann_param}, {rest})'
            else:
                return f'{decorator_start}{name_part}, {ann_param})'
        else:
            # No name parameter (unlikely but handle it)
            return full_match

    new_content = tool_pattern.sub(replace_tool, content)

    if new_content != content:
        file_path.write_text(new_content)

    return tools_found, tools_updated


def main():
    """Add annotations to all tool files."""
    tools_dir = Path("src/application/tools")

    # Files that need annotations (excluding those that already have them)
    files_to_process = [
        "cache_tools.py",
        "epic_tools.py",
        "issue_tools.py",
        "membership_tools.py",
        "milestone_tools.py",
        "task_tools.py",
        "user_tools.py",
        "webhook_tools.py",
        "wiki_tools.py",
    ]

    total_found = 0
    total_updated = 0

    for filename in files_to_process:
        file_path = tools_dir / filename
        if file_path.exists():
            found, updated = add_annotations_to_file(file_path)
            total_found += found
            total_updated += updated
            print(f"{filename}: {found} tools found, {updated} updated")
        else:
            print(f"{filename}: NOT FOUND")

    print(f"\nTotal: {total_found} tools found, {total_updated} updated")


if __name__ == "__main__":
    main()
