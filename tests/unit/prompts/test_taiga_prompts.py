"""
Unit tests for TaigaPrompts.

Tests for MCP prompts including:
- Sprint planning
- Backlog refinement
- Project health analysis
- Issue triage
- Daily standup
- Sprint retrospective
- Release planning
"""

from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP

from src.application.prompts.taiga_prompts import TaigaPrompts


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock(spec=FastMCP)
    mcp.prompt = MagicMock(return_value=lambda func: func)
    return mcp


@pytest.fixture
def taiga_prompts(mock_mcp):
    """Create TaigaPrompts instance with mock MCP."""
    return TaigaPrompts(mock_mcp)


class TestTaigaPromptsInit:
    """Tests for TaigaPrompts initialization."""

    def test_init_creates_instance(self, mock_mcp):
        """Test that TaigaPrompts initializes correctly."""
        prompts = TaigaPrompts(mock_mcp)
        assert prompts.mcp == mock_mcp

    def test_register_prompts_calls_registrations(self, mock_mcp):
        """Test that register_prompts registers all prompts."""
        prompts = TaigaPrompts(mock_mcp)
        prompts.register_prompts()

        # Should have called mcp.prompt for each prompt (6 prompts)
        assert mock_mcp.prompt.call_count >= 6


class TestSprintPlanningPrompt:
    """Tests for sprint planning prompt."""

    def test_sprint_planning_prompt_default_values(self, taiga_prompts):
        """Test sprint planning prompt with default values."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.sprint_planning_prompt(
            project_name="Test Project", sprint_name="Sprint 1"
        )

        assert "Sprint Planning: Sprint 1" in result
        assert "Project: Test Project" in result
        assert "Duration: 2 weeks" in result  # Default duration
        assert "Team Capacity: 40 story points" in result  # Default capacity
        assert "Pre-Planning Checklist" in result
        assert "taiga_list_userstories" in result

    def test_sprint_planning_prompt_custom_values(self, taiga_prompts):
        """Test sprint planning prompt with custom values."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.sprint_planning_prompt(
            project_name="Custom Project",
            sprint_name="Sprint 5",
            sprint_duration_weeks=3,
            team_capacity_points=60,
        )

        assert "Sprint Planning: Sprint 5" in result
        assert "Duration: 3 weeks" in result
        assert "Team Capacity: 60 story points" in result
        assert "should not exceed 60" in result

    def test_sprint_planning_prompt_contains_tools_references(self, taiga_prompts):
        """Test sprint planning prompt references Taiga tools."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.sprint_planning_prompt(project_name="Project", sprint_name="Sprint")

        # Should reference various Taiga tools
        assert "taiga_list_userstories" in result
        assert "taiga_get_userstory" in result
        assert "taiga_update_userstory" in result
        assert "taiga_list_tasks" in result
        assert "taiga_create_task" in result
        assert "taiga_bulk_update_milestone" in result


class TestBacklogRefinementPrompt:
    """Tests for backlog refinement prompt."""

    def test_backlog_refinement_prompt_default_values(self, taiga_prompts):
        """Test backlog refinement prompt with defaults."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.backlog_refinement_prompt(project_name="Test Project")

        assert "Backlog Refinement Session" in result
        assert "Project: Test Project" in result
        assert "Stories to Review: 10" in result  # Default

    def test_backlog_refinement_prompt_custom_count(self, taiga_prompts):
        """Test backlog refinement with custom story count."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.backlog_refinement_prompt(
            project_name="Project", stories_to_review=25
        )

        assert "Stories to Review: 25" in result
        assert "25 stories reviewed" in result

    def test_backlog_refinement_contains_estimation_guidance(self, taiga_prompts):
        """Test refinement prompt contains estimation guidance."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.backlog_refinement_prompt(project_name="Test")

        assert "Estimation" in result or "estimate" in result.lower()
        assert "Planning Poker" in result
        assert "Story Splitting" in result


class TestProjectHealthAnalysisPrompt:
    """Tests for project health analysis prompt."""

    def test_health_analysis_prompt_with_all_sections(self, taiga_prompts):
        """Test health analysis includes velocity and burndown."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.project_health_analysis_prompt(
            project_name="Health Project", include_velocity=True, include_burndown=True
        )

        assert "Project Health Analysis: Health Project" in result
        assert "Velocity Analysis" in result
        assert "Burndown Analysis" in result
        assert "Health Indicators" in result
        assert "Risk Assessment" in result

    def test_health_analysis_prompt_without_velocity(self, taiga_prompts):
        """Test health analysis without velocity section."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.project_health_analysis_prompt(
            project_name="Test", include_velocity=False, include_burndown=True
        )

        assert "Velocity Analysis" not in result
        assert "Burndown Analysis" in result

    def test_health_analysis_prompt_without_burndown(self, taiga_prompts):
        """Test health analysis without burndown section."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.project_health_analysis_prompt(
            project_name="Test", include_velocity=True, include_burndown=False
        )

        assert "Velocity Analysis" in result
        assert "Burndown Analysis" not in result

    def test_health_analysis_references_resources(self, taiga_prompts):
        """Test health analysis references MCP resources."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.project_health_analysis_prompt(project_name="Test")

        assert "taiga://projects" in result
        assert "taiga_get_project_stats" in result or "project_stats" in result


