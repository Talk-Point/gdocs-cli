"""Tests for output utilities."""

import json

from gdocs_cli.utils.output import (
    is_json_mode,
    print_document_info,
    print_error,
    print_info,
    print_json,
    print_json_error,
    print_success,
    print_table,
    print_warning,
    set_json_mode,
)


class TestJsonMode:
    """Tests for JSON mode."""

    def test_set_json_mode(self):
        """Test setting JSON mode."""
        set_json_mode(True)
        assert is_json_mode() is True

        set_json_mode(False)
        assert is_json_mode() is False

    def test_default_json_mode(self):
        """Test default JSON mode is False."""
        set_json_mode(False)  # Reset
        assert is_json_mode() is False


class TestPrintSuccess:
    """Tests for print_success."""

    def test_print_success_normal_mode(self, capsys):
        """Test print_success in normal mode."""
        set_json_mode(False)
        print_success("Operation completed")

        captured = capsys.readouterr()
        assert "Operation completed" in captured.out
        assert "✓" in captured.out

    def test_print_success_json_mode(self, capsys):
        """Test print_success is silent in JSON mode."""
        set_json_mode(True)
        print_success("Operation completed")

        captured = capsys.readouterr()
        assert captured.out == ""

        set_json_mode(False)


class TestPrintError:
    """Tests for print_error."""

    def test_print_error_simple(self, capsys):
        """Test print_error with message only."""
        set_json_mode(False)
        print_error("Something went wrong")

        captured = capsys.readouterr()
        assert "Something went wrong" in captured.out
        assert "✗" in captured.out

    def test_print_error_with_details(self, capsys):
        """Test print_error with details."""
        set_json_mode(False)
        print_error("Error occurred", details="More information")

        captured = capsys.readouterr()
        assert "Error occurred" in captured.out
        assert "More information" in captured.out

    def test_print_error_with_tip(self, capsys):
        """Test print_error with tip."""
        set_json_mode(False)
        print_error("Error occurred", tip="Try this instead")

        captured = capsys.readouterr()
        assert "Error occurred" in captured.out
        assert "Try this instead" in captured.out

    def test_print_error_json_mode(self, capsys):
        """Test print_error is silent in JSON mode."""
        set_json_mode(True)
        print_error("Error occurred")

        captured = capsys.readouterr()
        assert captured.out == ""

        set_json_mode(False)


class TestPrintWarning:
    """Tests for print_warning."""

    def test_print_warning(self, capsys):
        """Test print_warning."""
        set_json_mode(False)
        print_warning("This is a warning")

        captured = capsys.readouterr()
        assert "This is a warning" in captured.out
        assert "!" in captured.out

    def test_print_warning_json_mode(self, capsys):
        """Test print_warning is silent in JSON mode."""
        set_json_mode(True)
        print_warning("Warning")

        captured = capsys.readouterr()
        assert captured.out == ""

        set_json_mode(False)


class TestPrintInfo:
    """Tests for print_info."""

    def test_print_info(self, capsys):
        """Test print_info."""
        set_json_mode(False)
        print_info("Information message")

        captured = capsys.readouterr()
        assert "Information message" in captured.out
        assert "ℹ" in captured.out

    def test_print_info_json_mode(self, capsys):
        """Test print_info is silent in JSON mode."""
        set_json_mode(True)
        print_info("Info")

        captured = capsys.readouterr()
        assert captured.out == ""

        set_json_mode(False)


class TestPrintJson:
    """Tests for print_json."""

    def test_print_json_dict(self, capsys):
        """Test print_json with dict."""
        set_json_mode(False)  # Should still print
        print_json({"key": "value", "number": 42})

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["key"] == "value"
        assert data["number"] == 42

    def test_print_json_list(self, capsys):
        """Test print_json with list."""
        print_json([1, 2, 3])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == [1, 2, 3]

    def test_print_json_unicode(self, capsys):
        """Test print_json preserves unicode."""
        print_json({"emoji": "✓", "german": "Überschrift"})

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["emoji"] == "✓"
        assert data["german"] == "Überschrift"


class TestPrintJsonError:
    """Tests for print_json_error."""

    def test_print_json_error_simple(self, capsys):
        """Test print_json_error with code and message."""
        print_json_error("ERROR_CODE", "Error message")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["error"] is True
        assert data["code"] == "ERROR_CODE"
        assert data["message"] == "Error message"

    def test_print_json_error_with_details(self, capsys):
        """Test print_json_error with details."""
        print_json_error("ERROR_CODE", "Error message", details="More info")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["details"] == "More info"


class TestPrintTable:
    """Tests for print_table."""

    def test_print_table_normal(self, capsys):
        """Test print_table in normal mode."""
        set_json_mode(False)
        print_table(
            "Test Table",
            ["Col1", "Col2"],
            [["A", "B"], ["C", "D"]],
        )

        captured = capsys.readouterr()
        assert "Test Table" in captured.out
        assert "Col1" in captured.out
        assert "A" in captured.out

    def test_print_table_with_footer(self, capsys):
        """Test print_table with footer."""
        set_json_mode(False)
        print_table(
            "Test Table",
            ["Col1"],
            [["A"]],
            footer="Footer text",
        )

        captured = capsys.readouterr()
        assert "Footer text" in captured.out

    def test_print_table_json_mode(self, capsys):
        """Test print_table is silent in JSON mode."""
        set_json_mode(True)
        print_table("Table", ["Col"], [["A"]])

        captured = capsys.readouterr()
        assert captured.out == ""

        set_json_mode(False)


class TestPrintDocumentInfo:
    """Tests for print_document_info."""

    def test_print_document_info(self, capsys):
        """Test print_document_info."""
        set_json_mode(False)
        print_document_info("doc123", "Test Document")

        captured = capsys.readouterr()
        assert "Test Document" in captured.out
        assert "doc123" in captured.out
        assert "https://docs.google.com/document/d/doc123/edit" in captured.out

    def test_print_document_info_with_modified(self, capsys):
        """Test print_document_info with modified time."""
        set_json_mode(False)
        print_document_info("doc123", "Test Doc", modified_time="2024-01-15")

        captured = capsys.readouterr()
        assert "2024-01-15" in captured.out

    def test_print_document_info_no_url(self, capsys):
        """Test print_document_info without URL."""
        set_json_mode(False)
        print_document_info("doc123", "Test Doc", show_url=False)

        captured = capsys.readouterr()
        assert "https://" not in captured.out

    def test_print_document_info_json_mode(self, capsys):
        """Test print_document_info is silent in JSON mode."""
        set_json_mode(True)
        print_document_info("doc123", "Test Doc")

        captured = capsys.readouterr()
        assert captured.out == ""

        set_json_mode(False)
