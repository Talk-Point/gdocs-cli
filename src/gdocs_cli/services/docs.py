"""Google Docs and Drive API service."""

import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gdocs_cli.models.document import Document, DocumentSummary, Folder, SharedDrive
from gdocs_cli.services.auth import get_credentials

MAX_RETRIES = 3
BASE_DELAY = 1


class TokenExpiredError(Exception):
    """Raised when the OAuth token has expired and cannot be refreshed."""

    def __init__(self, account: str | None = None) -> None:
        self.account = account
        super().__init__(f"Token expired for {account or 'account'}")


def get_docs_service(account: str | None = None):
    """Get authenticated Google Docs API service.

    Args:
        account: Account to use for authentication.

    Returns:
        Google Docs API service instance.

    Raises:
        Exception: If not authenticated.
    """
    credentials = get_credentials(account=account)
    if not credentials:
        raise Exception("Not authenticated. Run 'gdocs auth login' first.")
    return build("docs", "v1", credentials=credentials)


def get_drive_service(account: str | None = None):
    """Get authenticated Google Drive API service.

    Args:
        account: Account to use for authentication.

    Returns:
        Google Drive API service instance.

    Raises:
        Exception: If not authenticated.
    """
    credentials = get_credentials(account=account)
    if not credentials:
        raise Exception("Not authenticated. Run 'gdocs auth login' first.")
    return build("drive", "v3", credentials=credentials)


