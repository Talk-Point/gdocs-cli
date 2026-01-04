"""BatchUpdate request builder utilities for Google Docs API."""

from gdocs_cli.models.element import NamedStyleType, ParagraphStyle, TextStyle


def insert_text_request(
    text: str,
    index: int = 1,
    segment_id: str | None = None,
) -> dict:
    """Build InsertTextRequest.

    Args:
        text: Text to insert.
        index: Position to insert at.
        segment_id: Optional segment ID.

    Returns:
        InsertTextRequest dict.
    """
    location = {"index": index}
    if segment_id:
        location["segmentId"] = segment_id

    return {
        "insertText": {
            "location": location,
            "text": text,
        }
    }


def insert_text_at_end_request(
    text: str,
    segment_id: str | None = None,
) -> dict:
    """Build InsertTextRequest to append at end of document.

    Args:
        text: Text to insert.
        segment_id: Optional segment ID.

    Returns:
        InsertTextRequest dict.
    """
    location: dict = {"endOfSegmentLocation": {}}
    if segment_id:
        location["endOfSegmentLocation"]["segmentId"] = segment_id

    return {
        "insertText": {
            **location,
            "text": text,
        }
    }


def update_text_style_request(
    start_index: int,
    end_index: int,
    style: TextStyle,
    segment_id: str | None = None,
) -> dict:
    """Build UpdateTextStyleRequest.

    Args:
        start_index: Start of range.
        end_index: End of range.
        style: TextStyle to apply.
        segment_id: Optional segment ID.

    Returns:
        UpdateTextStyleRequest dict.
    """
    fields = []
    text_style = {}

    if style.bold:
        text_style["bold"] = True
        fields.append("bold")
    if style.italic:
        text_style["italic"] = True
        fields.append("italic")
    if style.underline:
        text_style["underline"] = True
        fields.append("underline")
    if style.strikethrough:
        text_style["strikethrough"] = True
        fields.append("strikethrough")
    if style.font_size:
        text_style["fontSize"] = {"magnitude": style.font_size, "unit": "PT"}
        fields.append("fontSize")
    if style.font_family:
        text_style["weightedFontFamily"] = {"fontFamily": style.font_family}
        fields.append("weightedFontFamily")
    if style.link_url:
        text_style["link"] = {"url": style.link_url}
        fields.append("link")
    if style.foreground_color:
        text_style["foregroundColor"] = _parse_color(style.foreground_color)
        fields.append("foregroundColor")
    if style.background_color:
        text_style["backgroundColor"] = _parse_color(style.background_color)
        fields.append("backgroundColor")

    range_spec = {"startIndex": start_index, "endIndex": end_index}
    if segment_id:
        range_spec["segmentId"] = segment_id

    return {
        "updateTextStyle": {
            "range": range_spec,
            "textStyle": text_style,
            "fields": ",".join(fields),
        }
    }


def update_paragraph_style_request(
    start_index: int,
    end_index: int,
    style: ParagraphStyle,
    segment_id: str | None = None,
) -> dict:
    """Build UpdateParagraphStyleRequest.

    Args:
        start_index: Start of range.
        end_index: End of range.
        style: ParagraphStyle to apply.
        segment_id: Optional segment ID.

    Returns:
        UpdateParagraphStyleRequest dict.
    """
    fields = ["namedStyleType"]
    paragraph_style = {
        "namedStyleType": style.named_style.value,
    }

    if style.alignment.value != "START":
        paragraph_style["alignment"] = style.alignment.value
        fields.append("alignment")

    if style.space_above_pt > 0:
        paragraph_style["spaceAbove"] = {"magnitude": style.space_above_pt, "unit": "PT"}
        fields.append("spaceAbove")

    if style.space_below_pt > 0:
        paragraph_style["spaceBelow"] = {"magnitude": style.space_below_pt, "unit": "PT"}
        fields.append("spaceBelow")

    if style.indent_first_line_pt > 0:
        paragraph_style["indentFirstLine"] = {"magnitude": style.indent_first_line_pt, "unit": "PT"}
        fields.append("indentFirstLine")

    range_spec = {"startIndex": start_index, "endIndex": end_index}
    if segment_id:
        range_spec["segmentId"] = segment_id

    return {
        "updateParagraphStyle": {
            "range": range_spec,
            "paragraphStyle": paragraph_style,
            "fields": ",".join(fields),
        }
    }