class TestIssueTriagePrompt:
    """Tests for issue triage prompt."""

    def test_issue_triage_prompt_default_count(self, taiga_prompts):
        """Test issue triage with default count."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.issue_triage_prompt(project_name="Triage Project")

        assert "Issue Triage Session" in result
        assert "Project: Triage Project" in result
        assert "Issues to Process: 20" in result  # Default

    def test_issue_triage_prompt_custom_count(self, taiga_prompts):
        """Test issue triage with custom count."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.issue_triage_prompt(project_name="Project", triage_count=50)

        assert "Issues to Process: 50" in result
        assert "Issues categorized: 50" in result

    def test_issue_triage_contains_priority_severity(self, taiga_prompts):
        """Test triage prompt contains priority and severity guidance."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.issue_triage_prompt(project_name="Test")

        assert "Priority" in result
        assert "Severity" in result
        assert "Critical" in result
        assert "High" in result
        assert "Normal" in result
        assert "Low" in result

    def test_issue_triage_contains_categorization(self, taiga_prompts):
        """Test triage prompt contains categorization guidance."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.issue_triage_prompt(project_name="Test")

        assert "Bug" in result
        assert "Enhancement" in result
        assert "taiga_update_issue" in result
        assert "taiga_search" in result


class TestDailyStandupPrompt:
    """Tests for daily standup prompt."""

    def test_daily_standup_prompt_basic(self, taiga_prompts):
        """Test daily standup prompt with basic info."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.daily_standup_prompt(
            project_name="Standup Project", sprint_name="Sprint 3"
        )

        assert "Daily Standup" in result
        assert "Project: Standup Project" in result
        assert "Sprint: Sprint 3" in result
        assert "Team Size: 5" in result  # Default

    def test_daily_standup_prompt_custom_team_size(self, taiga_prompts):
        """Test standup with custom team size."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.daily_standup_prompt(
            project_name="Project", sprint_name="Sprint", team_size=8
        )

        assert "Team Size: 8" in result
        assert "8 total" in result

    def test_daily_standup_contains_format(self, taiga_prompts):
        """Test standup contains expected format sections."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.daily_standup_prompt(project_name="Test", sprint_name="Sprint")

        assert "Yesterday" in result
        assert "Today" in result
        assert "Blockers" in result
        assert "Post-Standup Actions" in result

    def test_daily_standup_references_timeline(self, taiga_prompts):
        """Test standup references timeline resource."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.daily_standup_prompt(project_name="Test", sprint_name="Sprint")

        assert "timeline" in result.lower()


class TestSprintRetrospectivePrompt:
    """Tests for sprint retrospective prompt."""

    def test_retrospective_prompt_basic(self, taiga_prompts):
        """Test retrospective prompt with basic info."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.sprint_retrospective_prompt(
            project_name="Retro Project", sprint_name="Sprint 5"
        )

        assert "Sprint Retrospective: Sprint 5" in result
        assert "Project: Retro Project" in result
        assert "Planned Points: 0" in result  # Default
        assert "Completed Points: 0" in result  # Default

    def test_retrospective_prompt_with_points(self, taiga_prompts):
        """Test retrospective with points data."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.sprint_retrospective_prompt(
            project_name="Project", sprint_name="Sprint", completed_points=35, planned_points=40
        )

        assert "Planned Points: 40" in result
        assert "Completed Points: 35" in result
        assert "87.5%" in result  # Completion rate

    def test_retrospective_prompt_zero_division_safe(self, taiga_prompts):
        """Test retrospective handles zero planned points."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.sprint_retrospective_prompt(
            project_name="Project",
            sprint_name="Sprint",
            completed_points=10,
            planned_points=0,  # Would cause division by zero
        )

        # Should not raise an error
        assert "Completion Rate: 0.0%" in result

    def test_retrospective_contains_format_sections(self, taiga_prompts):
        """Test retrospective contains expected format sections."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.sprint_retrospective_prompt(
            project_name="Test", sprint_name="Sprint"
        )

        assert "What Went Well" in result
        assert "What Didn't Go Well" in result
        assert "What Can We Improve" in result
        assert "Action Items" in result


class TestReleasePlanningPrompt:
    """Tests for release planning prompt."""

    def test_release_planning_prompt_basic(self, taiga_prompts):
        """Test release planning prompt with basic info."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.release_planning_prompt(
            project_name="Release Project", release_version="2.0.0"
        )

        assert "Release Planning: Release Project v2.0.0" in result
        assert "Pre-Release Checklist" in result
        assert "Release Scope" in result

    def test_release_planning_prompt_with_date(self, taiga_prompts):
        """Test release planning with target date."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.release_planning_prompt(
            project_name="Project", release_version="1.5.0", target_date="2025-03-01"
        )

        assert "Target Date: 2025-03-01" in result

    def test_release_planning_without_date(self, taiga_prompts):
        """Test release planning without target date."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.release_planning_prompt(
            project_name="Project", release_version="1.0.0", target_date=""
        )

        assert "Target Date:" not in result

    def test_release_planning_contains_priority_sections(self, taiga_prompts):
        """Test release planning contains priority sections."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.release_planning_prompt(project_name="Test", release_version="1.0")

        assert "Must Have (P0)" in result
        assert "Should Have (P1)" in result
        assert "Nice to Have (P2)" in result
        assert "Quality Gates" in result

    def test_release_planning_references_tools(self, taiga_prompts):
        """Test release planning references Taiga tools."""
        taiga_prompts.register_prompts()

        result = taiga_prompts.release_planning_prompt(project_name="Test", release_version="1.0")

        assert "taiga_list_epics" in result
        assert "taiga_list_userstories" in result
        assert "taiga_list_issues" in result
