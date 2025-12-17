"""
Infrastructure repository implementations for Taiga MCP Server.

This module provides concrete implementations of the domain repository
interfaces using TaigaAPIClient for API communication.
"""

from .base_repository_impl import BaseRepositoryImpl
from .epic_repository_impl import EpicRepositoryImpl
from .issue_repository_impl import IssueRepositoryImpl
from .member_repository_impl import MemberRepositoryImpl
from .milestone_repository_impl import MilestoneRepositoryImpl
from .project_repository_impl import ProjectRepositoryImpl
from .task_repository_impl import TaskRepositoryImpl
from .user_story_repository_impl import UserStoryRepositoryImpl
from .wiki_repository_impl import WikiRepositoryImpl

__all__ = [
    "BaseRepositoryImpl",
    "EpicRepositoryImpl",
    "IssueRepositoryImpl",
    "MemberRepositoryImpl",
    "MilestoneRepositoryImpl",
    "ProjectRepositoryImpl",
    "TaskRepositoryImpl",
    "UserStoryRepositoryImpl",
    "WikiRepositoryImpl",
]
