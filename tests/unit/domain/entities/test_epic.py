"""
Tests unitarios para la entidad Epic.
Implementa los tests para RF-001 a RF-007 y RNF-001, RNF-004.
TODOS LOS TESTS DEBEN FALLAR (ROJO) - NO HAY IMPLEMENTACIÓN AÚN.
"""

from datetime import datetime

import pytest


class TestEpicEntity:
    """Tests para la entidad Epic - RF-001 a RF-007"""

    def test_create_epic_with_minimal_data(self) -> None:
        """
        RF-002: El sistema debe permitir crear épicas con datos mínimos.

        Verifica que una épica se cree correctamente con solo
        los campos obligatorios (project, subject).
        """
        # Arrange
        from src.domain.entities.epic import Epic

        project_id = 309804
        subject = "Nueva Épica"

        # Act
        epic = Epic(project=project_id, subject=subject)

        # Assert
        assert epic.project == project_id
        assert epic.subject == subject
        assert epic.id is None  # ID se asigna al persistir
        assert epic.version is None  # Versión se asigna al persistir
        assert epic.color == "#A5694F"  # Color por defecto

    def test_create_epic_with_full_data(self, valid_epic_data) -> None:
        """
        RF-002: El sistema debe permitir crear épicas con todos los campos.

        Verifica que una épica se cree correctamente cuando se
        proporcionan todos los datos opcionales.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        # Act
        epic = Epic(**valid_epic_data)

        # Assert
        assert epic.project == valid_epic_data["project"]
        assert epic.subject == valid_epic_data["subject"]
        assert epic.description == valid_epic_data["description"]
        assert epic.color == valid_epic_data["color"]
        assert epic.assigned_to == valid_epic_data["assigned_to"]
        assert epic.status == valid_epic_data["status"]
        assert set(epic.tags) == set(valid_epic_data["tags"])  # Sets no tienen orden
        assert epic.client_requirement == valid_epic_data["client_requirement"]
        assert epic.team_requirement == valid_epic_data["team_requirement"]

    def test_epic_id_and_ref_properties(self) -> None:
        """
        RF-003, RF-004: El sistema debe manejar ID y ref de épicas.

        Verifica que las propiedades id y ref funcionen correctamente.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test")

        # Act & Assert
        # Antes de persistir
        assert epic.id is None
        assert epic.ref is None

        # Simular persistencia
        epic.id = 456789
        epic.ref = 5

        assert epic.id == 456789
        assert epic.ref == 5

    def test_epic_version_control(self) -> None:
        """
        RF-005, RF-006: El sistema debe manejar control de versión.

        Verifica el manejo de versiones para control de concurrencia.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test", version=1)

        # Act
        original_version = epic.version
        epic.increment_version()

        # Assert
        assert epic.version == original_version + 1

        # Test version validation
        with pytest.raises(ValueError, match="Version conflict"):
            epic.validate_version_match(original_version)

    def test_epic_version_match_success(self, valid_epic_data) -> None:
        """
        Test that validate_version_match succeeds when versions match.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(**valid_epic_data)
        epic.version = 5

        # Act & Assert - should not raise
        epic.validate_version_match(5)  # Versions match

    def test_epic_color_validation(self, invalid_epic_colors) -> None:
        """
        RNF-004: El sistema debe validar formato de colores.

        Verifica que solo se acepten colores en formato hexadecimal válido.
        """
        # Arrange
        from pydantic import ValidationError

        from src.domain.entities.epic import Epic

        # Act & Assert
        for invalid_color in invalid_epic_colors:
            with pytest.raises(ValidationError, match="Invalid color format"):
                Epic(project=309804, subject="Test", color=invalid_color)

    def test_epic_subject_validation(self, invalid_epic_subjects) -> None:
        """
        RNF-004: El sistema debe validar el título de las épicas.

        Verifica validaciones del campo subject.
        """
        # Arrange
        from pydantic import ValidationError

        from src.domain.entities.epic import Epic

        # Act & Assert
        for invalid_subject in invalid_epic_subjects:
            with pytest.raises(ValidationError):
                Epic(project=309804, subject=invalid_subject)

    def test_epic_tags_handling(self) -> None:
        """
        RF-001, RF-002: El sistema debe manejar tags correctamente.

        Verifica el manejo de tags como lista.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        tags = ["auth", "security", "v2"]

        # Act
        epic = Epic(project=309804, subject="Test", tags=tags)

        # Assert
        assert set(epic.tags) == set(tags)
        assert isinstance(epic.tags, list)
        assert len(epic.tags) == 3

        # Test adding tag
        epic.add_tag("new-feature")
        assert "new-feature" in epic.tags
        assert len(epic.tags) == 4

        # Test removing tag
        epic.remove_tag("security")
        assert "security" not in epic.tags
        assert len(epic.tags) == 3

    def test_epic_watchers_management(self) -> None:
        """
        RF-019, RF-020, RF-021: El sistema debe manejar observadores.

        Verifica el manejo de watchers de la épica.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test")
        user_id = 888691

        # Act & Assert - Initial state
        assert epic.watchers == []

        # Add watcher
        epic.add_watcher(user_id)
        assert user_id in epic.watchers
        assert len(epic.watchers) == 1

        # Try to add duplicate
        epic.add_watcher(user_id)
        assert len(epic.watchers) == 1  # Should not duplicate

        # Remove watcher
        epic.remove_watcher(user_id)
        assert user_id not in epic.watchers
        assert len(epic.watchers) == 0

        # Try to remove non-existent watcher
        with pytest.raises(ValueError, match="User is not watching"):
            epic.remove_watcher(user_id)

    def test_epic_voters_management(self) -> None:
        """
        RF-016, RF-017, RF-018: El sistema debe manejar votación.

        Verifica el manejo de votos de la épica.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test")
        user_id = 888691

        # Act & Assert - Initial state
        assert epic.total_voters == 0
        assert epic.voters == []

        # Upvote
        epic.add_voter(user_id)
        assert user_id in epic.voters
        assert epic.total_voters == 1

        # Try to vote again
        epic.add_voter(user_id)
        assert epic.total_voters == 1  # Should not duplicate

        # Downvote
        epic.remove_voter(user_id)
        assert user_id not in epic.voters
        assert epic.total_voters == 0

        # Try to downvote when not voted
        with pytest.raises(ValueError, match="User has not voted"):
            epic.remove_voter(user_id)

    def test_epic_requirements_flags(self) -> None:
        """
        RF-002: El sistema debe manejar flags de requerimientos.

        Verifica los flags client_requirement y team_requirement.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        # Act
        epic = Epic(project=309804, subject="Test", client_requirement=True, team_requirement=False)

        # Assert
        assert epic.client_requirement is True
        assert epic.team_requirement is False

        # Test toggling
        epic.toggle_client_requirement()
        assert epic.client_requirement is False

        epic.toggle_team_requirement()
        assert epic.team_requirement is True

    def test_epic_dates_handling(self) -> None:
        """
        RF-001: El sistema debe manejar fechas de creación y modificación.

        Verifica el manejo de timestamps.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test")

        # Act & Assert - Initial state
        assert epic.created_date is None
        assert epic.modified_date is None

        # Simulate persistence
        now = datetime.utcnow()
        epic.set_created_date(now)
        epic.set_modified_date(now)

        assert epic.created_date == now
        assert epic.modified_date == now

        # Update should change modified_date
        later = datetime.utcnow()
        epic.set_modified_date(later)
        assert epic.modified_date == later
        assert epic.modified_date > epic.created_date

    def test_epic_to_dict_serialization(self, valid_epic_data) -> None:
        """
        RNF-004: El sistema debe serializar épicas correctamente.

        Verifica la serialización a diccionario.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(**valid_epic_data)
        epic.id = 456789
        epic.ref = 5

        # Act
        epic_dict = epic.to_dict()

        # Assert
        assert isinstance(epic_dict, dict)
        assert epic_dict["id"] == 456789
        assert epic_dict["ref"] == 5
        assert epic_dict["project"] == valid_epic_data["project"]
        assert epic_dict["subject"] == valid_epic_data["subject"]
        assert epic_dict["color"] == valid_epic_data["color"]
        assert set(epic_dict["tags"]) == set(valid_epic_data["tags"])

    def test_epic_from_dict_deserialization(self, epic_response_data) -> None:
        """
        RNF-004: El sistema debe deserializar épicas correctamente.

        Verifica la creación desde diccionario (respuesta API).
        """
        # Arrange
        from src.domain.entities.epic import Epic

        # Act
        epic = Epic.from_dict(epic_response_data)

        # Assert
        assert epic.id == epic_response_data["id"]
        assert epic.ref == epic_response_data["ref"]
        assert epic.version == epic_response_data["version"]
        assert epic.subject == epic_response_data["subject"]
        assert epic.project == epic_response_data["project"]
        assert epic.watchers == epic_response_data["watchers"]
        assert epic.total_voters == epic_response_data["total_voters"]

    def test_epic_equality_comparison(self) -> None:
        """
        RNF-001: El sistema debe comparar épicas por ID.

        Verifica la comparación de igualdad entre épicas.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic1 = Epic(project=309804, subject="Epic 1")
        epic2 = Epic(project=309804, subject="Epic 2")
        epic3 = Epic(project=309804, subject="Epic 3")

        # Simular persistencia
        epic1.id = 456789
        epic2.id = 456789  # Mismo ID
        epic3.id = 456790  # Diferente ID

        # Act & Assert
        assert epic1 == epic2  # Mismo ID
        assert epic1 != epic3  # Diferente ID
        assert epic2 != epic3  # Diferente ID

        # Épicas sin ID no son iguales
        epic4 = Epic(project=309804, subject="Epic 4")
        epic5 = Epic(project=309804, subject="Epic 4")
        assert epic4 != epic5  # Sin ID, no son iguales

    def test_epic_hash_for_sets(self) -> None:
        """
        RNF-001: El sistema debe permitir épicas en sets/dicts.

        Verifica que las épicas sean hashables.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic1 = Epic(project=309804, subject="Epic 1")
        epic1.id = 456789

        epic2 = Epic(project=309804, subject="Epic 2")
        epic2.id = 456790

        # Act
        epic_set = {epic1, epic2}

        # Assert
        assert len(epic_set) == 2
        assert epic1 in epic_set
        assert epic2 in epic_set

    def test_epic_update_from_dict(self, epic_response_data) -> None:
        """
        RF-005, RF-006: El sistema debe actualizar épicas.

        Verifica la actualización parcial desde diccionario.
        """
        # Arrange
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Original")

        # Act
        update_data = {"subject": "Updated Subject", "status": 2, "color": "#FF0000"}
        epic.update_from_dict(update_data)

        # Assert
        assert epic.subject == "Updated Subject"
        assert epic.status == 2
        assert epic.color == "#FF0000"
        assert epic.project == 309804  # No debería cambiar

    def test_epic_increment_version_from_none(self) -> None:
        """Test increment_version when version is None (covers line 86)."""
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test")
        assert epic.version is None

        epic.increment_version()
        assert epic.version == 1

    def test_epic_add_empty_tag(self) -> None:
        """Test add_tag with empty string (covers line 106 exit branch)."""
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test", tags=["existing"])
        epic.add_tag("")
        epic.add_tag("   ")  # Whitespace-only tag
        assert epic.tags == ["existing"]  # No new tags added

    def test_epic_add_duplicate_tag(self) -> None:
        """Test add_tag with already existing tag (covers line 106 exit branch)."""
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test", tags=["existing"])
        epic.add_tag("existing")
        assert epic.tags == ["existing"]  # Still only one tag

    def test_epic_remove_nonexistent_tag(self) -> None:
        """Test remove_tag with non-existent tag (covers line 112 exit branch)."""
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test", tags=["existing"])
        epic.remove_tag("nonexistent")
        assert epic.tags == ["existing"]  # Nothing removed

    def test_epic_subject_whitespace_only(self) -> None:
        """Test that whitespace-only subject raises error (covers line 66)."""
        from pydantic import ValidationError

        from src.domain.entities.epic import Epic

        with pytest.raises(ValidationError):
            Epic(project=309804, subject="   ")

    def test_epic_equality_with_not_epic(self) -> None:
        """Test equality with non-Epic object."""
        from src.domain.entities.epic import Epic

        epic = Epic(project=309804, subject="Test")
        assert epic != "not an epic"
        assert epic != 123
        assert epic != None  # noqa: E711
