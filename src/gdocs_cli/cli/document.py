"""Document management CLI commands."""

from typing import Annotated

import typer

from gdocs_cli.cli.auth import require_auth
from gdocs_cli.services.docs import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    list_permissions,
    list_revisions,
    move_document,
    search_documents,
    share_document,
    unshare_document,
)
from gdocs_cli.utils.output import (
    is_json_mode,
    print_document_info,
    print_json,
    print_success,
    print_table,
)

document_app = typer.Typer(
    name="doc",
    help="Manage Google Docs documents.",
    no_args_is_help=True,
)


@document_app.command("create")
@require_auth
def create_command(
    title: Annotated[str, typer.Argument(help="Document title")],
    folder: Annotated[
        str | None,
        typer.Option("--folder", "-f", help="Folder ID to create document in"),
    ] = None,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Create a new Google Doc.

    Creates a document in My Drive by default.
    Use --folder to create in a specific folder or Shared Drive.
    """
    doc = create_document(title=title, folder_id=folder, account=account)

    if is_json_mode():
        print_json({"id": doc.id, "title": doc.title, "url": doc.url})
    else:
        print_success(f"Created: {doc.title}")
        typer.echo(f"  ID: {doc.id}")
        typer.echo(f"  URL: {doc.url}")


@document_app.command("get")
@require_auth
def get_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Get document details."""
    doc = get_document(document_id=document_id, account=account)

    if is_json_mode():
        print_json(
            {
                "id": doc.id,
                "title": doc.title,
                "revision_id": doc.revision_id,
                "url": doc.url,
            }
        )
    else:
        print_document_info(doc.id, doc.title)


@document_app.command("list")
@require_auth
def list_command(
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of documents to list"),
    ] = 20,
    folder: Annotated[
        str | None,
        typer.Option("--folder", "-f", help="Folder ID to list documents from"),
    ] = None,
    shared_drive: Annotated[
        str | None,
        typer.Option("--shared-drive", "-d", help="Shared Drive ID to list documents from"),
    ] = None,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """List your Google Docs.

    By default lists documents from My Drive.
    Use --shared-drive to list from a Shared Drive.
    Use --folder to list from a specific folder.
    """
    docs = list_documents(
        limit=limit,
        folder_id=folder,
        shared_drive_id=shared_drive,
        account=account,
    )

    if is_json_mode():
        print_json(
            {
                "documents": [
                    {"id": d.id, "title": d.title, "modified_time": d.modified_time} for d in docs
                ]
            }
        )
    else:
        if not docs:
            typer.echo("No documents found.")
            return

        rows = []
        for d in docs:
            doc_id = d.id[:16] + "..." if len(d.id) > 16 else d.id
            title = d.title[:50] + "..." if len(d.title) > 50 else d.title
            modified = str(d.modified_time)[:10] if d.modified_time else "-"
            rows.append([doc_id, title, modified])

        print_table("Documents", ["ID", "Title", "Modified"], rows)


@document_app.command("delete")
@require_auth
def delete_command(
    document_id: Annotated[str, typer.Argument(help="Document ID to delete")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Delete a document (move to trash)."""
    if not force:
        if not typer.confirm(f"Delete document {document_id}?"):
            raise typer.Abort()

    delete_document(document_id=document_id, account=account)

    if is_json_mode():
        print_json({"deleted": True, "id": document_id})
    else:
        print_success(f"Deleted: {document_id}")


@document_app.command("move")
@require_auth
def move_command(
    document_id: Annotated[str, typer.Argument(help="Document ID to move")],
    folder: Annotated[
        str,
        typer.Option("--folder", "-f", help="Target folder ID"),
    ],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Move a document to a folder.

    Works with regular folders and Shared Drive folders.
    """
    move_document(document_id=document_id, folder_id=folder, account=account)

    if is_json_mode():
        print_json({"moved": True, "id": document_id, "folder_id": folder})
    else:
        print_success(f"Moved {document_id} to folder {folder}")


@document_app.command("search")
@require_auth
def search_command(
    query: Annotated[str, typer.Argument(help="Search query (matches document title)")],
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum results"),
    ] = 20,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Search for documents by title."""
    docs = search_documents(query=query, limit=limit, account=account)

    if is_json_mode():
        print_json(
            {
                "query": query,
                "documents": [
                    {"id": d.id, "title": d.title, "modified_time": d.modified_time} for d in docs
                ],
            }
        )
    else:
        if not docs:
            typer.echo(f"No documents found matching '{query}'.")
            return

        rows = []
        for d in docs:
            doc_id = d.id[:16] + "..." if len(d.id) > 16 else d.id
            title = d.title[:50] + "..." if len(d.title) > 50 else d.title
            modified = str(d.modified_time)[:10] if d.modified_time else "-"
            rows.append([doc_id, title, modified])

        print_table(f"Search: '{query}'", ["ID", "Title", "Modified"], rows)


@document_app.command("share")
@require_auth
def share_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    email: Annotated[str, typer.Option("--email", "-e", help="Email to share with")],
    role: Annotated[
        str,
        typer.Option("--role", "-r", help="Permission role: reader, writer, commenter"),
    ] = "reader",
    no_notify: Annotated[
        bool,
        typer.Option("--no-notify", help="Don't send email notification"),
    ] = False,
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Message to include in notification"),
    ] = None,
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Share a document with a user.

    Roles:
      - reader: Can view
      - commenter: Can view and comment
      - writer: Can edit
    """
    if role not in ("reader", "writer", "commenter"):
        typer.echo(f"Invalid role: {role}. Must be reader, writer, or commenter.", err=True)
        raise typer.Exit(1)

    result = share_document(
        document_id=document_id,
        email=email,
        role=role,
        send_notification=not no_notify,
        message=message,
        account=account,
    )

    if is_json_mode():
        print_json(result)
    else:
        print_success(f"Shared with {email} as {role}")


@document_app.command("unshare")
@require_auth
def unshare_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    permission_id: Annotated[
        str,
        typer.Option("--permission", "-p", help="Permission ID to remove"),
    ],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """Remove sharing permission from a document.

    Use 'gdocs doc permissions <id>' to find permission IDs.
    """
    unshare_document(
        document_id=document_id,
        permission_id=permission_id,
        account=account,
    )

    if is_json_mode():
        print_json({"unshared": True, "permission_id": permission_id})
    else:
        print_success(f"Removed permission {permission_id}")


@document_app.command("permissions")
@require_auth
def permissions_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """List sharing permissions for a document."""
    permissions = list_permissions(document_id=document_id, account=account)

    if is_json_mode():
        print_json({"permissions": permissions})
    else:
        if not permissions:
            typer.echo("No permissions found.")
            return

        rows = []
        for p in permissions:
            perm_id = p.get("id", "-")[:16]
            perm_type = p.get("type", "-")
            role = p.get("role", "-")
            email = p.get("emailAddress", p.get("displayName", "-"))
            rows.append([perm_id, perm_type, role, email])

        print_table("Permissions", ["ID", "Type", "Role", "User"], rows)


@document_app.command("revisions")
@require_auth
def revisions_command(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to use"),
    ] = None,
) -> None:
    """List revision history of a document."""
    revisions = list_revisions(document_id=document_id, account=account)

    if is_json_mode():
        print_json({"revisions": revisions})
    else:
        if not revisions:
            typer.echo("No revisions found.")
            return

        rows = []
        for r in revisions:
            rev_id = r.get("id", "-")
            modified = r.get("modifiedTime", "-")[:19] if r.get("modifiedTime") else "-"
            user_info = r.get("lastModifyingUser", {})
            user = user_info.get("displayName", user_info.get("emailAddress", "-"))
            rows.append([rev_id, modified, user])

        print_table("Revisions", ["ID", "Modified", "User"], rows)
