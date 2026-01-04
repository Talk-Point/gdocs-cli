"""Domain models for gdocs-cli."""

from gdocs_cli.models.document import Document, DocumentSummary
from gdocs_cli.models.element import (
    NamedStyleType,
    ParagraphStyle,
    Table,
    TableCell,
    TextStyle,
)

__all__ = [
    "Document",
    "DocumentSummary",
    "NamedStyleType",
    "ParagraphStyle",
    "Table",
    "TableCell",
    "TextStyle",
]
