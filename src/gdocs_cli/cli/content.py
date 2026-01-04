"""Content manipulation CLI commands."""

from pathlib import Path
from typing import Annotated

import typer

from gdocs_cli.cli.auth import require_auth
from gdocs_cli.models.element import NamedStyleType, TextStyle
from gdocs_cli.services.docs import batch_update, get_document_content
from gdocs_cli.utils.output import is_json_mode, print_json, print_success
from gdocs_cli.utils.request_builder import (
    apply_named_style_request,
    create_paragraph_bullets_request,
    insert_text_at_end_request,
    insert_text_request,
    replace_all_text_request,
    update_text_style_request,
)

content_app = typer.Typer(
    name="content",
    help="Manipulate document content.",
    no_args_is_help=True,
)


def _extract_text_from_paragraph(paragraph: dict) -> str:
    """Extract text from a paragraph element."""
    text_parts = []
    for elem in paragraph.get("elements", []):
        if "textRun" in elem:
            text_parts.append(elem["textRun"].get("content", ""))
    return "".join(text_parts)


def _get_paragraph_style(paragraph: dict) -> str | None:
    """Get the named style type of a paragraph."""
    style = paragraph.get("paragraphStyle", {})
    return style.get("namedStyleType")


def _extract_cell_text(cell: dict) -> str:
    """Extract text from a table cell, stripping trailing newlines."""
    cell_content = cell.get("content", [])
    text_parts = []
    for element in cell_content:
        if "paragraph" in element:
            text_parts.append(_extract_text_from_paragraph(element["paragraph"]))
    return "".join(text_parts).strip()


def _table_to_markdown(table: dict) -> str:
    """Convert a Google Docs table to Markdown format."""
    rows = table.get("tableRows", [])
    if not rows:
        return ""

    markdown_rows = []

    for row_idx, row in enumerate(rows):
        cells = row.get("tableCells", [])
        cell_texts = [_extract_cell_text(cell) for cell in cells]
        markdown_rows.append("| " + " | ".join(cell_texts) + " |")

        # Add header separator after first row
        if row_idx == 0:
            separator = "| " + " | ".join(["---"] * len(cells)) + " |"
            markdown_rows.append(separator)

    return "\n".join(markdown_rows)


def _content_to_markdown(content: list) -> str:
    """Convert document content to Markdown format."""
    markdown_parts = []

    for element in content:
        if "paragraph" in element:
            paragraph = element["paragraph"]
            text = _extract_text_from_paragraph(paragraph).rstrip("\n")

            if not text:
                continue

            style = _get_paragraph_style(paragraph)

            # Apply heading styles
            if style == "TITLE":
                markdown_parts.append(f"# {text}\n")
            elif style == "SUBTITLE":
                markdown_parts.append(f"*{text}*\n")
            elif style == "HEADING_1":
                markdown_parts.append(f"# {text}\n")
            elif style == "HEADING_2":
                markdown_parts.append(f"## {text}\n")
            elif style == "HEADING_3":
                markdown_parts.append(f"### {text}\n")
            elif style == "HEADING_4":
                markdown_parts.append(f"#### {text}\n")
            elif style == "HEADING_5":
                markdown_parts.append(f"##### {text}\n")
            elif style == "HEADING_6":
                markdown_parts.append(f"###### {text}\n")
            else:
                markdown_parts.append(f"{text}\n")

        elif "table" in element:
            markdown_parts.append("\n" + _table_to_markdown(element["table"]) + "\n")

    return "\n".join(markdown_parts)


def _extract_text_from_content(content: list) -> str:
    """Extract plain text from document content structure."""
    text_parts = []

    for element in content:
        if "paragraph" in element:
            paragraph = element["paragraph"]
            text_parts.append(_extract_text_from_paragraph(paragraph))
        elif "table" in element:
            table = element["table"]
            for row in table.get("tableRows", []):
                for cell in row.get("tableCells", []):
                    text_parts.append(_extract_cell_text(cell) + "\t")
                text_parts.append("\n")

    return "".join(text_parts)


@content_app.command("read")
@require_auth
def read_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    plain: Annotated[
        bool,
        typer.Option("--plain", "-p", help="Output as plain text (no formatting)"),
    ] = False,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Output raw JSON structure"),
    ] = False,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Read and display document content as Markdown.

    By default shows Markdown format with tables.
    Use --plain for plain text.
    Use --raw for full JSON structure.
    """
    doc_content = get_document_content(document_id, account=account)

    if raw or is_json_mode():
        print_json(doc_content)
    else:
        title = doc_content.get("title", "Untitled")
        body = doc_content.get("body", {})
        content = body.get("content", [])

        if plain:
            text = _extract_text_from_content(content)
            typer.echo(f"# {title}\n")
            typer.echo(text)
        else:
            text = _content_to_markdown(content)
            typer.echo(f"# {title}\n")
            typer.echo(text)


@content_app.command("insert")
@require_auth
def insert_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    text: Annotated[str, typer.Argument(help="Text to insert")],
    index: Annotated[
        int,
        typer.Option("--index", "-i", help="Position to insert at (1-based)"),
    ] = 1,
    heading: Annotated[
        str | None,
        typer.Option(
            "--heading",
            "-h",
            help="Apply heading style (TITLE, SUBTITLE, HEADING_1-6)",
        ),
    ] = None,
    bold: Annotated[
        bool,
        typer.Option("--bold", "-b", help="Make text bold"),
    ] = False,
    italic: Annotated[
        bool,
        typer.Option("--italic", help="Make text italic"),
    ] = False,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Insert text into a document at a specific position.

    By default inserts at the beginning (index 1).
    Use --heading to apply a heading style.
    Use --bold or --italic for text formatting.
    """
    requests = []

    # Insert the text with newline
    text_with_newline = text + "\n"
    requests.append(insert_text_request(text_with_newline, index=index))

    # Calculate end index
    end_index = index + len(text_with_newline)

    # Apply heading style if specified
    if heading:
        try:
            style_type = NamedStyleType[heading.upper()]
        except KeyError:
            valid_styles = ", ".join([s.name for s in NamedStyleType])
            typer.echo(f"Invalid heading: {heading}. Valid: {valid_styles}", err=True)
            raise typer.Exit(1)

        requests.append(apply_named_style_request(index, end_index, style_type))

    # Apply text formatting
    if bold or italic:
        text_style = TextStyle(bold=bold, italic=italic)
        requests.append(update_text_style_request(index, index + len(text), text_style))

    batch_update(document_id, requests, account=account)

    if is_json_mode():
        print_json({"inserted": True, "index": index, "length": len(text)})
    else:
        print_success(f"Inserted {len(text)} characters at index {index}")


