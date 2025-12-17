"""Tests for repository interfaces."""

import inspect
from abc import ABC

import pytest

from src.domain.repositories import (
    BaseRepository,
    EpicRepository,
    IssueRepository,
    MemberRepository,
    MilestoneRepository,
    ProjectRepository,
    TaskRepository,
    UserStoryRepository,
    WikiRepository,
)


class TestRepositoryInterfaces:
    """Test suite for verifying repository interfaces are properly defined."""

    def test_base_repository_is_abstract(self) -> None:
        """Test 1.4.1: Verify that BaseRepository is abstract."""
        assert issubclass(BaseRepository, ABC)
        assert inspect.isabstract(BaseRepository)

    def test_base_repository_defines_crud_methods(self) -> None:
        """Test 1.4.2: Verify that BaseRepository defines CRUD methods."""
        expected_methods = {
            "get_by_id",
            "list",
            "create",
            "update",
            "delete",
            "exists",
        }

        abstract_methods = set(BaseRepository.__abstractmethods__)
        assert expected_methods.issubset(abstract_methods), (
            f"Missing methods: {expected_methods - abstract_methods}"
        )

    def test_epic_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that EpicRepository inherits from BaseRepository."""
        assert issubclass(EpicRepository, BaseRepository)
        assert issubclass(EpicRepository, ABC)
        assert inspect.isabstract(EpicRepository)

    def test_project_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that ProjectRepository inherits from BaseRepository."""
        assert issubclass(ProjectRepository, BaseRepository)
        assert issubclass(ProjectRepository, ABC)
        assert inspect.isabstract(ProjectRepository)

    def test_user_story_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that UserStoryRepository inherits from BaseRepository."""
        assert issubclass(UserStoryRepository, BaseRepository)
        assert issubclass(UserStoryRepository, ABC)
        assert inspect.isabstract(UserStoryRepository)

    def test_task_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that TaskRepository inherits from BaseRepository."""
        assert issubclass(TaskRepository, BaseRepository)
        assert issubclass(TaskRepository, ABC)
        assert inspect.isabstract(TaskRepository)

    def test_issue_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that IssueRepository inherits from BaseRepository."""
        assert issubclass(IssueRepository, BaseRepository)
        assert issubclass(IssueRepository, ABC)
        assert inspect.isabstract(IssueRepository)

    def test_milestone_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that MilestoneRepository inherits from BaseRepository."""
        assert issubclass(MilestoneRepository, BaseRepository)
        assert issubclass(MilestoneRepository, ABC)
        assert inspect.isabstract(MilestoneRepository)

    def test_member_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that MemberRepository inherits from BaseRepository."""
        assert issubclass(MemberRepository, BaseRepository)
        assert issubclass(MemberRepository, ABC)
        assert inspect.isabstract(MemberRepository)

    def test_wiki_repository_inherits_from_base(self) -> None:
        """Test 1.4.3: Verify that WikiRepository inherits from BaseRepository."""
        assert issubclass(WikiRepository, BaseRepository)
        assert issubclass(WikiRepository, ABC)
        assert inspect.isabstract(WikiRepository)

    def test_repositories_cannot_be_instantiated(self) -> None:
        """Test 1.4.4: Verify that abstract repositories cannot be instantiated."""
        repositories = [
            BaseRepository,
            EpicRepository,
            ProjectRepository,
            UserStoryRepository,
            TaskRepository,
            IssueRepository,
            MilestoneRepository,
            MemberRepository,
            WikiRepository,
        ]

        for repo_class in repositories:
            with pytest.raises(TypeError):
                # Intentar instanciar una clase abstracta debe fallar
                repo_class()

    def test_base_repository_has_correct_type_hints(self) -> None:
        """Test 1.4.4: Verify BaseRepository has correct type hints using Generic[T]."""
        # Verificar que BaseRepository tiene el parámetro genérico
        assert hasattr(BaseRepository, "__orig_bases__")

        # Verificar firmas de métodos tienen type hints
        get_by_id_sig = inspect.signature(BaseRepository.get_by_id)
        assert "entity_id" in get_by_id_sig.parameters
        assert get_by_id_sig.parameters["entity_id"].annotation is int

    def test_project_repository_has_specific_methods(self) -> None:
        """Test that ProjectRepository has project-specific methods."""
        specific_methods = {
            "get_by_slug",
            "list_by_member",
            "list_private",
            "list_public",
            "get_stats",
        }

        abstract_methods = set(ProjectRepository.__abstractmethods__)
        assert specific_methods.issubset(abstract_methods), (
            f"Missing methods: {specific_methods - abstract_methods}"
        )

    def test_user_story_repository_has_specific_methods(self) -> None:
        """Test that UserStoryRepository has user story-specific methods."""
        specific_methods = {
            "get_by_ref",
            "list_by_milestone",
            "list_by_status",
            "list_backlog",
            "bulk_create",
            "bulk_update",
            "move_to_milestone",
            "get_filters",
        }

        abstract_methods = set(UserStoryRepository.__abstractmethods__)
        assert specific_methods.issubset(abstract_methods), (
            f"Missing methods: {specific_methods - abstract_methods}"
        )

    def test_epic_repository_has_specific_methods(self) -> None:
        """Test that EpicRepository has epic-specific methods."""
        specific_methods = {
            "get_by_ref",
            "bulk_create",
            "get_filters",
            "upvote",
            "downvote",
            "watch",
            "unwatch",
            "list_by_project",
            "list_by_status",
        }

        abstract_methods = set(EpicRepository.__abstractmethods__)
        assert specific_methods.issubset(abstract_methods), (
            f"Missing methods: {specific_methods - abstract_methods}"
        )

    def test_all_repositories_have_docstrings(self) -> None:
        """Test that all repository interfaces have proper docstrings."""
        repositories = [
            BaseRepository,
            EpicRepository,
            ProjectRepository,
            UserStoryRepository,
            TaskRepository,
            IssueRepository,
            MilestoneRepository,
            MemberRepository,
            WikiRepository,
        ]

        for repo_class in repositories:
            assert repo_class.__doc__ is not None
            assert len(repo_class.__doc__.strip()) > 0

    def test_all_repository_methods_have_docstrings(self) -> None:
        """Test that all abstract methods have docstrings."""
        repositories = [
            BaseRepository,
            EpicRepository,
            ProjectRepository,
            UserStoryRepository,
            TaskRepository,
            IssueRepository,
            MilestoneRepository,
            MemberRepository,
            WikiRepository,
        ]

        for repo_class in repositories:
            for method_name in repo_class.__abstractmethods__:
                method = getattr(repo_class, method_name)
                assert method.__doc__ is not None, (
                    f"{repo_class.__name__}.{method_name} has no docstring"
                )
                assert len(method.__doc__.strip()) > 0