def apply_named_style_request(
    start_index: int,
    end_index: int,
    named_style: NamedStyleType,
    segment_id: str | None = None,
) -> dict:
    """Build UpdateParagraphStyleRequest for named style only.

    Args:
        start_index: Start of range.
        end_index: End of range.
        named_style: Named style to apply.
        segment_id: Optional segment ID.

    Returns:
        UpdateParagraphStyleRequest dict.
    """
    range_spec = {"startIndex": start_index, "endIndex": end_index}
    if segment_id:
        range_spec["segmentId"] = segment_id

    return {
        "updateParagraphStyle": {
            "range": range_spec,
            "paragraphStyle": {"namedStyleType": named_style.value},
            "fields": "namedStyleType",
        }
    }


def insert_table_request(
    rows: int,
    columns: int,
    index: int = 1,
    segment_id: str | None = None,
) -> dict:
    """Build InsertTableRequest.

    Args:
        rows: Number of rows.
        columns: Number of columns.
        index: Position to insert at.
        segment_id: Optional segment ID.

    Returns:
        InsertTableRequest dict.
    """
    location = {"index": index}
    if segment_id:
        location["segmentId"] = segment_id

    return {
        "insertTable": {
            "rows": rows,
            "columns": columns,
            "location": location,
        }
    }


def insert_table_row_request(
    table_start_index: int,
    row_index: int,
    insert_below: bool = True,
) -> dict:
    """Build InsertTableRowRequest.

    Args:
        table_start_index: Start index of the table.
        row_index: Row to insert relative to.
        insert_below: If True, insert below; if False, insert above.

    Returns:
        InsertTableRowRequest dict.
    """
    return {
        "insertTableRow": {
            "tableCellLocation": {
                "tableStartLocation": {"index": table_start_index},
                "rowIndex": row_index,
                "columnIndex": 0,
            },
            "insertBelow": insert_below,
        }
    }


def delete_table_row_request(
    table_start_index: int,
    row_index: int,
) -> dict:
    """Build DeleteTableRowRequest.

    Args:
        table_start_index: Start index of the table.
        row_index: Row to delete.

    Returns:
        DeleteTableRowRequest dict.
    """
    return {
        "deleteTableRow": {
            "tableCellLocation": {
                "tableStartLocation": {"index": table_start_index},
                "rowIndex": row_index,
                "columnIndex": 0,
            },
        }
    }


def insert_table_column_request(
    table_start_index: int,
    column_index: int,
    insert_right: bool = True,
) -> dict:
    """Build InsertTableColumnRequest.

    Args:
        table_start_index: Start index of the table.
        column_index: Column to insert relative to.
        insert_right: If True, insert right; if False, insert left.

    Returns:
        InsertTableColumnRequest dict.
    """
    return {
        "insertTableColumn": {
            "tableCellLocation": {
                "tableStartLocation": {"index": table_start_index},
                "rowIndex": 0,
                "columnIndex": column_index,
            },
            "insertRight": insert_right,
        }
    }


def delete_table_column_request(
    table_start_index: int,
    column_index: int,
) -> dict:
    """Build DeleteTableColumnRequest.

    Args:
        table_start_index: Start index of the table.
        column_index: Column to delete.

    Returns:
        DeleteTableColumnRequest dict.
    """
    return {
        "deleteTableColumn": {
            "tableCellLocation": {
                "tableStartLocation": {"index": table_start_index},
                "rowIndex": 0,
                "columnIndex": column_index,
            },
        }
    }


