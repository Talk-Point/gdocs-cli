"""Document domain models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Document:
    """A Google Docs document."""

    id: str
    title: str
    revision_id: str | None = None
    created_time: datetime | None = None
    modified_time: datetime | None = None
    body_content: list = field(default_factory=list)

    @property
    def url(self) -> str:
        """Get the document URL."""
        return f"https://docs.google.com/document/d/{self.id}/edit"


@dataclass
class DocumentSummary:
    """Document metadata for list operations."""

    id: str
    title: str
    modified_time: datetime | None = None

    @property
    def url(self) -> str:
        """Get the document URL."""
        return f"https://docs.google.com/document/d/{self.id}/edit"


@dataclass
class SharedDrive:
    """A Google Shared Drive (Team Drive)."""

    id: str
    name: str


@dataclass
class Folder:
    """A folder in Google Drive."""

    id: str
    name: str
    parent_id: str | None = None
