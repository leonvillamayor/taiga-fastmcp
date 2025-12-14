"""
Tests unitarios para validadores de dominio.

Este módulo contiene tests exhaustivos para los validadores Pydantic
que realizan validación temprana de parámetros.
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.domain.exceptions import ValidationError
from src.domain.validators import (
    EpicCreateValidator,
    EpicUpdateValidator,
    IssueCreateValidator,
    IssueUpdateValidator,
    MembershipCreateValidator,
    MembershipUpdateValidator,
    MilestoneCreateValidator,
    MilestoneUpdateValidator,
    ProjectCreateValidator,
    ProjectDuplicateValidator,
    ProjectTagEditValidator,
    ProjectTagValidator,
    ProjectUpdateValidator,
    TaskCreateValidator,
    TaskUpdateValidator,
    UserStoryCreateValidator,
    UserStoryUpdateValidator,
    WebhookCreateValidator,
    WebhookUpdateValidator,
    WikiPageCreateValidator,
    WikiPageUpdateValidator,
    validate_date_format,
    validate_hex_color,
    validate_input,
    validate_non_empty_string,
    validate_positive_id,
    validate_url,
)


# =============================================================================
# Tests de funciones auxiliares
# =============================================================================


class TestValidatePositiveId:
    """Tests para validate_positive_id."""

    def test_positive_id_valid(self) -> None:
        """Test 3.5.2: ID positivo es aceptado."""
        assert validate_positive_id(1, "test") == 1
        assert validate_positive_id(100, "test") == 100

    def test_zero_id_rejected(self) -> None:
        """Test 3.5.2: ID cero es rechazado."""
        with pytest.raises(ValueError, match="debe ser un número positivo"):
            validate_positive_id(0, "test")

    def test_negative_id_rejected(self) -> None:
        """Test 3.5.2: ID negativo es rechazado."""
        with pytest.raises(ValueError, match="debe ser un número positivo"):
            validate_positive_id(-1, "test")
        with pytest.raises(ValueError, match="debe ser un número positivo"):
            validate_positive_id(-100, "test")

    def test_none_id_accepted(self) -> None:
        """None es aceptado como valor válido."""
        assert validate_positive_id(None, "test") is None


class TestValidateNonEmptyString:
    """Tests para validate_non_empty_string."""

    def test_valid_string(self) -> None:
        """Test 3.5.3: String válido es aceptado."""
        assert validate_non_empty_string("hello", "test") == "hello"

    def test_string_with_spaces_trimmed(self) -> None:
        """String con espacios se limpia."""
        assert validate_non_empty_string("  hello  ", "test") == "hello"

    def test_empty_string_rejected(self) -> None:
        """Test 3.5.1: String vacío es rechazado."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            validate_non_empty_string("", "nombre")

    def test_whitespace_only_rejected(self) -> None:
        """Test 3.5.1: String solo con espacios es rechazado."""
        with pytest.raises(ValueError, match="no puede estar vacío"):
            validate_non_empty_string("   ", "nombre")

    def test_none_accepted(self) -> None:
        """None es aceptado como valor válido."""
        assert validate_non_empty_string(None, "test") is None


class TestValidateHexColor:
    """Tests para validate_hex_color."""

    def test_valid_hex_color(self) -> None:
        """Test 3.5.3: Color hexadecimal válido es aceptado."""
        assert validate_hex_color("#FF5733") == "#FF5733"
        assert validate_hex_color("#000000") == "#000000"
        assert validate_hex_color("#ffffff") == "#ffffff"

    def test_invalid_hex_color_rejected(self) -> None:
        """Color hexadecimal inválido es rechazado."""
        with pytest.raises(ValueError, match="formato hexadecimal #RRGGBB"):
            validate_hex_color("FF5733")  # Sin #
        with pytest.raises(ValueError, match="formato hexadecimal #RRGGBB"):
            validate_hex_color("#FFF")  # Muy corto
        with pytest.raises(ValueError, match="formato hexadecimal #RRGGBB"):
            validate_hex_color("#GGGGGG")  # Caracteres inválidos

    def test_none_accepted(self) -> None:
        """None es aceptado como valor válido."""
        assert validate_hex_color(None) is None


