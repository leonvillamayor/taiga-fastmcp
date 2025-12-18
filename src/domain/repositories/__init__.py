"""
Domain repositories interfaces for Taiga MCP Server.
"""

from .base_repository import BaseRepository
from .epic_repository import EpicRepository
from .issue_repository import IssueRepository
from .member_repository import MemberRepository
from .milestone_repository import MilestoneRepository
from .project_repository import ProjectRepository
from .task_repository import TaskRepository
from .user_story_repository import UserStoryRepository
from .wiki_repository import WikiRepository


__all__ = [
    "BaseRepository",
    "EpicRepository",
    "IssueRepository",
    "MemberRepository",
    "MilestoneRepository",
    "ProjectRepository",
    "TaskRepository",
    "UserStoryRepository",
    "WikiRepository",
]
