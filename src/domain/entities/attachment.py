"""
Attachment entity for Taiga MCP Server.
Represents a file attachment associated with an epic or other entity.
"""

from datetime import datetime
from typing import Any, ClassVar


class Attachment:
    """
    Attachment entity representing a file attached to an epic or other object.

    Attachments are files uploaded and associated with entities like epics,
    user stories, tasks, or issues. They have metadata like size, type, and URL.
    """

    # Maximum file size: 10MB
    MAX_FILE_SIZE: ClassVar[int] = 10 * 1024 * 1024  # 10MB in bytes

    # Allowed content types
    ALLOWED_CONTENT_TYPES: ClassVar[set[str]] = {
        "application/pdf",
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "text/plain",
        "text/csv",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/x-rar-compressed",
        "application/json",
        "application/xml",
        "text/xml",
        "text/html",
        "text/markdown",
    }

    def __init__(
        self,
        name: str,
        project: int,
        object_id: int,
        size: int | None = None,
        url: str | None = None,
        description: str | None = None,
        is_deprecated: bool = False,
        content_type: str | None = None,
        id: int | None = None,
        created_date: datetime | None = None,
        modified_date: datetime | None = None,
        owner: int | None = None,
        sha1: str | None = None,
    ):
        """
        Initialize an Attachment entity.

        Args:
            name: File name (required)
            project: Project ID where the attachment belongs
            object_id: ID of the object (epic, user story, etc.) this is attached to
            size: File size in bytes
            url: URL to access the attachment
            description: Description of the attachment
            is_deprecated: Flag indicating if the attachment is deprecated
            content_type: MIME type of the file
            id: Unique identifier (None for new attachments)
            created_date: Creation timestamp
            modified_date: Last modification timestamp
            owner: User ID who uploaded the attachment
            sha1: SHA1 hash of the file content
        """
        # Validate required fields
        if not name or not name.strip():
            from src.domain.exceptions import ValidationError

            raise ValidationError("File name is required")

        if len(name) > 255:
            from src.domain.exceptions import ValidationError

            raise ValidationError("File name too long")

        # Validate forbidden characters in filename
        forbidden_chars = ["/", "\\", "\0", ".."]
        for char in forbidden_chars:
            if char in name:
                from src.domain.exceptions import ValidationError

                raise ValidationError(f"Invalid name: Forbidden character '{char}' in filename")

        # Validate size if provided
        if size is not None:
            if size < 0:
                from src.domain.exceptions import ValidationError

                raise ValidationError("Invalid size: Size cannot be negative")
            if size > self.MAX_FILE_SIZE:
                from src.domain.exceptions import ValidationError

                raise ValidationError(
                    f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE} bytes"
                )

        # Validate content type if provided
        if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
            from src.domain.exceptions import ValidationError

            raise ValidationError(f"File type not allowed: {content_type}")

        # Core attributes - Make file properties immutable
        self._id: int | None = id
        self._name: str = name
        self._project: int = project
        self._object_id: int = object_id
        self._size: int | None = size
        self._url: str | None = url
        self._description: str | None = description
        self._is_deprecated: bool = is_deprecated
        self._content_type: str | None = content_type
        self._owner: int | None = owner
        self._sha1: str | None = sha1

        # Timestamps
        self._created_date: datetime | None = created_date
        self._modified_date: datetime | None = modified_date

        # Deletion tracking
        self._deletion_date: datetime | None = None

    # Properties for read-only access to immutable file attributes
    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, value: int | None) -> None:
        self._id = value

    @property
    def name(self) -> str | None:
        return self._name

    @name.setter
    def name(self, _value: str) -> None:
        raise AttributeError("Cannot modify file")

    @property
    def project(self) -> Any:
        return self._project

    @project.setter
    def project(self, value: int) -> None:
        self._project = value

    @property
    def object_id(self) -> int:
        return self._object_id

    @object_id.setter
    def object_id(self, value: int) -> None:
        self._object_id = value

    @property
    def size(self) -> int | None:
        return self._size

    @size.setter
    def size(self, _value: int) -> None:
        raise AttributeError("Cannot modify file")

    @property
    def url(self) -> str | None:
        return self._url

    @url.setter
    def url(self, value: str | None) -> None:
        self._url = value

    @property
    def description(self) -> str | None:
        return self._description

    @description.setter
    def description(self, value: str | None) -> None:
        self._description = value
        self._modified_date = datetime.utcnow()

    @property
    def is_deprecated(self) -> bool:
        return self._is_deprecated

    @is_deprecated.setter
    def is_deprecated(self, value: bool) -> None:
        self._is_deprecated = value
        self._modified_date = datetime.utcnow()

    @property
    def content_type(self) -> str | None:
        return self._content_type

    @content_type.setter
    def content_type(self, value: str | None) -> None:
        self._content_type = value

    @property
    def owner(self) -> int | None:
        return self._owner

    @owner.setter
    def owner(self, value: int | None) -> None:
        self._owner = value

    @property
    def sha1(self) -> str | None:
        return self._sha1

    @sha1.setter
    def sha1(self, value: str | None) -> None:
        self._sha1 = value

    @property
    def created_date(self) -> Any:
        return self._created_date

    @created_date.setter
    def created_date(self, value: datetime | None) -> None:
        self._created_date = value

    @property
    def modified_date(self) -> Any:
        return self._modified_date

    @modified_date.setter
    def modified_date(self, value: datetime | None) -> None:
        self._modified_date = value

    @property
    def deletion_date(self) -> Any:
        return self._deletion_date

    @property
    def is_marked_for_deletion(self) -> bool:
        """Check if attachment is marked for deletion."""
        return self._deletion_date is not None

    def deprecate(self) -> None:
        """Mark the attachment as deprecated."""
        self._is_deprecated = True
        self._modified_date = datetime.utcnow()

    def undeprecate(self) -> None:
        """Mark the attachment as not deprecated."""
        self._is_deprecated = False
        self._modified_date = datetime.utcnow()

    def unmark_deprecated(self) -> None:
        """Unmark the attachment as deprecated (alias for undeprecate)."""
        self.undeprecate()

    def mark_as_deprecated(self) -> None:
        """Mark the attachment as deprecated (alias for deprecate)."""
        self.deprecate()

    def mark_for_deletion(self) -> None:
        """Mark the attachment for deletion by deprecating it."""
        self._is_deprecated = True
        self._deletion_date = datetime.utcnow()
        self._modified_date = datetime.utcnow()

    def set_created_date(self, date: datetime) -> None:
        """Set the creation date."""
        self.created_date = date

    def generate_url(self, base_url: str | None = None) -> str:
        """
        Generate URL for the attachment.

        Args:
            base_url: Base URL of the Taiga instance (optional)

        Returns:
            Full URL to the attachment
        """
        if self.url:
            return self.url

        # Use a default base URL if not provided
        if base_url is None:
            base_url = "https://api.taiga.io"

        if self.id:
            self._url = f"{base_url}/attachments/{self.id}/{self.name}"
            return self._url
        return ""

    def update_description(self, description: str) -> None:
        """
        Update the attachment description.

        Args:
            description: New description
        """
        self._description = description
        self._modified_date = datetime.utcnow()

    def get_size_mb(self) -> float:
        """
        Get file size in megabytes.

        Returns:
            File size in MB, or 0 if size is not set
        """
        if self.size is None:
            return 0.0
        return self.size / (1024 * 1024)

    def is_image(self) -> bool:
        """
        Check if the attachment is an image.

        Returns:
            True if the content type indicates an image, False otherwise
        """
        if not self.content_type:
            return False
        return self.content_type.startswith("image/")

    def is_document(self) -> bool:
        """
        Check if the attachment is a document.

        Returns:
            True if the content type indicates a document, False otherwise
        """
        if not self.content_type:
            return False

        document_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument",
            "application/vnd.ms-",
            "text/",
        ]

        return any(self.content_type.startswith(dtype) for dtype in document_types)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert attachment to dictionary representation.

        Returns:
            Dictionary with all attachment attributes
        """
        return {
            "id": self.id,
            "name": self.name,
            "project": self.project,
            "object_id": self.object_id,
            "size": self.size,
            "url": self.url,
            "description": self.description,
            "is_deprecated": self.is_deprecated,
            "content_type": self.content_type,
            "owner": self.owner,
            "sha1": self.sha1,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "modified_date": self.modified_date.isoformat() if self.modified_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Attachment":
        """
        Create an Attachment instance from a dictionary.

        Args:
            data: Dictionary with attachment data

        Returns:
            Attachment instance
        """
        # Parse dates if they're strings
        created_date = data.get("created_date")
        if created_date and isinstance(created_date, str):
            created_date = datetime.fromisoformat(created_date.replace("Z", "+00:00"))

        modified_date = data.get("modified_date")
        if modified_date and isinstance(modified_date, str):
            modified_date = datetime.fromisoformat(modified_date.replace("Z", "+00:00"))

        # Validate required fields
        if "project" not in data or data["project"] is None:
            from src.domain.exceptions import ValidationError

            raise ValidationError("project is required")
        if "object_id" not in data or data["object_id"] is None:
            from src.domain.exceptions import ValidationError

            raise ValidationError("object_id is required")

        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            project=data["project"],
            object_id=data["object_id"],
            size=data.get("size"),
            url=data.get("url"),
            description=data.get("description"),
            is_deprecated=data.get("is_deprecated", False),
            content_type=data.get("content_type"),
            owner=data.get("owner"),
            sha1=data.get("sha1"),
            created_date=created_date,
            modified_date=modified_date,
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare attachments by ID.

        Two attachments are equal if they have the same ID.
        Attachments without ID are never equal.
        """
        if not isinstance(other, Attachment):
            return False
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Hash based on ID for use in sets/dicts.

        Returns:
            Hash of the attachment ID
        """
        if self.id is None:
            # For attachments without ID, use object identity
            return id(self)
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Attachment(id={self.id}, name='{self.name}', "
            f"size={self.size}, object_id={self.object_id})"
        )
