"""
Tests unitarios para la entidad RelatedUserStory.
Implementa los tests para RF-009 a RF-014.
TODOS LOS TESTS DEBEN FALLAR (ROJO) - NO HAY IMPLEMENTACIÓN AÚN.
"""

import pytest


class TestRelatedUserStoryEntity:
    """Tests para la entidad RelatedUserStory - RF-009 a RF-014"""

    def test_create_related_userstory(self) -> None:
        """
        RF-010: El sistema debe crear relaciones epic-userstory.

        Verifica que una relación se cree correctamente.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        epic_id = 456789
        userstory_id = 123456
        order = 1

        # Act
        relation = RelatedUserStory(epic=epic_id, user_story=userstory_id, order=order)

        # Assert
        assert relation.epic == epic_id
        assert relation.user_story == userstory_id
        assert relation.order == order
        assert relation.id is None  # Se asigna al persistir

    def test_related_userstory_with_full_data(self, related_userstory_data) -> None:
        """
        RF-009: El sistema debe manejar datos completos de relación.

        Verifica que se manejen todos los datos de la relación.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        # Act
        relation = RelatedUserStory.from_dict(related_userstory_data)

        # Assert
        assert relation.id == related_userstory_data["id"]
        assert relation.epic == related_userstory_data["epic"]
        assert relation.order == related_userstory_data["order"]
        assert relation.user_story_details == related_userstory_data["user_story"]

    def test_related_userstory_order_validation(self) -> None:
        """
        RF-012: El sistema debe validar el orden de las relaciones.

        Verifica que el orden sea un valor válido.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory
        from src.domain.exceptions import ValidationError

        # Act & Assert - Orden válido
        relation = RelatedUserStory(epic=456789, user_story=123456, order=1)
        assert relation.order == 1

        # Orden negativo no válido
        with pytest.raises(ValidationError, match="Order must be positive"):
            RelatedUserStory(epic=456789, user_story=123456, order=-1)

        # Orden cero es válido (sin orden específico)
        relation_no_order = RelatedUserStory(epic=456789, user_story=123456, order=0)
        assert relation_no_order.order == 0

    def test_related_userstory_update_order(self) -> None:
        """
        RF-012: El sistema debe permitir actualizar el orden.

        Verifica la actualización del campo order.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(epic=456789, user_story=123456, order=1)

        # Act
        relation.update_order(5)

        # Assert
        assert relation.order == 5

        # Test invalid order update
        from src.domain.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Order must be positive"):
            relation.update_order(-1)

    def test_related_userstory_same_project_validation(self) -> None:
        """
        RF-010: Las relaciones deben ser del mismo proyecto.

        Verifica que epic y userstory pertenezcan al mismo proyecto.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        epic_project = 309804
        userstory_project = 309805  # Diferente proyecto

        # Act & Assert
        # Esto debería validarse a nivel de caso de uso, no de entidad
        # La entidad solo almacena IDs, la validación es responsabilidad del dominio
        relation = RelatedUserStory(
            epic=456789,
            user_story=123456,
            order=1,
            epic_project=epic_project,
            userstory_project=userstory_project,
        )

        assert not relation.is_same_project()

    def test_related_userstory_to_dict(self) -> None:
        """
        RNF-004: El sistema debe serializar relaciones correctamente.

        Verifica la serialización a diccionario.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(epic=456789, user_story=123456, order=2)
        relation.id = 123

        # Act
        relation_dict = relation.to_dict()

        # Assert
        assert isinstance(relation_dict, dict)
        assert relation_dict["id"] == 123
        assert relation_dict["epic"] == 456789
        assert relation_dict["user_story"] == 123456
        assert relation_dict["order"] == 2

    def test_related_userstory_from_dict(self, related_userstory_data) -> None:
        """
        RNF-004: El sistema debe deserializar relaciones correctamente.

        Verifica la creación desde diccionario.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        # Act
        relation = RelatedUserStory.from_dict(related_userstory_data)

        # Assert
        assert relation.id == 123
        assert relation.epic == 456789
        assert relation.order == 1
        assert relation.user_story_details["id"] == 123456
        assert relation.user_story_details["subject"] == "Login de usuarios"

    def test_related_userstory_equality(self) -> None:
        """
        RNF-001: El sistema debe comparar relaciones por ID.

        Verifica la comparación de igualdad entre relaciones.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        rel1 = RelatedUserStory(epic=456789, user_story=123456, order=1)
        rel2 = RelatedUserStory(epic=456789, user_story=123456, order=1)
        rel3 = RelatedUserStory(epic=456789, user_story=123457, order=1)

        # Simular persistencia
        rel1.id = 100
        rel2.id = 100  # Mismo ID
        rel3.id = 101  # Diferente ID

        # Act & Assert
        assert rel1 == rel2  # Mismo ID
        assert rel1 != rel3  # Diferente ID

        # Sin ID, comparar por epic y user_story
        rel4 = RelatedUserStory(epic=456789, user_story=123456, order=1)
        rel5 = RelatedUserStory(epic=456789, user_story=123456, order=2)
        assert rel4 == rel5  # Misma epic y user_story, diferente orden

    def test_related_userstory_duplicate_detection(self) -> None:
        """
        RF-010, RF-014: El sistema debe evitar duplicados.

        Verifica la detección de relaciones duplicadas.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        rel1 = RelatedUserStory(epic=456789, user_story=123456, order=1)
        rel2 = RelatedUserStory(epic=456789, user_story=123456, order=2)
        rel3 = RelatedUserStory(epic=456789, user_story=123457, order=1)

        # Act & Assert
        assert rel1.is_duplicate_of(rel2)  # Misma epic y user_story
        assert not rel1.is_duplicate_of(rel3)  # Diferente user_story

    def test_related_userstory_bulk_creation(self, bulk_userstories_ids) -> None:
        """
        RF-014: El sistema debe crear relaciones en bulk.

        Verifica la creación masiva de relaciones.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        epic_id = 456789

        # Act
        relations = [
            RelatedUserStory(epic=epic_id, user_story=us_id, order=idx + 1)
            for idx, us_id in enumerate(bulk_userstories_ids)
        ]

        # Assert
        assert len(relations) == len(bulk_userstories_ids)
        for idx, relation in enumerate(relations):
            assert relation.epic == epic_id
            assert relation.user_story == bulk_userstories_ids[idx]
            assert relation.order == idx + 1

    def test_related_userstory_ordering(self) -> None:
        """
        RF-009: El sistema debe respetar el orden de las relaciones.

        Verifica el ordenamiento de relaciones.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        rel1 = RelatedUserStory(epic=456789, user_story=123456, order=3)
        rel2 = RelatedUserStory(epic=456789, user_story=123457, order=1)
        rel3 = RelatedUserStory(epic=456789, user_story=123458, order=2)

        # Act
        relations = [rel1, rel2, rel3]
        sorted_relations = sorted(relations, key=lambda r: r.order)

        # Assert
        assert sorted_relations[0] == rel2  # order=1
        assert sorted_relations[1] == rel3  # order=2
        assert sorted_relations[2] == rel1  # order=3

    def test_related_userstory_without_order(self) -> None:
        """
        RF-010: El sistema debe permitir relaciones sin orden específico.

        Verifica que order sea opcional.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        # Act
        relation = RelatedUserStory(
            epic=456789,
            user_story=123456,
            # No especificamos order
        )

        # Assert
        assert relation.order == 0  # Valor por defecto

    def test_related_userstory_hash(self) -> None:
        """
        RNF-001: Las relaciones deben ser hashables.

        Verifica que las relaciones puedan usarse en sets.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        rel1 = RelatedUserStory(epic=456789, user_story=123456, order=1)
        rel1.id = 100

        rel2 = RelatedUserStory(epic=456789, user_story=123457, order=2)
        rel2.id = 101

        # Act
        relation_set = {rel1, rel2}

        # Assert
        assert len(relation_set) == 2
        assert rel1 in relation_set
        assert rel2 in relation_set

    def test_related_userstory_str_representation(self) -> None:
        """
        RNF-006: Las relaciones deben tener representación legible.

        Verifica la representación string de la relación.
        """
        # Arrange
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(epic=456789, user_story=123456, order=1)
        relation.id = 123

        # Act
        str_repr = str(relation)

        # Assert
        assert "RelatedUserStory" in str_repr
        assert "123" in str_repr  # ID
        assert "456789" in str_repr  # Epic ID
        assert "123456" in str_repr  # UserStory ID

    def test_related_userstory_to_dict_with_details(self) -> None:
        """Test to_dict with user_story_details populated."""
        from src.domain.entities.related_userstory import RelatedUserStory

        details = {"id": 123456, "subject": "Test Story", "project": 1}
        relation = RelatedUserStory(
            epic=456789,
            user_story=123456,
            order=1,
            user_story_details=details,
            epic_project=1,
            userstory_project=2,
        )
        relation.id = 100

        result = relation.to_dict()

        assert result["user_story_details"] == details
        assert result["epic_project"] == 1
        assert result["userstory_project"] == 2

    def test_related_userstory_to_dict_without_optional_fields(self) -> None:
        """Test to_dict without optional fields."""
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(epic=456789, user_story=123456, order=1)

        result = relation.to_dict()

        assert "user_story_details" not in result
        assert "epic_project" not in result
        assert "userstory_project" not in result

    def test_related_userstory_is_same_project_both_none(self) -> None:
        """Test is_same_project returns True when both projects are None."""
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(epic=456789, user_story=123456, order=1)

        assert relation.is_same_project() is True

    def test_related_userstory_is_same_project_one_none(self) -> None:
        """Test is_same_project returns True when one project is None."""
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(
            epic=456789, user_story=123456, order=1, epic_project=1, userstory_project=None
        )

        assert relation.is_same_project() is True

    def test_related_userstory_is_same_project_equal(self) -> None:
        """Test is_same_project returns True when projects are equal."""
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(
            epic=456789, user_story=123456, order=1, epic_project=1, userstory_project=1
        )

        assert relation.is_same_project() is True

    def test_related_userstory_from_dict_with_nested_user_story(self) -> None:
        """Test from_dict with user_story as nested dict."""
        from src.domain.entities.related_userstory import RelatedUserStory

        data = {
            "id": 100,
            "epic": 456789,
            "user_story": {"id": 123456, "subject": "Test", "project": 2},
            "order": 1,
        }

        relation = RelatedUserStory.from_dict(data)

        assert relation.id == 100
        assert relation.epic == 456789
        assert relation.user_story == 123456
        assert relation.userstory_project == 2

    def test_related_userstory_from_dict_missing_epic(self) -> None:
        """Test from_dict raises error when epic is missing."""
        from src.domain.entities.related_userstory import RelatedUserStory
        from src.domain.exceptions import ValidationError

        data = {"id": 100, "user_story": 123456, "order": 1}

        with pytest.raises(ValidationError, match="epic is required"):
            RelatedUserStory.from_dict(data)

    def test_related_userstory_from_dict_missing_user_story(self) -> None:
        """Test from_dict raises error when user_story is missing."""
        from src.domain.entities.related_userstory import RelatedUserStory
        from src.domain.exceptions import ValidationError

        data = {"id": 100, "epic": 456789, "order": 1}

        with pytest.raises(ValidationError, match="user_story is required"):
            RelatedUserStory.from_dict(data)

    def test_related_userstory_from_dict_with_user_story_id_field(self) -> None:
        """Test from_dict with user_story_id field fallback."""
        from src.domain.entities.related_userstory import RelatedUserStory

        data = {"id": 100, "epic": 456789, "user_story_id": 123456, "order": 1}

        relation = RelatedUserStory.from_dict(data)

        assert relation.user_story == 123456

    def test_related_userstory_equality_not_related_userstory(self) -> None:
        """Test equality with non-RelatedUserStory object."""
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(epic=456789, user_story=123456, order=1)

        assert relation != "not a relation"
        assert relation != 123
        assert relation != None  # noqa: E711

    def test_related_userstory_hash_without_id(self) -> None:
        """Test hash without ID uses epic and user_story combo."""
        from src.domain.entities.related_userstory import RelatedUserStory

        relation = RelatedUserStory(epic=456789, user_story=123456, order=1)

        assert hash(relation) == hash((456789, 123456))
