"""Tests for domain models."""

from gdocs_cli.models.document import Document, DocumentSummary, Folder, SharedDrive
from gdocs_cli.models.element import (
    Alignment,
    NamedStyleType,
    ParagraphStyle,
    Table,
    TextStyle,
)


class TestDocument:
    """Tests for Document model."""

    def test_document_url(self):
        """Test document URL generation."""
        doc = Document(id="abc123", title="Test Doc")
        assert doc.url == "https://docs.google.com/document/d/abc123/edit"

    def test_document_defaults(self):
        """Test document default values."""
        doc = Document(id="abc123", title="Test Doc")
        assert doc.revision_id is None
        assert doc.created_time is None
        assert doc.modified_time is None
        assert doc.body_content == []


class TestDocumentSummary:
    """Tests for DocumentSummary model."""

    def test_summary_url(self):
        """Test summary URL generation."""
        summary = DocumentSummary(id="xyz789", title="Summary Doc")
        assert summary.url == "https://docs.google.com/document/d/xyz789/edit"


class TestSharedDrive:
    """Tests for SharedDrive model."""

    def test_shared_drive_creation(self):
        """Test shared drive creation."""
        drive = SharedDrive(id="drive123", name="Team Drive")
        assert drive.id == "drive123"
        assert drive.name == "Team Drive"


class TestFolder:
    """Tests for Folder model."""

    def test_folder_creation(self):
        """Test folder creation."""
        folder = Folder(id="folder123", name="My Folder")
        assert folder.id == "folder123"
        assert folder.name == "My Folder"
        assert folder.parent_id is None

    def test_folder_with_parent(self):
        """Test folder with parent."""
        folder = Folder(id="folder123", name="Subfolder", parent_id="parent456")
        assert folder.parent_id == "parent456"


class TestTextStyle:
    """Tests for TextStyle model."""

    def test_text_style_defaults(self):
        """Test text style default values."""
        style = TextStyle()
        assert style.bold is False
        assert style.italic is False
        assert style.underline is False
        assert style.font_size is None

    def test_text_style_custom(self):
        """Test text style with custom values."""
        style = TextStyle(bold=True, italic=True, font_size=14.0)
        assert style.bold is True
        assert style.italic is True
        assert style.font_size == 14.0


class TestParagraphStyle:
    """Tests for ParagraphStyle model."""

    def test_paragraph_style_defaults(self):
        """Test paragraph style defaults."""
        style = ParagraphStyle()
        assert style.named_style == NamedStyleType.NORMAL_TEXT
        assert style.alignment == Alignment.START

    def test_paragraph_style_heading(self):
        """Test paragraph style with heading."""
        style = ParagraphStyle(named_style=NamedStyleType.HEADING_1)
        assert style.named_style == NamedStyleType.HEADING_1


class TestNamedStyleType:
    """Tests for NamedStyleType enum."""

    def test_heading_values(self):
        """Test heading enum values."""
        assert NamedStyleType.HEADING_1.value == "HEADING_1"
        assert NamedStyleType.TITLE.value == "TITLE"


class TestTable:
    """Tests for Table model."""

    def test_table_creation(self):
        """Test table creation."""
        table = Table(rows=3, columns=4)
        assert table.rows == 3
        assert table.columns == 4
        assert table.cells == []