@content_app.command("append")
@require_auth
def append_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    text: Annotated[str, typer.Argument(help="Text to append")],
    heading: Annotated[
        str | None,
        typer.Option("--heading", "-h", help="Apply heading style"),
    ] = None,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Append text to end of document."""
    requests = []

    # Append text at end
    text_with_newline = text + "\n"
    requests.append(insert_text_at_end_request(text_with_newline))

    # If heading is specified, we need to get the document to find the end index
    if heading:
        doc_content = get_document_content(document_id, account=account)
        body = doc_content.get("body", {})
        content = body.get("content", [])
        if content:
            last_element = content[-1]
            end_index = last_element.get("endIndex", 1)
        else:
            end_index = 1

        # After appending, the new text starts at end_index
        try:
            style_type = NamedStyleType[heading.upper()]
        except KeyError:
            valid_styles = ", ".join([s.name for s in NamedStyleType])
            typer.echo(f"Invalid heading: {heading}. Valid: {valid_styles}", err=True)
            raise typer.Exit(1)

        # Note: The style will be applied in a separate batch update after the insert
        batch_update(document_id, requests, account=account)

        # Now apply the heading style to the appended text
        new_doc_content = get_document_content(document_id, account=account)
        new_body = new_doc_content.get("body", {})
        new_content = new_body.get("content", [])
        if new_content:
            new_end = new_content[-1].get("endIndex", 1)
            style_requests = [apply_named_style_request(end_index, new_end - 1, style_type)]
            batch_update(document_id, style_requests, account=account)
    else:
        batch_update(document_id, requests, account=account)

    if is_json_mode():
        print_json({"appended": True, "length": len(text)})
    else:
        print_success(f"Appended {len(text)} characters")


@content_app.command("from-file")
@require_auth
def from_file_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    file_path: Annotated[str, typer.Argument(help="Path to text file")],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Insert content from a file.

    Reads the file content and appends it to the document.
    Supports plain text and basic markdown files.
    """
    path = Path(file_path)
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    content = path.read_text()

    requests = [insert_text_at_end_request(content)]
    batch_update(document_id, requests, account=account)

    if is_json_mode():
        print_json({"imported": True, "file": file_path, "length": len(content)})
    else:
        print_success(f"Imported {len(content)} characters from {file_path}")


@content_app.command("replace")
@require_auth
def replace_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    find: Annotated[str, typer.Argument(help="Text to find")],
    replace: Annotated[str, typer.Argument(help="Text to replace with")],
    match_case: Annotated[
        bool,
        typer.Option("--match-case/--ignore-case", help="Match case sensitivity"),
    ] = True,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Replace all occurrences of text in a document."""
    requests = [replace_all_text_request(find, replace, match_case=match_case)]
    result = batch_update(document_id, requests, account=account)

    # Get number of replacements from response
    replies = result.get("replies", [])
    occurrences = 0
    if replies:
        occurrences = replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)

    if is_json_mode():
        print_json({"replaced": True, "occurrences": occurrences})
    else:
        print_success(f"Replaced {occurrences} occurrence(s)")


@content_app.command("bullets")
@require_auth
def bullets_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    start_index: Annotated[int, typer.Argument(help="Start index of range")],
    end_index: Annotated[int, typer.Argument(help="End index of range")],
    preset: Annotated[
        str,
        typer.Option("--preset", "-p", help="Bullet preset style"),
    ] = "BULLET_DISC_CIRCLE_SQUARE",
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Apply bullet points to a range of paragraphs.

    Presets: BULLET_DISC_CIRCLE_SQUARE, BULLET_DIAMONDX_ARROW3D_SQUARE,
    BULLET_CHECKBOX, NUMBERED_DECIMAL_ALPHA_ROMAN, etc.
    """
    requests = [create_paragraph_bullets_request(start_index, end_index, preset)]
    batch_update(document_id, requests, account=account)

    if is_json_mode():
        print_json({"bullets_applied": True, "start": start_index, "end": end_index})
    else:
        print_success(f"Applied bullets to range {start_index}-{end_index}")
