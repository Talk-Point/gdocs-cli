"""Structural element domain models."""

from dataclasses import dataclass, field
from enum import Enum


class NamedStyleType(str, Enum):
    """Available paragraph styles."""

    NORMAL_TEXT = "NORMAL_TEXT"
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    HEADING_5 = "HEADING_5"
    HEADING_6 = "HEADING_6"


class Alignment(str, Enum):
    """Paragraph alignment options."""

    START = "START"
    CENTER = "CENTER"
    END = "END"
    JUSTIFIED = "JUSTIFIED"


@dataclass
class TextStyle:
    """Text formatting options."""

    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    font_size: float | None = None  # in PT
    font_family: str | None = None
    foreground_color: str | None = None  # Hex color
    background_color: str | None = None  # Hex color
    link_url: str | None = None


@dataclass
class ParagraphStyle:
    """Paragraph formatting options."""

    named_style: NamedStyleType = NamedStyleType.NORMAL_TEXT
    alignment: Alignment = Alignment.START
    line_spacing: float = 1.0
    space_above_pt: float = 0
    space_below_pt: float = 0
    indent_first_line_pt: float = 0


@dataclass
class TableCell:
    """A single table cell."""

    content: str
    row_span: int = 1
    column_span: int = 1


@dataclass
class Table:
    """A table structure."""

    rows: int
    columns: int
    cells: list[list[str]] = field(default_factory=list)
    start_index: int | None = None
