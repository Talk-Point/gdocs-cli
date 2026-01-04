"""Shared Drives management CLI commands."""

from typing import Annotated

import typer

from gdocs_cli.cli.auth import require_auth
from gdocs_cli.services.docs import list_folders, list_shared_drives
from gdocs_cli.utils.output import is_json_mode, print_json, print_table

drives_app = typer.Typer(
    name="drives",
    help="Manage Shared Drives (Team Drives).",
    no_args_is_help=True,
)


@drives_app.command("list")
@require_auth
def list_drives_command(
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """List all Shared Drives you have access to."""
    drives = list_shared_drives(account=account)

    if is_json_mode():
        print_json({"drives": [{"id": d.id, "name": d.name} for d in drives]})
    else:
        if not drives:
            typer.echo("No Shared Drives found.")
            return

        rows = [[d.id, d.name] for d in drives]
        print_table("Shared Drives", ["ID", "Name"], rows)


@drives_app.command("folders")
@require_auth
def list_folders_command(
    drive_id: Annotated[
        str | None,
        typer.Argument(help="Shared Drive ID (optional, lists from My Drive if not specified)"),
    ] = None,
    parent: Annotated[
        str | None,
        typer.Option("--parent", "-p", help="Parent folder ID to list from"),
    ] = None,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """List folders in a Shared Drive or My Drive.

    Without arguments, lists root folders from My Drive.
    Specify a drive ID to list folders from a Shared Drive.
    Use --parent to list subfolders.
    """
    folders = list_folders(
        parent_id=parent,
        shared_drive_id=drive_id,
        account=account,
    )

    if is_json_mode():
        print_json(
            {"folders": [{"id": f.id, "name": f.name, "parent_id": f.parent_id} for f in folders]}
        )
    else:
        if not folders:
            typer.echo("No folders found.")
            return

        rows = [[f.id, f.name] for f in folders]
        print_table("Folders", ["ID", "Name"], rows)