def _execute_with_retry(request, account: str | None = None):
    """Execute API request with exponential backoff.

    Args:
        request: API request to execute.
        account: Account for error context.

    Returns:
        API response.

    Raises:
        HttpError: If request fails after retries.
        TokenExpiredError: If token has expired.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status == 401:
                raise TokenExpiredError(account)
            if e.resp.status == 429:  # Rate limited
                delay = BASE_DELAY * (2**attempt)
                time.sleep(delay)
            else:
                raise
    return request.execute()  # Final attempt


# =============================================================================
# Document CRUD Operations
# =============================================================================


def create_document(
    title: str,
    folder_id: str | None = None,
    account: str | None = None,
) -> Document:
    """Create a new Google Doc, optionally in a specific folder/Shared Drive.

    Args:
        title: Document title.
        folder_id: Optional folder ID (works with Shared Drives too).
        account: Account to use.

    Returns:
        Created Document object.
    """
    docs_service = get_docs_service(account=account)
    body = {"title": title}
    request = docs_service.documents().create(body=body)
    response = _execute_with_retry(request, account=account)

    document_id = response["documentId"]

    # If folder specified, move to that folder (supports Shared Drives)
    if folder_id:
        drive_service = get_drive_service(account=account)

        # Get current parent (My Drive root)
        file = (
            drive_service.files()
            .get(
                fileId=document_id,
                fields="parents",
                supportsAllDrives=True,
            )
            .execute()
        )
        previous_parents = ",".join(file.get("parents", []))

        # Move to target folder
        drive_service.files().update(
            fileId=document_id,
            addParents=folder_id,
            removeParents=previous_parents,
            supportsAllDrives=True,
            fields="id, parents",
        ).execute()

    return Document(
        id=document_id,
        title=response["title"],
        revision_id=response.get("revisionId"),
    )


def get_document(document_id: str, account: str | None = None) -> Document:
    """Get document by ID.

    Args:
        document_id: The document ID.
        account: Account to use.

    Returns:
        Document with content.
    """
    service = get_docs_service(account=account)
    request = service.documents().get(documentId=document_id)
    response = _execute_with_retry(request, account=account)

    return Document(
        id=response["documentId"],
        title=response["title"],
        revision_id=response.get("revisionId"),
    )


def get_document_content(document_id: str, account: str | None = None) -> dict:
    """Get full document content including body.

    Args:
        document_id: The document ID.
        account: Account to use.

    Returns:
        Full document API response.
    """
    service = get_docs_service(account=account)
    request = service.documents().get(documentId=document_id)
    return _execute_with_retry(request, account=account)


def list_documents(
    limit: int = 20,
    folder_id: str | None = None,
    shared_drive_id: str | None = None,
    account: str | None = None,
) -> list[DocumentSummary]:
    """List Google Docs from Drive or Shared Drive.

    Args:
        limit: Maximum documents to return.
        folder_id: Optional folder ID to filter by.
        shared_drive_id: Optional Shared Drive ID.
        account: Account to use.

    Returns:
        List of document summaries.
    """
    service = get_drive_service(account=account)

    # Build query
    query = "mimeType='application/vnd.google-apps.document'"
    if folder_id:
        query += f" and '{folder_id}' in parents"

    # Build request parameters
    params = {
        "q": query,
        "pageSize": limit,
        "fields": "files(id, name, modifiedTime, parents)",
        "orderBy": "modifiedTime desc",
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }

    # If searching in a specific Shared Drive
    if shared_drive_id:
        params["corpora"] = "drive"
        params["driveId"] = shared_drive_id

    request = service.files().list(**params)
    response = _execute_with_retry(request, account=account)

    return [
        DocumentSummary(
            id=f["id"],
            title=f["name"],
            modified_time=f.get("modifiedTime"),
        )
        for f in response.get("files", [])
    ]


def delete_document(document_id: str, account: str | None = None) -> None:
    """Delete a document (move to trash).

    Args:
        document_id: Document ID to delete.
        account: Account to use.
    """
    service = get_drive_service(account=account)
    request = service.files().delete(
        fileId=document_id,
        supportsAllDrives=True,
    )
    _execute_with_retry(request, account=account)


def move_document(
    document_id: str,
    folder_id: str,
    account: str | None = None,
) -> None:
    """Move a document to a folder (supports Shared Drives).

    Args:
        document_id: Document to move.
        folder_id: Target folder ID.
        account: Account to use.
    """
    service = get_drive_service(account=account)

    # Get current parents
    file = (
        service.files()
        .get(
            fileId=document_id,
            fields="parents",
            supportsAllDrives=True,
        )
        .execute()
    )
    previous_parents = ",".join(file.get("parents", []))

    # Move file
    request = service.files().update(
        fileId=document_id,
        addParents=folder_id,
        removeParents=previous_parents,
        supportsAllDrives=True,
        fields="id, parents",
    )
    _execute_with_retry(request, account=account)


# =============================================================================
# Shared Drives Operations
# =============================================================================


def list_shared_drives(account: str | None = None) -> list[SharedDrive]:
    """List all Shared Drives the user has access to.

    Args:
        account: Account to use.

    Returns:
        List of shared drives.
    """
    service = get_drive_service(account=account)
    request = service.drives().list(pageSize=100)
    response = _execute_with_retry(request, account=account)

    return [SharedDrive(id=d["id"], name=d["name"]) for d in response.get("drives", [])]


def list_folders(
    parent_id: str | None = None,
    shared_drive_id: str | None = None,
    account: str | None = None,
) -> list[Folder]:
    """List folders in a location.

    Args:
        parent_id: Parent folder ID. If None, lists root folders.
        shared_drive_id: Shared Drive ID to list folders from.
        account: Account to use.

    Returns:
        List of folders.
    """
    service = get_drive_service(account=account)

    # Build query
    query = "mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    # Build request parameters
    params = {
        "q": query,
        "pageSize": 100,
        "fields": "files(id, name, parents)",
        "orderBy": "name",
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }

    if shared_drive_id:
        params["corpora"] = "drive"
        params["driveId"] = shared_drive_id

    request = service.files().list(**params)
    response = _execute_with_retry(request, account=account)

    return [
        Folder(
            id=f["id"],
            name=f["name"],
            parent_id=f.get("parents", [None])[0] if f.get("parents") else None,
        )
        for f in response.get("files", [])
    ]


# =============================================================================
# Sharing & Permissions Operations
# =============================================================================


def list_permissions(document_id: str, account: str | None = None) -> list[dict]:
    """List permissions for a document.

    Args:
        document_id: Document ID.
        account: Account to use.

    Returns:
        List of permission dictionaries.
    """
    service = get_drive_service(account=account)
    request = service.permissions().list(
        fileId=document_id,
        supportsAllDrives=True,
        fields="permissions(id, type, role, emailAddress, displayName)",
    )
    response = _execute_with_retry(request, account=account)
    return response.get("permissions", [])


def share_document(
    document_id: str,
    email: str,
    role: str = "reader",
    send_notification: bool = True,
    message: str | None = None,
    account: str | None = None,
) -> dict:
    """Share a document with a user.

    Args:
        document_id: Document ID.
        email: Email address to share with.
        role: Permission role (reader, writer, commenter).
        send_notification: Whether to send email notification.
        message: Optional message in notification.
        account: Account to use.

    Returns:
        Created permission.
    """
    service = get_drive_service(account=account)

    permission = {
        "type": "user",
        "role": role,
        "emailAddress": email,
    }

    request = service.permissions().create(
        fileId=document_id,
        body=permission,
        sendNotificationEmail=send_notification,
        emailMessage=message,
        supportsAllDrives=True,
        fields="id, type, role, emailAddress",
    )
    return _execute_with_retry(request, account=account)


def unshare_document(
    document_id: str,
    permission_id: str,
    account: str | None = None,
) -> None:
    """Remove a permission from a document.

    Args:
        document_id: Document ID.
        permission_id: Permission ID to remove.
        account: Account to use.
    """
    service = get_drive_service(account=account)
    request = service.permissions().delete(
        fileId=document_id,
        permissionId=permission_id,
        supportsAllDrives=True,
    )
    _execute_with_retry(request, account=account)


# =============================================================================
# Revision History Operations
# =============================================================================


def list_revisions(document_id: str, account: str | None = None) -> list[dict]:
    """List revisions of a document.

    Args:
        document_id: Document ID.
        account: Account to use.

    Returns:
        List of revision dictionaries.
    """
    service = get_drive_service(account=account)
    request = service.revisions().list(
        fileId=document_id,
        fields="revisions(id, modifiedTime, lastModifyingUser)",
    )
    response = _execute_with_retry(request, account=account)
    return response.get("revisions", [])


# =============================================================================
# Search Operations
# =============================================================================


def search_documents(
    query: str,
    limit: int = 20,
    account: str | None = None,
) -> list[DocumentSummary]:
    """Search for documents by name.

    Args:
        query: Search query (matches document title).
        limit: Maximum results.
        account: Account to use.

    Returns:
        List of matching documents.
    """
    service = get_drive_service(account=account)

    # Build query - search in name
    full_query = f"mimeType='application/vnd.google-apps.document' and name contains '{query}'"

    params = {
        "q": full_query,
        "pageSize": limit,
        "fields": "files(id, name, modifiedTime)",
        "orderBy": "modifiedTime desc",
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }

    request = service.files().list(**params)
    response = _execute_with_retry(request, account=account)

    return [
        DocumentSummary(
            id=f["id"],
            title=f["name"],
            modified_time=f.get("modifiedTime"),
        )
        for f in response.get("files", [])
    ]


# =============================================================================
# BatchUpdate Operations
# =============================================================================


def batch_update(
    document_id: str,
    requests: list[dict],
    account: str | None = None,
) -> dict:
    """Execute batch update on document.

    Args:
        document_id: Target document ID.
        requests: List of update requests.
        account: Account to use.

    Returns:
        API response.
    """
    service = get_docs_service(account=account)
    body = {"requests": requests}
    request = service.documents().batchUpdate(
        documentId=document_id,
        body=body,
    )
    return _execute_with_retry(request, account=account)
