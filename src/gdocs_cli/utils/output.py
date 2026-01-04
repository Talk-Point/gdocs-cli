"""Output formatting utilities using rich."""

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console(force_terminal=True if sys.platform == "win32" else None)

# Global flag for JSON output mode
_json_mode = False


def set_json_mode(enabled: bool) -> None:
    """Set global JSON output mode."""
    global _json_mode
    _json_mode = enabled


def is_json_mode() -> bool:
    """Check if JSON output mode is enabled."""
    return _json_mode


def print_success(message: str) -> None:
    """Print a success message."""
    if _json_mode:
        return
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str, details: str | None = None, tip: str | None = None) -> None:
    """Print an error message with optional details and tip."""
    if _json_mode:
        return
    console.print(f"[red]✗[/red] [bold]Error:[/bold] {message}")
    if details:
        console.print(f"  {details}")
    if tip:
        console.print(f"\n  [dim]Tip: {tip}[/dim]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    if _json_mode:
        return
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    if _json_mode:
        return
    console.print(f"[blue]ℹ[/blue] {message}")


def print_json(data: dict[str, Any] | list[Any]) -> None:
    """Print data as formatted JSON."""
    console.print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def print_json_error(code: str, message: str, details: str | None = None) -> None:
    """Print an error in JSON format."""
    error_data = {
        "error": True,
        "code": code,
        "message": message,
    }
    if details:
        error_data["details"] = details
    print_json(error_data)


def print_table(
    title: str | None,
    columns: list[str],
    rows: list[list[str]],
    footer: str | None = None,
) -> None:
    """Print a formatted table."""
    if _json_mode:
        return

    table = Table(title=title, show_header=True, header_style="bold")

    for column in columns:
        table.add_column(column)

    for row in rows:
        table.add_row(*row)

    console.print(table)

    if footer:
        console.print(f"\n[dim]{footer}[/dim]")


def print_document_info(
    doc_id: str,
    title: str,
    modified_time: str | None = None,
    show_url: bool = True,
) -> None:
    """Print document information.

    Args:
        doc_id: Document ID.
        title: Document title.
        modified_time: Optional modification time.
        show_url: Whether to show the document URL.
    """
    if _json_mode:
        return

    console.print(f"[bold]Title:[/bold] {title}")
    console.print(f"[bold]ID:[/bold] {doc_id}")
    if modified_time:
        console.print(f"[bold]Modified:[/bold] {modified_time}")
    if show_url:
        console.print(f"[bold]URL:[/bold] https://docs.google.com/document/d/{doc_id}/edit")