class TestValidateDateFormat:
    """Tests para validate_date_format."""

    def test_valid_date(self) -> None:
        """Test 3.5.3: Fecha válida es aceptada."""
        assert validate_date_format("2024-01-15", "test") == "2024-01-15"
        assert validate_date_format("2024-12-31", "test") == "2024-12-31"

    def test_invalid_date_format_rejected(self) -> None:
        """Formato de fecha inválido es rechazado."""
        with pytest.raises(ValueError, match="formato YYYY-MM-DD"):
            validate_date_format("15-01-2024", "fecha")  # Formato DD-MM-YYYY
        with pytest.raises(ValueError, match="formato YYYY-MM-DD"):
            validate_date_format("2024/01/15", "fecha")  # Separador incorrecto

    def test_invalid_date_values_rejected(self) -> None:
        """Valores de fecha inválidos son rechazados."""
        with pytest.raises(ValueError, match="formato YYYY-MM-DD"):
            validate_date_format("2024-13-15", "fecha")  # Mes 13
        with pytest.raises(ValueError, match="formato YYYY-MM-DD"):
            validate_date_format("2024-02-30", "fecha")  # 30 de febrero

    def test_none_accepted(self) -> None:
        """None es aceptado como valor válido."""
        assert validate_date_format(None, "test") is None


class TestValidateUrl:
    """Tests para validate_url."""

    def test_valid_http_url(self) -> None:
        """Test 3.5.3: URL HTTP válida es aceptada."""
        assert validate_url("http://example.com") == "http://example.com"

    def test_valid_https_url(self) -> None:
        """Test 3.5.3: URL HTTPS válida es aceptada."""
        assert validate_url("https://example.com") == "https://example.com"

    def test_invalid_url_rejected(self) -> None:
        """URL sin protocolo es rechazada."""
        with pytest.raises(ValueError, match="http:// o https://"):
            validate_url("example.com")
        with pytest.raises(ValueError, match="http:// o https://"):
            validate_url("ftp://example.com")

    def test_none_accepted(self) -> None:
        """None es aceptado como valor válido."""
        assert validate_url(None) is None


# =============================================================================
# Tests de validadores de Proyecto
# =============================================================================


