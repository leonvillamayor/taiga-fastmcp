"""
Tests unitarios para la entidad Attachment.
Implementa los tests para RF-022 a RF-026.
TODOS LOS TESTS DEBEN FALLAR (ROJO) - NO HAY IMPLEMENTACIÓN AÚN.
"""

from datetime import datetime

import pytest


class TestAttachmentEntity:
    """Tests para la entidad Attachment - RF-022 a RF-026"""

    def test_create_attachment_minimal(self) -> None:
        """
        RF-023: El sistema debe crear adjuntos con datos mínimos.

        Verifica la creación de un adjunto con campos obligatorios.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        name = "requirements.pdf"
        project = 309804
        object_id = 456789  # Epic ID

        # Act
        attachment = Attachment(name=name, project=project, object_id=object_id)

        # Assert
        assert attachment.name == name
        assert attachment.project == project
        assert attachment.object_id == object_id
        assert attachment.id is None  # Se asigna al persistir
        assert attachment.is_deprecated is False  # Por defecto

    def test_create_attachment_with_full_data(self, epic_attachment_data) -> None:
        """
        RF-023: El sistema debe crear adjuntos con todos los campos.

        Verifica la creación con datos completos.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        # Act
        attachment = Attachment.from_dict(epic_attachment_data)

        # Assert
        assert attachment.id == epic_attachment_data["id"]
        assert attachment.name == epic_attachment_data["name"]
        assert attachment.size == epic_attachment_data["size"]
        assert attachment.url == epic_attachment_data["url"]
        assert attachment.description == epic_attachment_data["description"]
        assert attachment.is_deprecated == epic_attachment_data["is_deprecated"]
        assert attachment.object_id == epic_attachment_data["object_id"]
        assert attachment.project == epic_attachment_data["project"]
        assert attachment.content_type == epic_attachment_data["content_type"]

    def test_attachment_size_validation(self) -> None:
        """
        RF-023: El sistema debe validar tamaño de archivos.

        Verifica la validación del tamaño máximo.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        max_size = 10 * 1024 * 1024  # 10MB

        # Act & Assert - Tamaño válido
        attachment = Attachment(
            name="file.pdf", project=309804, object_id=456789, size=max_size - 1
        )
        assert attachment.size < max_size

        # Tamaño excedido
        with pytest.raises(ValidationError, match="File size exceeds maximum"):
            Attachment(name="file.pdf", project=309804, object_id=456789, size=max_size + 1)

    def test_attachment_content_type_validation(self) -> None:
        """
        RF-023: El sistema debe validar tipos de archivo.

        Verifica la validación de tipos permitidos.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

        # Act & Assert - Tipos válidos
        for content_type in allowed_types:
            attachment = Attachment(
                name="file", project=309804, object_id=456789, content_type=content_type
            )
            assert attachment.content_type == content_type

        # Tipo no permitido
        with pytest.raises(ValidationError, match="File type not allowed"):
            Attachment(
                name="file.exe",
                project=309804,
                object_id=456789,
                content_type="application/x-executable",
            )

    def test_attachment_name_validation(self) -> None:
        """
        RF-023: El sistema debe validar nombres de archivo.

        Verifica la validación del nombre.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        # Act & Assert - Nombre válido
        attachment = Attachment(name="valid-file_name.pdf", project=309804, object_id=456789)
        assert attachment.name == "valid-file_name.pdf"

        # Nombre vacío
        with pytest.raises(ValidationError, match="File name is required"):
            Attachment(name="", project=309804, object_id=456789)

        # Nombre muy largo
        long_name = "a" * 256 + ".pdf"
        with pytest.raises(ValidationError, match="File name too long"):
            Attachment(name=long_name, project=309804, object_id=456789)

    def test_attachment_update_metadata(self) -> None:
        """
        RF-025: El sistema debe actualizar metadata de adjuntos.

        Verifica la actualización de descripción y deprecated.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="file.pdf",
            project=309804,
            object_id=456789,
            description="Original description",
            is_deprecated=False,
        )

        # Act
        attachment.update_description("Updated description")
        attachment.mark_as_deprecated()

        # Assert
        assert attachment.description == "Updated description"
        assert attachment.is_deprecated is True

        # Test unmarking deprecated
        attachment.unmark_deprecated()
        assert attachment.is_deprecated is False

    def test_attachment_cannot_update_file(self) -> None:
        """
        RF-025: No se debe poder cambiar el archivo, solo metadata.

        Verifica que el archivo no se pueda cambiar.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="original.pdf", project=309804, object_id=456789)
        attachment.id = 789012

        # Act & Assert
        # El nombre es inmutable después de crear
        with pytest.raises(AttributeError, match="Cannot modify file"):
            attachment.name = "new.pdf"

        # El tamaño es inmutable
        with pytest.raises(AttributeError, match="Cannot modify file"):
            attachment.size = 2048

    def test_attachment_url_generation(self) -> None:
        """
        RF-023: El sistema debe generar URL de acceso.

        Verifica la generación de URL para el archivo.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        attachment.id = 789012

        # Act
        url = attachment.generate_url()

        # Assert
        assert url is not None
        assert str(attachment.id) in url
        assert "attachments" in url
        assert url.startswith("https://")

    def test_attachment_to_dict(self, epic_attachment_data) -> None:
        """
        RNF-004: El sistema debe serializar adjuntos correctamente.

        Verifica la serialización a diccionario.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        attachment = Attachment.from_dict(epic_attachment_data)

        # Act
        attachment_dict = attachment.to_dict()

        # Assert
        assert isinstance(attachment_dict, dict)
        assert attachment_dict["id"] == epic_attachment_data["id"]
        assert attachment_dict["name"] == epic_attachment_data["name"]
        assert attachment_dict["size"] == epic_attachment_data["size"]
        assert attachment_dict["url"] == epic_attachment_data["url"]
        assert attachment_dict["description"] == epic_attachment_data["description"]
        assert attachment_dict["is_deprecated"] == epic_attachment_data["is_deprecated"]

    def test_attachment_from_dict(self, epic_attachment_data) -> None:
        """
        RNF-004: El sistema debe deserializar adjuntos correctamente.

        Verifica la creación desde diccionario.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        # Act
        attachment = Attachment.from_dict(epic_attachment_data)

        # Assert
        assert attachment.id == 789012
        assert attachment.name == "requirements.pdf"
        assert attachment.size == 1048576
        assert attachment.project == 309804
        assert attachment.object_id == 456789

    def test_attachment_equality(self) -> None:
        """
        RNF-001: El sistema debe comparar adjuntos por ID.

        Verifica la comparación de igualdad.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        att1 = Attachment(name="file1.pdf", project=309804, object_id=456789)
        att2 = Attachment(name="file2.pdf", project=309804, object_id=456789)

        # Simular persistencia
        att1.id = 789012
        att2.id = 789012  # Mismo ID

        # Act & Assert
        assert att1 == att2  # Mismo ID aunque diferente nombre

    def test_attachment_filter_by_epic(self) -> None:
        """
        RF-022: El sistema debe filtrar adjuntos por épica.

        Verifica el filtrado por object_id (epic_id).
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        epic_id = 456789
        attachments = [
            Attachment(name="file1.pdf", project=309804, object_id=epic_id),
            Attachment(name="file2.pdf", project=309804, object_id=epic_id),
            Attachment(name="file3.pdf", project=309804, object_id=999999),  # Otra épica
        ]

        # Act
        epic_attachments = [att for att in attachments if att.object_id == epic_id]

        # Assert
        assert len(epic_attachments) == 2
        assert all(att.object_id == epic_id for att in epic_attachments)

    def test_attachment_filter_by_project(self) -> None:
        """
        RF-022: El sistema debe filtrar adjuntos por proyecto.

        Verifica el filtrado por project.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        project_id = 309804
        attachments = [
            Attachment(name="file1.pdf", project=project_id, object_id=456789),
            Attachment(name="file2.pdf", project=project_id, object_id=456790),
            Attachment(name="file3.pdf", project=999999, object_id=456791),  # Otro proyecto
        ]

        # Act
        project_attachments = [att for att in attachments if att.project == project_id]

        # Assert
        assert len(project_attachments) == 2
        assert all(att.project == project_id for att in project_attachments)

    def test_attachment_created_date(self) -> None:
        """
        RF-023: El sistema debe registrar fecha de creación.

        Verifica el manejo de created_date.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)

        # Act
        now = datetime.utcnow()
        attachment.set_created_date(now)

        # Assert
        assert attachment.created_date == now

    def test_attachment_deletion(self) -> None:
        """
        RF-026: El sistema debe eliminar adjuntos.

        Verifica el marcado para eliminación.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        attachment.id = 789012

        # Act
        attachment.mark_for_deletion()

        # Assert
        assert attachment.is_marked_for_deletion is True
        assert attachment.deletion_date is not None

    def test_attachment_str_representation(self) -> None:
        """
        RNF-006: Los adjuntos deben tener representación legible.

        Verifica la representación string.
        """
        # Arrange
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="requirements.pdf", project=309804, object_id=456789)
        attachment.id = 789012

        # Act
        str_repr = str(attachment)

        # Assert
        assert "Attachment" in str_repr
        assert "789012" in str_repr  # ID
        assert "requirements.pdf" in str_repr  # Nombre

    def test_attachment_forbidden_characters_slash(self) -> None:
        """Test that forward slash in filename raises error."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Invalid name"):
            Attachment(name="path/file.pdf", project=309804, object_id=456789)

    def test_attachment_forbidden_characters_backslash(self) -> None:
        """Test that backslash in filename raises error."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Invalid name"):
            Attachment(name="path\\file.pdf", project=309804, object_id=456789)

    def test_attachment_forbidden_characters_null(self) -> None:
        """Test that null character in filename raises error."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Invalid name"):
            Attachment(name="file\0.pdf", project=309804, object_id=456789)

    def test_attachment_forbidden_characters_double_dot(self) -> None:
        """Test that double dot in filename raises error."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Invalid name"):
            Attachment(name="../file.pdf", project=309804, object_id=456789)

    def test_attachment_negative_size(self) -> None:
        """Test that negative size raises error."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Size cannot be negative"):
            Attachment(name="file.pdf", project=309804, object_id=456789, size=-1)

    def test_attachment_setters(self) -> None:
        """Test various property setters."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)

        # Test project setter
        attachment.project = 999
        assert attachment.project == 999

        # Test object_id setter
        attachment.object_id = 123
        assert attachment.object_id == 123

        # Test url setter
        attachment.url = "https://example.com/file.pdf"
        assert attachment.url == "https://example.com/file.pdf"

        # Test description setter
        attachment.description = "New description"
        assert attachment.description == "New description"

        # Test is_deprecated setter
        attachment.is_deprecated = True
        assert attachment.is_deprecated is True

        # Test content_type setter
        attachment.content_type = "application/pdf"
        assert attachment.content_type == "application/pdf"

        # Test owner setter
        attachment.owner = 42
        assert attachment.owner == 42

        # Test sha1 setter
        attachment.sha1 = "abc123"
        assert attachment.sha1 == "abc123"

        # Test modified_date setter
        from datetime import datetime

        now = datetime.utcnow()
        attachment.modified_date = now
        assert attachment.modified_date == now

    def test_attachment_generate_url_without_id(self) -> None:
        """Test URL generation without ID returns empty string."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        # No ID set

        url = attachment.generate_url()
        assert url == ""

    def test_attachment_generate_url_with_custom_base(self) -> None:
        """Test URL generation with custom base URL."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        attachment.id = 123

        url = attachment.generate_url(base_url="https://custom.taiga.io")
        assert url == "https://custom.taiga.io/attachments/123/file.pdf"

    def test_attachment_generate_url_already_set(self) -> None:
        """Test URL generation when URL is already set."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="file.pdf", project=309804, object_id=456789, url="https://existing.url/file.pdf"
        )
        attachment.id = 123

        url = attachment.generate_url()
        assert url == "https://existing.url/file.pdf"

    def test_attachment_get_size_mb_none(self) -> None:
        """Test get_size_mb returns 0 when size is None."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        assert attachment.get_size_mb() == 0.0

    def test_attachment_get_size_mb_with_size(self) -> None:
        """Test get_size_mb returns correct value."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="file.pdf", project=309804, object_id=456789, size=2 * 1024 * 1024
        )
        assert attachment.get_size_mb() == 2.0

    def test_attachment_is_image_without_content_type(self) -> None:
        """Test is_image returns False when content_type is None."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        assert attachment.is_image() is False

    def test_attachment_is_image_with_image_type(self) -> None:
        """Test is_image returns True for image content types."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="image.jpg", project=309804, object_id=456789, content_type="image/jpeg"
        )
        assert attachment.is_image() is True

    def test_attachment_is_image_with_non_image_type(self) -> None:
        """Test is_image returns False for non-image content types."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="doc.pdf", project=309804, object_id=456789, content_type="application/pdf"
        )
        assert attachment.is_image() is False

    def test_attachment_is_document_without_content_type(self) -> None:
        """Test is_document returns False when content_type is None."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        assert attachment.is_document() is False

    def test_attachment_is_document_with_pdf(self) -> None:
        """Test is_document returns True for PDF."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="doc.pdf", project=309804, object_id=456789, content_type="application/pdf"
        )
        assert attachment.is_document() is True

    def test_attachment_is_document_with_word(self) -> None:
        """Test is_document returns True for Word documents."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="doc.docx", project=309804, object_id=456789, content_type="application/msword"
        )
        assert attachment.is_document() is True

    def test_attachment_is_document_with_text(self) -> None:
        """Test is_document returns True for text files."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="readme.txt", project=309804, object_id=456789, content_type="text/plain"
        )
        assert attachment.is_document() is True

    def test_attachment_is_document_with_openxml(self) -> None:
        """Test is_document returns True for OpenXML documents."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="doc.docx",
            project=309804,
            object_id=456789,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert attachment.is_document() is True

    def test_attachment_is_document_with_ms_excel(self) -> None:
        """Test is_document returns True for MS Excel."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="sheet.xls",
            project=309804,
            object_id=456789,
            content_type="application/vnd.ms-excel",
        )
        assert attachment.is_document() is True

    def test_attachment_is_document_with_image(self) -> None:
        """Test is_document returns False for images."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="image.jpg", project=309804, object_id=456789, content_type="image/jpeg"
        )
        assert attachment.is_document() is False

    def test_attachment_from_dict_missing_project(self) -> None:
        """Test from_dict raises error when project is missing."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        data = {"name": "file.pdf", "object_id": 456789}

        with pytest.raises(ValidationError, match="project is required"):
            Attachment.from_dict(data)

    def test_attachment_from_dict_missing_object_id(self) -> None:
        """Test from_dict raises error when object_id is missing."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        data = {"name": "file.pdf", "project": 309804}

        with pytest.raises(ValidationError, match="object_id is required"):
            Attachment.from_dict(data)

    def test_attachment_from_dict_project_none(self) -> None:
        """Test from_dict raises error when project is None."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        data = {"name": "file.pdf", "project": None, "object_id": 456789}

        with pytest.raises(ValidationError, match="project is required"):
            Attachment.from_dict(data)

    def test_attachment_from_dict_object_id_none(self) -> None:
        """Test from_dict raises error when object_id is None."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        data = {"name": "file.pdf", "project": 309804, "object_id": None}

        with pytest.raises(ValidationError, match="object_id is required"):
            Attachment.from_dict(data)

    def test_attachment_from_dict_with_dates(self) -> None:
        """Test from_dict with date strings."""
        from src.domain.entities.attachment import Attachment

        data = {
            "name": "file.pdf",
            "project": 309804,
            "object_id": 456789,
            "created_date": "2024-01-15T10:30:00Z",
            "modified_date": "2024-01-16T11:45:00Z",
        }

        attachment = Attachment.from_dict(data)
        assert attachment.created_date is not None
        assert attachment.modified_date is not None

    def test_attachment_equality_both_no_id(self) -> None:
        """Test equality when both attachments have no ID."""
        from src.domain.entities.attachment import Attachment

        att1 = Attachment(name="file1.pdf", project=309804, object_id=456789)
        att2 = Attachment(name="file2.pdf", project=309804, object_id=456789)

        # Both have no ID, so they're not equal
        assert att1 != att2

    def test_attachment_equality_one_no_id(self) -> None:
        """Test equality when one attachment has no ID."""
        from src.domain.entities.attachment import Attachment

        att1 = Attachment(name="file1.pdf", project=309804, object_id=456789)
        att1.id = 123
        att2 = Attachment(name="file2.pdf", project=309804, object_id=456789)
        # att2 has no ID

        # One has ID, one doesn't
        assert att1 != att2

    def test_attachment_equality_not_attachment(self) -> None:
        """Test equality with non-Attachment object."""
        from src.domain.entities.attachment import Attachment

        att = Attachment(name="file.pdf", project=309804, object_id=456789)
        att.id = 123

        assert att != "not an attachment"
        assert att != 123
        assert att != None  # noqa: E711

    def test_attachment_hash_without_id(self) -> None:
        """Test hash without ID uses object identity."""
        from src.domain.entities.attachment import Attachment

        att1 = Attachment(name="file1.pdf", project=309804, object_id=456789)
        att2 = Attachment(name="file2.pdf", project=309804, object_id=456789)

        # Different objects should have different hashes
        assert hash(att1) != hash(att2)
        # Same object should have same hash
        assert hash(att1) == hash(att1)

    def test_attachment_hash_with_id(self) -> None:
        """Test hash with ID uses ID."""
        from src.domain.entities.attachment import Attachment

        att1 = Attachment(name="file1.pdf", project=309804, object_id=456789)
        att1.id = 123
        att2 = Attachment(name="file2.pdf", project=309804, object_id=456789)
        att2.id = 123

        # Same ID should have same hash
        assert hash(att1) == hash(att2)

    def test_attachment_deprecate_method(self) -> None:
        """Test deprecate method."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(name="file.pdf", project=309804, object_id=456789)
        assert attachment.is_deprecated is False

        attachment.deprecate()
        assert attachment.is_deprecated is True

    def test_attachment_undeprecate_method(self) -> None:
        """Test undeprecate method."""
        from src.domain.entities.attachment import Attachment

        attachment = Attachment(
            name="file.pdf", project=309804, object_id=456789, is_deprecated=True
        )
        assert attachment.is_deprecated is True

        attachment.undeprecate()
        assert attachment.is_deprecated is False

    def test_attachment_whitespace_name(self) -> None:
        """Test that whitespace-only name raises error."""
        from src.domain.entities.attachment import Attachment
        from src.domain.exceptions import ValidationError

        with pytest.raises(ValidationError, match="File name is required"):
            Attachment(name="   ", project=309804, object_id=456789)
