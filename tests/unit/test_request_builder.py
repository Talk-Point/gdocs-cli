"""Tests for request builder utilities."""

from gdocs_cli.models.element import NamedStyleType, ParagraphStyle, TextStyle
from gdocs_cli.utils.request_builder import (
    apply_named_style_request,
    create_paragraph_bullets_request,
    delete_table_row_request,
    insert_table_request,
    insert_table_row_request,
    insert_text_at_end_request,
    insert_text_request,
    replace_all_text_request,
    update_paragraph_style_request,
    update_text_style_request,
)


class TestInsertTextRequest:
    """Tests for insert text requests."""

    def test_basic_insert(self):
        """Test basic text insertion."""
        request = insert_text_request("Hello", index=1)
        assert request == {
            "insertText": {
                "location": {"index": 1},
                "text": "Hello",
            }
        }

    def test_insert_with_segment(self):
        """Test insertion with segment ID."""
        request = insert_text_request("Hello", index=5, segment_id="header")
        assert request["insertText"]["location"]["segmentId"] == "header"

    def test_insert_at_end(self):
        """Test insertion at end of document."""
        request = insert_text_at_end_request("Appended text")
        assert "endOfSegmentLocation" in request["insertText"]
        assert request["insertText"]["text"] == "Appended text"


class TestUpdateTextStyleRequest:
    """Tests for text style update requests."""

    def test_bold_style(self):
        """Test bold text style."""
        style = TextStyle(bold=True)
        request = update_text_style_request(0, 10, style)
        assert request["updateTextStyle"]["textStyle"]["bold"] is True
        assert "bold" in request["updateTextStyle"]["fields"]

    def test_multiple_styles(self):
        """Test multiple text styles."""
        style = TextStyle(bold=True, italic=True, underline=True)
        request = update_text_style_request(0, 10, style)
        text_style = request["updateTextStyle"]["textStyle"]
        assert text_style["bold"] is True
        assert text_style["italic"] is True
        assert text_style["underline"] is True

    def test_font_size(self):
        """Test font size style."""
        style = TextStyle(font_size=14.0)
        request = update_text_style_request(0, 10, style)
        font_size = request["updateTextStyle"]["textStyle"]["fontSize"]
        assert font_size["magnitude"] == 14.0
        assert font_size["unit"] == "PT"


class TestUpdateParagraphStyleRequest:
    """Tests for paragraph style update requests."""

    def test_heading_style(self):
        """Test heading paragraph style."""
        style = ParagraphStyle(named_style=NamedStyleType.HEADING_1)
        request = update_paragraph_style_request(0, 20, style)
        para_style = request["updateParagraphStyle"]["paragraphStyle"]
        assert para_style["namedStyleType"] == "HEADING_1"

    def test_apply_named_style(self):
        """Test applying named style directly."""
        request = apply_named_style_request(0, 20, NamedStyleType.TITLE)
        assert request["updateParagraphStyle"]["paragraphStyle"]["namedStyleType"] == "TITLE"
        assert request["updateParagraphStyle"]["fields"] == "namedStyleType"


class TestTableRequests:
    """Tests for table-related requests."""

    def test_insert_table(self):
        """Test table insertion."""
        request = insert_table_request(3, 4, index=1)
        assert request["insertTable"]["rows"] == 3
        assert request["insertTable"]["columns"] == 4
        assert request["insertTable"]["location"]["index"] == 1

    def test_insert_table_row(self):
        """Test row insertion."""
        request = insert_table_row_request(10, row_index=2, insert_below=True)
        cell_loc = request["insertTableRow"]["tableCellLocation"]
        assert cell_loc["tableStartLocation"]["index"] == 10
        assert cell_loc["rowIndex"] == 2
        assert request["insertTableRow"]["insertBelow"] is True

    def test_delete_table_row(self):
        """Test row deletion."""
        request = delete_table_row_request(10, row_index=1)
        cell_loc = request["deleteTableRow"]["tableCellLocation"]
        assert cell_loc["tableStartLocation"]["index"] == 10
        assert cell_loc["rowIndex"] == 1


class TestReplaceAllTextRequest:
    """Tests for replace all text requests."""

    def test_basic_replace(self):
        """Test basic text replacement."""
        request = replace_all_text_request("old", "new")
        assert request["replaceAllText"]["containsText"]["text"] == "old"
        assert request["replaceAllText"]["replaceText"] == "new"
        assert request["replaceAllText"]["containsText"]["matchCase"] is True

    def test_case_insensitive_replace(self):
        """Test case-insensitive replacement."""
        request = replace_all_text_request("old", "new", match_case=False)
        assert request["replaceAllText"]["containsText"]["matchCase"] is False


class TestBulletRequests:
    """Tests for bullet-related requests."""

    def test_create_bullets(self):
        """Test bullet creation."""
        request = create_paragraph_bullets_request(0, 50)
        assert request["createParagraphBullets"]["range"]["startIndex"] == 0
        assert request["createParagraphBullets"]["range"]["endIndex"] == 50
        assert "bulletPreset" in request["createParagraphBullets"]