class TestProjectCreateValidator:
    """Tests para ProjectCreateValidator."""

    def test_valid_project_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = ProjectCreateValidator(name="Mi Proyecto", description="Descripción")
        assert validator.name == "Mi Proyecto"
        assert validator.description == "Descripción"

    def test_name_required(self) -> None:
        """Test 3.5.1: Nombre vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectCreateValidator(name="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_name_whitespace_only_rejected(self) -> None:
        """Test 3.5.1: Nombre solo con espacios es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectCreateValidator(name="   ")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_name_trimmed(self) -> None:
        """Nombre se limpia de espacios extras."""
        validator = ProjectCreateValidator(name="  Mi Proyecto  ")
        assert validator.name == "Mi Proyecto"

    def test_empty_tags_rejected(self) -> None:
        """Tags vacíos son rechazados."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectCreateValidator(name="Test", tags=["valid", ""])
        errors = exc_info.value.errors()
        assert any("tags" in str(e.get("loc", [])).lower() for e in errors)

    def test_valid_tags_accepted(self) -> None:
        """Tags válidos son aceptados."""
        validator = ProjectCreateValidator(name="Test", tags=["tag1", "tag2"])
        assert validator.tags == ["tag1", "tag2"]


class TestProjectUpdateValidator:
    """Tests para ProjectUpdateValidator."""

    def test_valid_project_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = ProjectUpdateValidator(project_id=1, name="Nuevo nombre")
        assert validator.project_id == 1
        assert validator.name == "Nuevo nombre"

    def test_project_id_positive(self) -> None:
        """Test 3.5.2: ID de proyecto negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectUpdateValidator(project_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)

    def test_project_id_zero_rejected(self) -> None:
        """Test 3.5.2: ID de proyecto cero es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectUpdateValidator(project_id=0)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)

    def test_name_empty_rejected(self) -> None:
        """Test 3.5.1: Nombre vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectUpdateValidator(project_id=1, name="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)


class TestProjectDuplicateValidator:
    """Tests para ProjectDuplicateValidator."""

    def test_valid_duplicate(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = ProjectDuplicateValidator(project_id=1, name="Copia de Proyecto")
        assert validator.project_id == 1
        assert validator.name == "Copia de Proyecto"

    def test_name_required(self) -> None:
        """Test 3.5.1: Nombre es requerido."""
        with pytest.raises(PydanticValidationError):
            ProjectDuplicateValidator(project_id=1, name="")


class TestProjectTagValidator:
    """Tests para ProjectTagValidator."""

    def test_valid_tag(self) -> None:
        """Test 3.5.3: Tag válido es aceptado."""
        validator = ProjectTagValidator(project_id=1, tag="feature", color="#FF5733")
        assert validator.project_id == 1
        assert validator.tag == "feature"
        assert validator.color == "#FF5733"

    def test_tag_empty_rejected(self) -> None:
        """Test 3.5.1: Tag vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectTagValidator(project_id=1, tag="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_color_invalid_rejected(self) -> None:
        """Color inválido es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectTagValidator(project_id=1, tag="feature", color="red")
        errors = exc_info.value.errors()
        assert any("hexadecimal" in str(e.get("msg", "")).lower() for e in errors)


class TestProjectTagEditValidator:
    """Tests para ProjectTagEditValidator."""

    def test_valid_tag_edit(self) -> None:
        """Datos válidos para edición de tag son aceptados."""
        validator = ProjectTagEditValidator(from_tag="bug", to_tag="defect")
        assert validator.from_tag == "bug"
        assert validator.to_tag == "defect"

    def test_valid_tag_edit_with_color(self) -> None:
        """Datos válidos con color son aceptados."""
        validator = ProjectTagEditValidator(from_tag="bug", to_tag="defect", color="#FF5733")
        assert validator.from_tag == "bug"
        assert validator.to_tag == "defect"
        assert validator.color == "#FF5733"

    def test_from_tag_empty_rejected(self) -> None:
        """Tag original vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectTagEditValidator(from_tag="", to_tag="defect")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_from_tag_whitespace_only_rejected(self) -> None:
        """Tag original solo con espacios es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectTagEditValidator(from_tag="   ", to_tag="defect")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_to_tag_empty_rejected(self) -> None:
        """Nuevo tag vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectTagEditValidator(from_tag="bug", to_tag="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_to_tag_whitespace_only_rejected(self) -> None:
        """Nuevo tag solo con espacios es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectTagEditValidator(from_tag="bug", to_tag="   ")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_color_invalid_rejected(self) -> None:
        """Color inválido es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProjectTagEditValidator(from_tag="bug", to_tag="defect", color="red")
        errors = exc_info.value.errors()
        assert any("hexadecimal" in str(e.get("msg", "")).lower() for e in errors)

    def test_tags_trimmed(self) -> None:
        """Tags con espacios son trimmeados."""
        validator = ProjectTagEditValidator(from_tag="  bug  ", to_tag="  defect  ")
        assert validator.from_tag == "bug"
        assert validator.to_tag == "defect"


# =============================================================================
# Tests de validadores de Epic
# =============================================================================


class TestEpicCreateValidator:
    """Tests para EpicCreateValidator."""

    def test_valid_epic_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = EpicCreateValidator(project_id=1, subject="Mi Épica")
        assert validator.project_id == 1
        assert validator.subject == "Mi Épica"

    def test_subject_empty_rejected(self) -> None:
        """Test 3.5.1: Asunto vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            EpicCreateValidator(project_id=1, subject="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_project_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de proyecto negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            EpicCreateValidator(project_id=-1, subject="Test")
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)

    def test_color_valid(self) -> None:
        """Color válido es aceptado."""
        validator = EpicCreateValidator(project_id=1, subject="Test", color="#FF5733")
        assert validator.color == "#FF5733"

    def test_color_invalid_rejected(self) -> None:
        """Color inválido es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            EpicCreateValidator(project_id=1, subject="Test", color="invalid")
        errors = exc_info.value.errors()
        assert any("hexadecimal" in str(e.get("msg", "")).lower() for e in errors)


class TestEpicUpdateValidator:
    """Tests para EpicUpdateValidator."""

    def test_valid_epic_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = EpicUpdateValidator(epic_id=1, subject="Actualizado")
        assert validator.epic_id == 1
        assert validator.subject == "Actualizado"

    def test_epic_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de épica negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            EpicUpdateValidator(epic_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de validadores de User Story
# =============================================================================


class TestUserStoryCreateValidator:
    """Tests para UserStoryCreateValidator."""

    def test_valid_userstory_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = UserStoryCreateValidator(project_id=1, subject="Mi Historia")
        assert validator.project_id == 1
        assert validator.subject == "Mi Historia"

    def test_subject_empty_rejected(self) -> None:
        """Test 3.5.1: Asunto vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserStoryCreateValidator(project_id=1, subject="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_project_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de proyecto negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserStoryCreateValidator(project_id=-1, subject="Test")
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


class TestUserStoryUpdateValidator:
    """Tests para UserStoryUpdateValidator."""

    def test_valid_userstory_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = UserStoryUpdateValidator(userstory_id=1, subject="Actualizado")
        assert validator.userstory_id == 1
        assert validator.subject == "Actualizado"

    def test_userstory_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de historia negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserStoryUpdateValidator(userstory_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de validadores de Issue
# =============================================================================


class TestIssueCreateValidator:
    """Tests para IssueCreateValidator."""

    def test_valid_issue_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = IssueCreateValidator(
            project_id=1, subject="Bug encontrado", type=1, priority=2, severity=3
        )
        assert validator.project_id == 1
        assert validator.subject == "Bug encontrado"
        assert validator.type == 1
        assert validator.priority == 2
        assert validator.severity == 3

    def test_subject_empty_rejected(self) -> None:
        """Test 3.5.1: Asunto vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            IssueCreateValidator(project_id=1, subject="", type=1, priority=2, severity=3)
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_required_ids_negative_rejected(self) -> None:
        """Test 3.5.2: IDs requeridos negativos son rechazados."""
        with pytest.raises(PydanticValidationError) as exc_info:
            IssueCreateValidator(project_id=-1, subject="Test", type=1, priority=2, severity=3)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)

    def test_due_date_valid(self) -> None:
        """Fecha límite válida es aceptada."""
        validator = IssueCreateValidator(
            project_id=1,
            subject="Test",
            type=1,
            priority=2,
            severity=3,
            due_date="2024-12-31",
        )
        assert validator.due_date == "2024-12-31"

    def test_due_date_invalid_rejected(self) -> None:
        """Fecha límite inválida es rechazada."""
        with pytest.raises(PydanticValidationError) as exc_info:
            IssueCreateValidator(
                project_id=1,
                subject="Test",
                type=1,
                priority=2,
                severity=3,
                due_date="invalid",
            )
        errors = exc_info.value.errors()
        assert any("formato" in str(e.get("msg", "")).lower() for e in errors)


class TestIssueUpdateValidator:
    """Tests para IssueUpdateValidator."""

    def test_valid_issue_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = IssueUpdateValidator(issue_id=1, subject="Actualizado")
        assert validator.issue_id == 1
        assert validator.subject == "Actualizado"

    def test_issue_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de issue negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            IssueUpdateValidator(issue_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de validadores de Task
# =============================================================================


class TestTaskCreateValidator:
    """Tests para TaskCreateValidator."""

    def test_valid_task_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = TaskCreateValidator(project_id=1, subject="Mi Tarea")
        assert validator.project_id == 1
        assert validator.subject == "Mi Tarea"

    def test_subject_empty_rejected(self) -> None:
        """Test 3.5.1: Asunto vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TaskCreateValidator(project_id=1, subject="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_project_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de proyecto negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TaskCreateValidator(project_id=-1, subject="Test")
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


class TestTaskUpdateValidator:
    """Tests para TaskUpdateValidator."""

    def test_valid_task_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = TaskUpdateValidator(task_id=1, subject="Actualizado")
        assert validator.task_id == 1
        assert validator.subject == "Actualizado"

    def test_task_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de tarea negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TaskUpdateValidator(task_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de validadores de Milestone
# =============================================================================


class TestMilestoneCreateValidator:
    """Tests para MilestoneCreateValidator."""

    def test_valid_milestone_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = MilestoneCreateValidator(
            project_id=1,
            name="Sprint 1",
            estimated_start="2024-01-01",
            estimated_finish="2024-01-15",
        )
        assert validator.project_id == 1
        assert validator.name == "Sprint 1"
        assert validator.estimated_start == "2024-01-01"
        assert validator.estimated_finish == "2024-01-15"

    def test_name_empty_rejected(self) -> None:
        """Test 3.5.1: Nombre vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MilestoneCreateValidator(
                project_id=1,
                name="",
                estimated_start="2024-01-01",
                estimated_finish="2024-01-15",
            )
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_dates_invalid_rejected(self) -> None:
        """Fechas inválidas son rechazadas."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MilestoneCreateValidator(
                project_id=1,
                name="Sprint 1",
                estimated_start="invalid",
                estimated_finish="2024-01-15",
            )
        errors = exc_info.value.errors()
        assert any("formato" in str(e.get("msg", "")).lower() for e in errors)

    def test_dates_order_rejected(self) -> None:
        """Fecha de inicio después de fin es rechazada."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MilestoneCreateValidator(
                project_id=1,
                name="Sprint 1",
                estimated_start="2024-01-20",
                estimated_finish="2024-01-15",
            )
        errors = exc_info.value.errors()
        assert any("anterior" in str(e.get("msg", "")).lower() for e in errors)

    def test_disponibility_negative_rejected(self) -> None:
        """Disponibilidad negativa es rechazada."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MilestoneCreateValidator(
                project_id=1,
                name="Sprint 1",
                estimated_start="2024-01-01",
                estimated_finish="2024-01-15",
                disponibility=-10.0,
            )
        errors = exc_info.value.errors()
        assert any("negativa" in str(e.get("msg", "")).lower() for e in errors)


class TestMilestoneUpdateValidator:
    """Tests para MilestoneUpdateValidator."""

    def test_valid_milestone_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = MilestoneUpdateValidator(milestone_id=1, name="Sprint 2")
        assert validator.milestone_id == 1
        assert validator.name == "Sprint 2"

    def test_milestone_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de milestone negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MilestoneUpdateValidator(milestone_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de validadores de Wiki
# =============================================================================


class TestWikiPageCreateValidator:
    """Tests para WikiPageCreateValidator."""

    def test_valid_wiki_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = WikiPageCreateValidator(
            project_id=1, slug="getting-started", content="# Inicio"
        )
        assert validator.project_id == 1
        assert validator.slug == "getting-started"
        assert validator.content == "# Inicio"

    def test_slug_empty_rejected(self) -> None:
        """Test 3.5.1: Slug vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WikiPageCreateValidator(project_id=1, slug="", content="Contenido")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_content_empty_rejected(self) -> None:
        """Test 3.5.1: Contenido vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WikiPageCreateValidator(project_id=1, slug="test", content="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_slug_invalid_format_rejected(self) -> None:
        """Slug con formato inválido es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WikiPageCreateValidator(project_id=1, slug="-invalid-slug-", content="Test")
        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestWikiPageUpdateValidator:
    """Tests para WikiPageUpdateValidator."""

    def test_valid_wiki_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = WikiPageUpdateValidator(wiki_id=1, content="Actualizado")
        assert validator.wiki_id == 1
        assert validator.content == "Actualizado"

    def test_wiki_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de wiki negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WikiPageUpdateValidator(wiki_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de validadores de Webhook
# =============================================================================


class TestWebhookCreateValidator:
    """Tests para WebhookCreateValidator."""

    def test_valid_webhook_create(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = WebhookCreateValidator(
            project_id=1, name="Slack", url="https://hooks.slack.com/xxx", key="secret"
        )
        assert validator.project_id == 1
        assert validator.name == "Slack"
        assert validator.url == "https://hooks.slack.com/xxx"
        assert validator.key == "secret"

    def test_name_empty_rejected(self) -> None:
        """Test 3.5.1: Nombre vacío es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WebhookCreateValidator(project_id=1, name="", url="https://example.com", key="secret")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)

    def test_url_invalid_rejected(self) -> None:
        """URL inválida es rechazada."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WebhookCreateValidator(project_id=1, name="Test", url="not-a-url", key="secret")
        errors = exc_info.value.errors()
        assert any("http" in str(e.get("msg", "")).lower() for e in errors)

    def test_key_empty_rejected(self) -> None:
        """Test 3.5.1: Clave vacía es rechazada."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WebhookCreateValidator(project_id=1, name="Test", url="https://example.com", key="")
        errors = exc_info.value.errors()
        assert any("vacío" in str(e.get("msg", "")).lower() for e in errors)


class TestWebhookUpdateValidator:
    """Tests para WebhookUpdateValidator."""

    def test_valid_webhook_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = WebhookUpdateValidator(webhook_id=1, name="Actualizado")
        assert validator.webhook_id == 1
        assert validator.name == "Actualizado"

    def test_webhook_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de webhook negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            WebhookUpdateValidator(webhook_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de validadores de Membership
# =============================================================================


class TestMembershipCreateValidator:
    """Tests para MembershipCreateValidator."""

    def test_valid_membership_with_username(self) -> None:
        """Test 3.5.3: Membresía con username es aceptada."""
        validator = MembershipCreateValidator(project_id=1, role=2, username="johndoe")
        assert validator.project_id == 1
        assert validator.role == 2
        assert validator.username == "johndoe"

    def test_valid_membership_with_email(self) -> None:
        """Test 3.5.3: Membresía con email es aceptada."""
        validator = MembershipCreateValidator(project_id=1, role=2, email="john@example.com")
        assert validator.project_id == 1
        assert validator.email == "john@example.com"

    def test_no_username_or_email_rejected(self) -> None:
        """Se requiere username o email."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MembershipCreateValidator(project_id=1, role=2)
        errors = exc_info.value.errors()
        assert any(
            "username" in str(e.get("msg", "")).lower() or "email" in str(e.get("msg", "")).lower()
            for e in errors
        )

    def test_email_invalid_rejected(self) -> None:
        """Email inválido es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MembershipCreateValidator(project_id=1, role=2, email="not-an-email")
        errors = exc_info.value.errors()
        assert any("email" in str(e.get("msg", "")).lower() for e in errors)


class TestMembershipUpdateValidator:
    """Tests para MembershipUpdateValidator."""

    def test_valid_membership_update(self) -> None:
        """Test 3.5.3: Datos válidos son aceptados."""
        validator = MembershipUpdateValidator(membership_id=1, role=3)
        assert validator.membership_id == 1
        assert validator.role == 3

    def test_membership_id_negative_rejected(self) -> None:
        """Test 3.5.2: ID de membresía negativo es rechazado."""
        with pytest.raises(PydanticValidationError) as exc_info:
            MembershipUpdateValidator(membership_id=-1)
        errors = exc_info.value.errors()
        assert any("positivo" in str(e.get("msg", "")).lower() for e in errors)


# =============================================================================
# Tests de la función validate_input
# =============================================================================


class TestValidateInput:
    """Tests para la función validate_input."""

    def test_valid_input_returns_dict(self) -> None:
        """Test 3.5.3: Entrada válida retorna diccionario validado."""
        data = {"name": "Mi Proyecto", "description": "Descripción"}
        result = validate_input(ProjectCreateValidator, data)
        assert result["name"] == "Mi Proyecto"
        assert result["description"] == "Descripción"

    def test_invalid_input_raises_validation_error(self) -> None:
        """Test 3.5.4: Entrada inválida lanza ValidationError de dominio."""
        data = {"name": ""}
        with pytest.raises(ValidationError) as exc_info:
            validate_input(ProjectCreateValidator, data)
        # Verificar que el mensaje es descriptivo
        assert "vacío" in str(exc_info.value).lower()

    def test_missing_required_field_raises_error(self) -> None:
        """Campo requerido faltante lanza error."""
        data = {"description": "Solo descripción"}
        with pytest.raises(ValidationError):
            validate_input(ProjectCreateValidator, data)

    def test_none_values_excluded(self) -> None:
        """Test 3.5.3: Valores None se excluyen del resultado."""
        data = {"project_id": 1, "name": None}
        result = validate_input(ProjectUpdateValidator, data)
        assert "name" not in result
        assert result["project_id"] == 1

    def test_error_messages_are_descriptive(self) -> None:
        """Test 3.5.4: Los mensajes de error son descriptivos en español."""
        data = {"project_id": -1}
        with pytest.raises(ValidationError) as exc_info:
            validate_input(ProjectUpdateValidator, data)
        error_msg = str(exc_info.value)
        # Verificar que contiene información útil
        assert "positivo" in error_msg.lower() or "project_id" in error_msg.lower()


# =============================================================================
# Tests de integración - Validación ocurre antes de llamada API
# =============================================================================


class TestValidationBeforeAPI:
    """
    Test 3.5.5: Verificar que la validación ocurre antes de cualquier
    llamada a la API.
    """

    def test_validation_is_synchronous(self) -> None:
        """La validación es síncrona y no requiere llamadas externas."""
        # Este test verifica que podemos validar sin ningún mock de API
        validator = ProjectCreateValidator(name="Test")
        assert validator.name == "Test"

    def test_validation_fails_fast(self) -> None:
        """La validación falla inmediatamente con datos inválidos."""
        import time

        start = time.time()
        with pytest.raises(PydanticValidationError):
            ProjectCreateValidator(name="")
        elapsed = time.time() - start
        # La validación debe ser casi instantánea (< 100ms)
        assert elapsed < 0.1

    def test_multiple_validation_errors_collected(self) -> None:
        """Múltiples errores de validación se recolectan."""
        with pytest.raises(PydanticValidationError) as exc_info:
            IssueCreateValidator(
                project_id=-1,
                subject="",
                type=0,
                priority=-1,
                severity=0,
            )
        errors = exc_info.value.errors()
        # Debe haber múltiples errores
        assert len(errors) >= 2
