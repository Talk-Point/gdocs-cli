"""Table management CLI commands."""

from typing import Annotated

import typer

from gdocs_cli.cli.auth import require_auth
from gdocs_cli.services.docs import batch_update, get_document_content
from gdocs_cli.utils.output import is_json_mode, print_json, print_success, print_table
from gdocs_cli.utils.request_builder import (
    delete_table_column_request,
    delete_table_row_request,
    insert_table_column_request,
    insert_table_request,
    insert_table_row_request,
)

table_app = typer.Typer(
    name="table",
    help="Manage tables in documents.",
    no_args_is_help=True,
)


def _find_tables(doc_content: dict) -> list[dict]:
    """Find all tables in document content.

    Args:
        doc_content: Full document content from API.

    Returns:
        List of table info dicts with index and dimensions.
    """
    tables = []
    body = doc_content.get("body", {})
    content = body.get("content", [])

    for element in content:
        if "table" in element:
            table = element["table"]
            tables.append(
                {
                    "start_index": element.get("startIndex"),
                    "end_index": element.get("endIndex"),
                    "rows": table.get("rows", 0),
                    "columns": table.get("columns", 0),
                }
            )

    return tables


@table_app.command("create")
@require_auth
def create_table_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    rows: Annotated[
        int,
        typer.Option("--rows", "-r", help="Number of rows"),
    ] = 3,
    columns: Annotated[
        int,
        typer.Option("--columns", "-c", help="Number of columns"),
    ] = 3,
    index: Annotated[
        int,
        typer.Option("--index", "-i", help="Position to insert table at"),
    ] = 1,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Create a table in a document.

    By default creates a 3x3 table at the beginning of the document.
    """
    requests = [insert_table_request(rows, columns, index=index)]
    batch_update(document_id, requests, account=account)

    if is_json_mode():
        print_json(
            {
                "created": True,
                "rows": rows,
                "columns": columns,
                "index": index,
            }
        )
    else:
        print_success(f"Created {rows}x{columns} table at index {index}")


@table_app.command("list")
@require_auth
def list_tables_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """List all tables in a document."""
    doc_content = get_document_content(document_id, account=account)
    tables = _find_tables(doc_content)

    if is_json_mode():
        print_json({"tables": tables})
    else:
        if not tables:
            typer.echo("No tables found in document.")
            return

        rows = []
        for i, t in enumerate(tables):
            rows.append(
                [
                    str(i),
                    str(t["start_index"]),
                    f"{t['rows']}x{t['columns']}",
                ]
            )

        print_table("Tables", ["Index", "Start Position", "Size (RxC)"], rows)


@table_app.command("add-row")
@require_auth
def add_row_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    table_index: Annotated[
        int,
        typer.Argument(help="Table index (0-based, use 'table list' to find)"),
    ],
    row: Annotated[
        int,
        typer.Option("--row", "-r", help="Row index to insert relative to"),
    ] = 0,
    above: Annotated[
        bool,
        typer.Option("--above", help="Insert above instead of below"),
    ] = False,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Add a row to a table.

    By default adds below the specified row.
    Use --above to insert above instead.
    """
    doc_content = get_document_content(document_id, account=account)
    tables = _find_tables(doc_content)

    if table_index >= len(tables):
        typer.echo(f"Table index {table_index} not found. Document has {len(tables)} table(s).")
        raise typer.Exit(1)

    table = tables[table_index]
    requests = [insert_table_row_request(table["start_index"], row, insert_below=not above)]
    batch_update(document_id, requests, account=account)

    position = "above" if above else "below"
    if is_json_mode():
        print_json({"added_row": True, "table_index": table_index, "position": position})
    else:
        print_success(f"Added row {position} row {row} in table {table_index}")


@table_app.command("delete-row")
@require_auth
def delete_row_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    table_index: Annotated[
        int,
        typer.Argument(help="Table index (0-based)"),
    ],
    row: Annotated[
        int,
        typer.Option("--row", "-r", help="Row index to delete"),
    ],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Delete a row from a table."""
    doc_content = get_document_content(document_id, account=account)
    tables = _find_tables(doc_content)

    if table_index >= len(tables):
        typer.echo(f"Table index {table_index} not found. Document has {len(tables)} table(s).")
        raise typer.Exit(1)

    table = tables[table_index]
    requests = [delete_table_row_request(table["start_index"], row)]
    batch_update(document_id, requests, account=account)

    if is_json_mode():
        print_json({"deleted_row": True, "table_index": table_index, "row": row})
    else:
        print_success(f"Deleted row {row} from table {table_index}")


@table_app.command("add-column")
@require_auth
def add_column_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    table_index: Annotated[
        int,
        typer.Argument(help="Table index (0-based)"),
    ],
    column: Annotated[
        int,
        typer.Option("--column", "-c", help="Column index to insert relative to"),
    ] = 0,
    left: Annotated[
        bool,
        typer.Option("--left", help="Insert left instead of right"),
    ] = False,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Add a column to a table.

    By default adds to the right of the specified column.
    Use --left to insert to the left instead.
    """
    doc_content = get_document_content(document_id, account=account)
    tables = _find_tables(doc_content)

    if table_index >= len(tables):
        typer.echo(f"Table index {table_index} not found. Document has {len(tables)} table(s).")
        raise typer.Exit(1)

    table = tables[table_index]
    requests = [insert_table_column_request(table["start_index"], column, insert_right=not left)]
    batch_update(document_id, requests, account=account)

    position = "left of" if left else "right of"
    if is_json_mode():
        print_json({"added_column": True, "table_index": table_index, "position": position})
    else:
        print_success(f"Added column {position} column {column} in table {table_index}")


@table_app.command("delete-column")
@require_auth
def delete_column_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    table_index: Annotated[
        int,
        typer.Argument(help="Table index (0-based)"),
    ],
    column: Annotated[
        int,
        typer.Option("--column", "-c", help="Column index to delete"),
    ],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Delete a column from a table."""
    doc_content = get_document_content(document_id, account=account)
    tables = _find_tables(doc_content)

    if table_index >= len(tables):
        typer.echo(f"Table index {table_index} not found. Document has {len(tables)} table(s).")
        raise typer.Exit(1)

    table = tables[table_index]
    requests = [delete_table_column_request(table["start_index"], column)]
    batch_update(document_id, requests, account=account)

    if is_json_mode():
        print_json({"deleted_column": True, "table_index": table_index, "column": column})
    else:
        print_success(f"Deleted column {column} from table {table_index}")
