"""Main CLI application."""

from typing import Annotated

import typer

from gdocs_cli import __version__
from gdocs_cli.cli.auth import auth_app
from gdocs_cli.cli.content import content_app
from gdocs_cli.cli.document import document_app
from gdocs_cli.cli.drives import drives_app
from gdocs_cli.cli.table import table_app
from gdocs_cli.utils.output import set_json_mode

app = typer.Typer(
    name="gdocs",
    help="A command-line interface for Google Docs.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"gdocs-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[  # noqa: ARG001
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output results as JSON.",
        ),
    ] = False,
) -> None:
    """Google Docs CLI - Manage documents from the command line."""
    set_json_mode(json_output)


# Register sub-apps
app.add_typer(auth_app, name="auth")
app.add_typer(document_app, name="doc")
app.add_typer(content_app, name="content")
app.add_typer(table_app, name="table")
app.add_typer(drives_app, name="drives")


if __name__ == "__main__":
    app()
