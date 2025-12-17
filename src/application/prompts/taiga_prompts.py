"""
MCP Prompts para Taiga.

Este módulo implementa los prompts MCP que proporcionan
plantillas estructuradas para tareas comunes de gestión
de proyectos en Taiga.

Los prompts MCP son plantillas que ayudan a los usuarios
a interactuar con Taiga de manera más efectiva.
"""

from fastmcp import FastMCP

from src.infrastructure.logging import get_logger


class TaigaPrompts:
    """
    Prompts MCP para interacción con Taiga.

    Esta clase proporciona prompts para:
    - Planificación de sprints
    - Análisis de salud del proyecto
    - Triaje de issues
    - Resúmenes de retrospectiva
    - Daily standup

    Los prompts son plantillas que guían la interacción
    con el sistema de gestión de proyectos.

    Attributes:
        mcp: Instancia de FastMCP para registrar prompts
    """

    def __init__(self, mcp: FastMCP) -> None:
        """
        Inicializa TaigaPrompts.

        Args:
            mcp: Instancia de FastMCP
        """
        self.mcp = mcp
        self._logger = get_logger("taiga_prompts")

    def register_prompts(self) -> None:
        """Registra todos los prompts MCP."""
        self._register_planning_prompts()
        self._register_analysis_prompts()
        self._register_workflow_prompts()

    def _register_planning_prompts(self) -> None:
        """Registra prompts relacionados con planificación."""

        @self.mcp.prompt(
            name="sprint_planning",
            description="Generate a structured sprint planning session guide for a Taiga project",
        )
        def sprint_planning_prompt(
            project_name: str,
            sprint_name: str,
            sprint_duration_weeks: int = 2,
            team_capacity_points: int = 40,
        ) -> str:
            """
            Generate a sprint planning prompt.

            Creates a structured guide for conducting a sprint planning
            session with the team.

            Args:
                project_name: Name of the project
                sprint_name: Name of the sprint to plan
                sprint_duration_weeks: Duration of the sprint in weeks
                team_capacity_points: Total story points the team can handle

            Returns:
                Formatted sprint planning guide
            """
            self._logger.debug(
                f"[prompt:sprint_planning] Generating for {project_name}/{sprint_name}"
            )

            return f"""# Sprint Planning: {sprint_name}
Project: {project_name}
Duration: {sprint_duration_weeks} weeks
Team Capacity: {team_capacity_points} story points

## Pre-Planning Checklist
1. Review backlog items using `taiga_list_userstories` with status filter
2. Check team availability and capacity
3. Review previous sprint velocity using `taiga_get_project_stats`
4. Identify any carry-over items from previous sprint

## Planning Steps

### Step 1: Backlog Review
Use these Taiga tools to review the backlog:
- `taiga_list_userstories` - Get all user stories in the backlog
- `taiga_get_userstory` - Get details of specific stories
- `taiga_list_epics` - Review epic progress

### Step 2: Story Selection
For each candidate story:
1. Review acceptance criteria
2. Estimate story points (if not done)
3. Identify dependencies
4. Assign to team member

Use `taiga_update_userstory` to:
- Set milestone (sprint)
- Assign user
- Update status

### Step 3: Task Breakdown
For each selected story:
1. Use `taiga_list_tasks` to see existing tasks
2. Use `taiga_create_task` to add new tasks
3. Estimate hours per task

### Step 4: Capacity Check
- Total selected points should not exceed {team_capacity_points}
- Use `taiga_bulk_update_milestone` to move stories to sprint
- Use `taiga_bulk_update_sprint_order` to prioritize within sprint

## Sprint Goals
Document 2-3 key goals for this sprint:
1. [Goal 1]
2. [Goal 2]
3. [Goal 3]

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Code reviewed
- [ ] Tests passing
- [ ] Documentation updated
"""

        # Store reference for testing
        self.sprint_planning_prompt = sprint_planning_prompt

        @self.mcp.prompt(
            name="backlog_refinement",
            description="Generate a structured backlog refinement session guide",
        )
        def backlog_refinement_prompt(
            project_name: str,
            stories_to_review: int = 10,
        ) -> str:
            """
            Generate a backlog refinement prompt.

            Creates a guide for conducting backlog refinement/grooming
            sessions.

            Args:
                project_name: Name of the project
                stories_to_review: Number of stories to review

            Returns:
                Formatted backlog refinement guide
            """
            self._logger.debug(f"[prompt:backlog_refinement] Generating for {project_name}")

            return f"""# Backlog Refinement Session
Project: {project_name}
Stories to Review: {stories_to_review}

## Session Goals
1. Review and clarify user stories
2. Estimate story points
3. Identify dependencies and blockers
4. Ensure stories are ready for sprint planning

## Preparation
Use these tools before the session:
- `taiga_list_userstories` with filters to get unrefined stories
- `taiga_search` to find related items
- `taiga_list_epics` to understand epic context

## Refinement Process

### For Each Story:

#### 1. Story Review
- Read the story description
- Check acceptance criteria completeness
- Use `taiga_get_userstory` for full details

#### 2. Discussion Points
- Is the story clear and understandable?
- Are acceptance criteria testable?
- What are the technical considerations?
- Are there dependencies on other stories?

#### 3. Estimation
If using Planning Poker:
- Team discusses complexity
- Each member estimates
- Discuss outliers
- Reach consensus

Update with `taiga_update_userstory`:
- Set points field
- Add any notes to description

#### 4. Story Splitting
If story is too large (>8 points):
- Use `taiga_create_userstory` to create smaller stories
- Update original with `taiga_update_userstory`
- Link to epic if applicable

## Session Output
- {stories_to_review} stories reviewed and estimated
- Stories ready for sprint planning
- Blockers identified and documented
"""

        # Store reference for testing
        self.backlog_refinement_prompt = backlog_refinement_prompt

    def _register_analysis_prompts(self) -> None:
        """Registra prompts relacionados con análisis."""

        @self.mcp.prompt(
            name="project_health_analysis",
            description="Analyze the health and status of a Taiga project",
        )
        def project_health_analysis_prompt(
            project_name: str,
            include_velocity: bool = True,
            include_burndown: bool = True,
        ) -> str:
            """
            Generate a project health analysis prompt.

            Creates a comprehensive guide for analyzing project health
            metrics and identifying potential issues.

            Args:
                project_name: Name of the project
                include_velocity: Whether to include velocity analysis
                include_burndown: Whether to include burndown analysis

            Returns:
                Formatted project health analysis guide
            """
            self._logger.debug(f"[prompt:project_health_analysis] Generating for {project_name}")

            velocity_section = ""
            if include_velocity:
                velocity_section = """
### Velocity Analysis
1. Get sprint history using `taiga_list_milestones`
2. For each completed sprint:
   - Count completed story points
   - Calculate average velocity
3. Identify velocity trends (improving/declining/stable)
"""

            burndown_section = ""
            if include_burndown:
                burndown_section = """
### Burndown Analysis
1. Get current sprint using `taiga_get_milestone`
2. Check remaining work vs. time remaining
3. Identify if sprint is on track, ahead, or behind
"""

            return f"""# Project Health Analysis: {project_name}

## Overview
This analysis will evaluate the current health of the project
across multiple dimensions.

## Data Collection

### Step 1: Project Statistics
Use `taiga_get_project_stats` or resource `taiga://projects/{{id}}/stats` to get:
- Total user stories, tasks, issues
- Completion rates
- Points distribution

### Step 2: Current Sprint Status
Use `taiga_list_milestones` to find active sprint, then:
- Check completion percentage
- Review remaining items
- Identify blocked items
{velocity_section}{burndown_section}
## Health Indicators

### 1. Backlog Health
- [ ] Backlog is groomed (stories have estimates)
- [ ] Stories have clear acceptance criteria
- [ ] No stale items (>30 days without update)

Use `taiga_list_userstories` with date filters to check.

### 2. Sprint Health
- [ ] Sprint has clear goals
- [ ] Work is evenly distributed
- [ ] No items blocked for >2 days

### 3. Issue Health
- [ ] Critical issues addressed within SLA
- [ ] Issue backlog is manageable
- [ ] Issues are properly categorized

Use `taiga_list_issues` with priority/severity filters.

### 4. Team Health
- [ ] Workload is balanced
- [ ] No single points of failure
- [ ] Team communication is healthy

Use `taiga://projects/{{id}}/members` resource to review team.

## Recommendations
Based on analysis, provide:
1. Immediate actions needed
2. Short-term improvements (this sprint)
3. Long-term improvements (next quarter)

## Risk Assessment
- High Risk: [Issues requiring immediate attention]
- Medium Risk: [Issues to address soon]
- Low Risk: [Issues to monitor]
"""

        # Store reference for testing
        self.project_health_analysis_prompt = project_health_analysis_prompt

        @self.mcp.prompt(
            name="issue_triage",
            description="Guide for triaging and prioritizing issues in a Taiga project",
        )
        def issue_triage_prompt(
            project_name: str,
            triage_count: int = 20,
        ) -> str:
            """
            Generate an issue triage prompt.

            Creates a structured guide for triaging and prioritizing
            incoming issues.

            Args:
                project_name: Name of the project
                triage_count: Number of issues to triage

            Returns:
                Formatted issue triage guide
            """
            self._logger.debug(f"[prompt:issue_triage] Generating for {project_name}")

            return f"""# Issue Triage Session
Project: {project_name}
Issues to Process: {triage_count}

## Triage Goals
1. Categorize new issues
2. Set appropriate priority and severity
3. Assign to team members
4. Identify duplicates or related issues

## Setup
Get untriaged issues:
```
taiga_list_issues with status="New" or unassigned
```

## Triage Process

### For Each Issue:

#### 1. Initial Assessment
- Read issue description
- Check reproduction steps (if bug)
- Review attachments/screenshots

Use `taiga_get_issue` for full details.

#### 2. Categorization
Set issue type using `taiga_update_issue`:
- Bug: Something broken
- Enhancement: Improvement request
- Question: Clarification needed
- Support: User assistance

#### 3. Priority Assignment
| Priority | Criteria |
|----------|----------|
| Critical | System down, data loss |
| High | Major feature broken |
| Normal | Standard defect/request |
| Low | Minor inconvenience |

#### 4. Severity Assignment
| Severity | Criteria |
|----------|----------|
| Critical | Complete blocker |
| High | Significant impact |
| Normal | Moderate impact |
| Low | Minimal impact |

#### 5. Assignment
Consider:
- Team member expertise
- Current workload
- Issue complexity

Use `taiga_update_issue` to assign.

#### 6. Duplicate Check
Use `taiga_search` to find related issues:
- Similar keywords
- Same component
- Related timeframe

Link duplicates in comments.

## Triage Outcome
- Issues categorized: {triage_count}
- Critical issues escalated: [count]
- Duplicates identified: [count]
- Assigned to team: [count]
"""

        # Store reference for testing
        self.issue_triage_prompt = issue_triage_prompt

    def _register_workflow_prompts(self) -> None:
        """Registra prompts relacionados con flujos de trabajo."""

        @self.mcp.prompt(
            name="daily_standup",
            description="Generate a daily standup meeting guide and status report",
        )
        def daily_standup_prompt(
            project_name: str,
            sprint_name: str,
            team_size: int = 5,
        ) -> str:
            """
            Generate a daily standup prompt.

            Creates a guide for conducting effective daily standup
            meetings and gathering status updates.

            Args:
                project_name: Name of the project
                sprint_name: Current sprint name
                team_size: Number of team members

            Returns:
                Formatted daily standup guide
            """
            self._logger.debug(
                f"[prompt:daily_standup] Generating for {project_name}/{sprint_name}"
            )

            return f"""# Daily Standup
Project: {project_name}
Sprint: {sprint_name}
Team Size: {team_size}

## Pre-Standup Data Collection

### Sprint Progress
Use `taiga_get_milestone` to get current sprint status:
- Total items vs. completed
- Days remaining
- Burndown status

### Recent Activity
Use `taiga://projects/{{id}}/timeline` resource or `taiga_get_project_timeline` to see:
- What was completed yesterday
- What was started
- Any blockers raised

### Blocked Items
Use `taiga_list_tasks` or `taiga_list_userstories` with is_blocked=true:
- Identify all blocked items
- Check blocker age
- Review blocker reasons

## Standup Format

### For Each Team Member ({team_size} total):

#### 1. Yesterday
- What did you complete?
- Were there any unexpected challenges?

#### 2. Today
- What will you work on?
- Any planned collaboration?

#### 3. Blockers
- Is anything blocking your progress?
- Do you need help from anyone?

## Post-Standup Actions

### Update Board
For any status changes mentioned:
```
taiga_update_userstory - Change status
taiga_update_task - Mark progress
taiga_create_task - Add new tasks identified
```

### Address Blockers
For each blocker:
1. Identify owner
2. Set action items
3. Follow up timeline

### Sprint Health Check
- On track: Continue as planned
- Behind: Discuss scope adjustment
- Ahead: Consider pulling in more work

## Standup Notes
Date: [Today's date]
Attendees: [Names]

### Key Updates
1. [Update 1]
2. [Update 2]

### Blockers Identified
1. [Blocker 1] - Owner: [Name] - Action: [Action]

### Action Items
1. [Action 1] - Owner: [Name] - Due: [Date]
"""

        # Store reference for testing
        self.daily_standup_prompt = daily_standup_prompt

        @self.mcp.prompt(
            name="sprint_retrospective",
            description="Generate a sprint retrospective meeting guide and template",
        )
        def sprint_retrospective_prompt(
            project_name: str,
            sprint_name: str,
            completed_points: int = 0,
            planned_points: int = 0,
        ) -> str:
            """
            Generate a sprint retrospective prompt.

            Creates a comprehensive guide for conducting sprint
            retrospective meetings.

            Args:
                project_name: Name of the project
                sprint_name: Name of completed sprint
                completed_points: Story points completed
                planned_points: Story points planned

            Returns:
                Formatted retrospective guide
            """
            self._logger.debug(
                f"[prompt:sprint_retrospective] Generating for {project_name}/{sprint_name}"
            )

            completion_rate = (completed_points / planned_points * 100) if planned_points > 0 else 0

            return f"""# Sprint Retrospective: {sprint_name}
Project: {project_name}

## Sprint Summary
- Planned Points: {planned_points}
- Completed Points: {completed_points}
- Completion Rate: {completion_rate:.1f}%

## Data Gathering

### Sprint Metrics
Use these tools to gather sprint data:
- `taiga_get_milestone` - Get sprint details
- `taiga_get_project_stats` - Overall statistics
- `taiga_get_project_timeline` - Activity history

### What We Delivered
List completed items:
```
taiga_list_userstories milestone={{sprint_id}} status="Done"
```

### What We Didn't Complete
List incomplete items:
```
taiga_list_userstories milestone={{sprint_id}} status!="Done"
```

## Retrospective Format

### Part 1: What Went Well (Keep Doing)
Discuss successes and positive aspects:
- Technical achievements
- Team collaboration
- Process improvements
- Individual contributions

### Part 2: What Didn't Go Well (Stop Doing)
Discuss challenges and problems:
- Blockers encountered
- Communication issues
- Technical debt
- Process friction

### Part 3: What Can We Improve (Start Doing)
Discuss improvement opportunities:
- Process changes
- Tool improvements
- Skill development
- Team dynamics

## Action Items Template

| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| [Action 1] | [Name] | [Date] | High/Med/Low |
| [Action 2] | [Name] | [Date] | High/Med/Low |

## Velocity Tracking
- This Sprint: {completed_points} points
- Previous Sprint: [X] points
- 3-Sprint Average: [X] points
- Trend: [Improving/Stable/Declining]

## Carry-Over Items
Document items moving to next sprint:
Use `taiga_bulk_update_milestone` to move items.

## Team Appreciation
Take a moment to recognize:
- Outstanding contributions
- Helpful collaborations
- Learning achievements

## Next Sprint Preview
- Start Date: [Date]
- End Date: [Date]
- Capacity: [X] points
- Key Goals: [Goals]
"""

        # Store reference for testing
        self.sprint_retrospective_prompt = sprint_retrospective_prompt

        @self.mcp.prompt(
            name="release_planning",
            description="Generate a release planning guide for a Taiga project",
        )
        def release_planning_prompt(
            project_name: str,
            release_version: str,
            target_date: str = "",
        ) -> str:
            """
            Generate a release planning prompt.

            Creates a guide for planning and tracking releases.

            Args:
                project_name: Name of the project
                release_version: Version number for release
                target_date: Target release date

            Returns:
                Formatted release planning guide
            """
            self._logger.debug(
                f"[prompt:release_planning] Generating for {project_name} v{release_version}"
            )

            date_section = f"\nTarget Date: {target_date}" if target_date else ""

            return f"""# Release Planning: {project_name} v{release_version}{date_section}

## Release Overview
Define the scope and goals for this release.

## Pre-Release Checklist

### 1. Feature Inventory
Use `taiga_list_epics` and `taiga_list_userstories` to:
- List all features for this release
- Check completion status
- Identify remaining work

### 2. Bug Assessment
Use `taiga_list_issues` to:
- Review open bugs
- Identify release blockers
- Prioritize fixes

### 3. Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [Strategy] |

## Release Scope

### Must Have (P0)
Critical features that must be in this release:
1. [Feature 1]
2. [Feature 2]

### Should Have (P1)
Important features if time permits:
1. [Feature 1]
2. [Feature 2]

### Nice to Have (P2)
Optional features:
1. [Feature 1]

## Sprint Mapping
Map features to sprints:

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| Sprint 1 | [Focus] | [Deliverables] |
| Sprint 2 | [Focus] | [Deliverables] |

## Dependencies
External dependencies to track:
- [ ] [Dependency 1]
- [ ] [Dependency 2]

## Quality Gates
- [ ] All P0 features complete
- [ ] No critical bugs open
- [ ] Performance testing passed
- [ ] Security review complete
- [ ] Documentation updated

## Communication Plan
- Stakeholder updates: [Frequency]
- Demo schedule: [Dates]
- Release notes: [Owner]

## Post-Release
- [ ] Monitor for issues
- [ ] Gather feedback
- [ ] Plan next iteration
"""

        # Store reference for testing
        self.release_planning_prompt = release_planning_prompt