def delete_content_range_request(
    start_index: int,
    end_index: int,
    segment_id: str | None = None,
) -> dict:
    """Build DeleteContentRangeRequest.

    Args:
        start_index: Start of range to delete.
        end_index: End of range to delete.
        segment_id: Optional segment ID.

    Returns:
        DeleteContentRangeRequest dict.
    """
    range_spec = {"startIndex": start_index, "endIndex": end_index}
    if segment_id:
        range_spec["segmentId"] = segment_id

    return {
        "deleteContentRange": {
            "range": range_spec,
        }
    }


def replace_all_text_request(
    find_text: str,
    replace_text: str,
    match_case: bool = True,
) -> dict:
    """Build ReplaceAllTextRequest.

    Args:
        find_text: Text to find.
        replace_text: Text to replace with.
        match_case: Whether to match case.

    Returns:
        ReplaceAllTextRequest dict.
    """
    return {
        "replaceAllText": {
            "containsText": {
                "text": find_text,
                "matchCase": match_case,
            },
            "replaceText": replace_text,
        }
    }


def insert_inline_image_request(
    uri: str,
    index: int = 1,
    width_pt: float | None = None,
    height_pt: float | None = None,
    segment_id: str | None = None,
) -> dict:
    """Build InsertInlineImageRequest.

    Args:
        uri: URI of the image.
        index: Position to insert at.
        width_pt: Optional width in points.
        height_pt: Optional height in points.
        segment_id: Optional segment ID.

    Returns:
        InsertInlineImageRequest dict.
    """
    location = {"index": index}
    if segment_id:
        location["segmentId"] = segment_id

    request = {
        "insertInlineImage": {
            "location": location,
            "uri": uri,
        }
    }

    if width_pt or height_pt:
        object_size = {}
        if width_pt:
            object_size["width"] = {"magnitude": width_pt, "unit": "PT"}
        if height_pt:
            object_size["height"] = {"magnitude": height_pt, "unit": "PT"}
        request["insertInlineImage"]["objectSize"] = object_size

    return request


def create_paragraph_bullets_request(
    start_index: int,
    end_index: int,
    bullet_preset: str = "BULLET_DISC_CIRCLE_SQUARE",
    segment_id: str | None = None,
) -> dict:
    """Build CreateParagraphBulletsRequest.

    Args:
        start_index: Start of range.
        end_index: End of range.
        bullet_preset: Bullet preset type.
        segment_id: Optional segment ID.

    Returns:
        CreateParagraphBulletsRequest dict.
    """
    range_spec = {"startIndex": start_index, "endIndex": end_index}
    if segment_id:
        range_spec["segmentId"] = segment_id

    return {
        "createParagraphBullets": {
            "range": range_spec,
            "bulletPreset": bullet_preset,
        }
    }


def delete_paragraph_bullets_request(
    start_index: int,
    end_index: int,
    segment_id: str | None = None,
) -> dict:
    """Build DeleteParagraphBulletsRequest.

    Args:
        start_index: Start of range.
        end_index: End of range.
        segment_id: Optional segment ID.

    Returns:
        DeleteParagraphBulletsRequest dict.
    """
    range_spec = {"startIndex": start_index, "endIndex": end_index}
    if segment_id:
        range_spec["segmentId"] = segment_id

    return {
        "deleteParagraphBullets": {
            "range": range_spec,
        }
    }


def _parse_color(hex_color: str) -> dict:
    """Parse hex color to Google Docs color format.

    Args:
        hex_color: Hex color string (e.g., "#FF0000" or "FF0000").

    Returns:
        Color dict for Google Docs API.
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0

    return {
        "color": {
            "rgbColor": {
                "red": r,
                "green": g,
                "blue": b,
            }
        }
    }
