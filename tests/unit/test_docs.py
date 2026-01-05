"""Tests for docs service."""

from unittest.mock import MagicMock

from gdocs_cli.services.docs import (
    _execute_with_retry,
    batch_update,
    create_document,
    delete_document,
    get_document,
    get_document_content,
    list_documents,
    list_folders,
    list_shared_drives,
    move_document,
)


class TestExecuteWithRetry:
    """Tests for _execute_with_retry."""

    def test_execute_success(self):
        """Test successful execution."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"result": "success"}

        result = _execute_with_retry(mock_request)

        assert result == {"result": "success"}
        mock_request.execute.assert_called_once()

    # Note: HttpError tests are skipped in Python 3.14 alpha due to import issues
    # with google-api-python-client. These will work in stable Python versions.


class TestCreateDocument:
    """Tests for create_document."""

    def test_create_document_simple(self, mocker):
        """Test creating a simple document."""
        mock_docs_service = MagicMock()
        mock_docs_service.documents().create().execute.return_value = {
            "documentId": "doc123",
            "title": "Test Doc",
            "revisionId": "rev1",
        }

        mocker.patch("gdocs_cli.services.docs.get_docs_service", return_value=mock_docs_service)

        result = create_document("Test Doc")

        assert result.id == "doc123"
        assert result.title == "Test Doc"

    def test_create_document_in_folder(self, mocker):
        """Test creating document in a folder."""
        mock_docs_service = MagicMock()
        mock_docs_service.documents().create().execute.return_value = {
            "documentId": "doc123",
            "title": "Test Doc",
        }

        mock_drive_service = MagicMock()
        mock_drive_service.files().get().execute.return_value = {"parents": ["root"]}
        mock_drive_service.files().update().execute.return_value = {}

        mocker.patch("gdocs_cli.services.docs.get_docs_service", return_value=mock_docs_service)
        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_drive_service)

        result = create_document("Test Doc", folder_id="folder123")

        assert result.id == "doc123"
        mock_drive_service.files().update.assert_called()


class TestGetDocument:
    """Tests for get_document."""

    def test_get_document_success(self, mocker):
        """Test getting document successfully."""
        mock_service = MagicMock()
        mock_service.documents().get().execute.return_value = {
            "documentId": "doc123",
            "title": "Test Doc",
            "revisionId": "rev1",
        }

        mocker.patch("gdocs_cli.services.docs.get_docs_service", return_value=mock_service)

        result = get_document("doc123")

        assert result.id == "doc123"
        assert result.title == "Test Doc"
        assert result.revision_id == "rev1"


class TestGetDocumentContent:
    """Tests for get_document_content."""

    def test_get_document_content(self, mocker):
        """Test getting full document content."""
        mock_service = MagicMock()
        expected_content = {
            "documentId": "doc123",
            "title": "Test Doc",
            "body": {"content": [{"paragraph": {}}]},
        }
        mock_service.documents().get().execute.return_value = expected_content

        mocker.patch("gdocs_cli.services.docs.get_docs_service", return_value=mock_service)

        result = get_document_content("doc123")

        assert result == expected_content


class TestListDocuments:
    """Tests for list_documents."""

    def test_list_documents_simple(self, mocker):
        """Test listing documents."""
        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {"id": "doc1", "name": "Doc 1", "modifiedTime": "2024-01-01T00:00:00Z"},
                {"id": "doc2", "name": "Doc 2", "modifiedTime": "2024-01-02T00:00:00Z"},
            ]
        }

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_documents()

        assert len(result) == 2
        assert result[0].id == "doc1"
        assert result[0].title == "Doc 1"

    def test_list_documents_with_folder(self, mocker):
        """Test listing documents in folder."""
        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {"files": []}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        list_documents(folder_id="folder123")

        # Check that folder was included in query
        call_kwargs = mock_service.files().list.call_args[1]
        assert "folder123" in call_kwargs["q"]

    def test_list_documents_shared_drive(self, mocker):
        """Test listing documents from shared drive."""
        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {"files": []}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        list_documents(shared_drive_id="drive123")

        call_kwargs = mock_service.files().list.call_args[1]
        assert call_kwargs["corpora"] == "drive"
        assert call_kwargs["driveId"] == "drive123"


class TestDeleteDocument:
    """Tests for delete_document."""

    def test_delete_document(self, mocker):
        """Test deleting document."""
        mock_service = MagicMock()

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        delete_document("doc123")

        mock_service.files().delete.assert_called_with(
            fileId="doc123",
            supportsAllDrives=True,
        )


class TestMoveDocument:
    """Tests for move_document."""

    def test_move_document(self, mocker):
        """Test moving document."""
        mock_service = MagicMock()
        mock_service.files().get().execute.return_value = {"parents": ["old_folder"]}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        move_document("doc123", "new_folder")

        mock_service.files().update.assert_called()
        call_kwargs = mock_service.files().update.call_args[1]
        assert call_kwargs["addParents"] == "new_folder"
        assert call_kwargs["removeParents"] == "old_folder"


class TestListSharedDrives:
    """Tests for list_shared_drives."""

    def test_list_shared_drives(self, mocker):
        """Test listing shared drives."""
        mock_service = MagicMock()
        mock_service.drives().list().execute.return_value = {
            "drives": [
                {"id": "drive1", "name": "Team Drive 1"},
                {"id": "drive2", "name": "Team Drive 2"},
            ]
        }

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_shared_drives()

        assert len(result) == 2
        assert result[0].id == "drive1"
        assert result[0].name == "Team Drive 1"

    def test_list_shared_drives_empty(self, mocker):
        """Test listing shared drives when none exist."""
        mock_service = MagicMock()
        mock_service.drives().list().execute.return_value = {"drives": []}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_shared_drives()

        assert result == []


class TestListFolders:
    """Tests for list_folders."""

    def test_list_folders(self, mocker):
        """Test listing folders."""
        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {"id": "folder1", "name": "Folder 1", "parents": ["root"]},
                {"id": "folder2", "name": "Folder 2", "parents": ["folder1"]},
            ]
        }

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_folders()

        assert len(result) == 2
        assert result[0].id == "folder1"
        assert result[0].name == "Folder 1"
        assert result[0].parent_id == "root"

    def test_list_folders_with_parent(self, mocker):
        """Test listing folders with parent filter."""
        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {"files": []}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        list_folders(parent_id="parent123")

        call_kwargs = mock_service.files().list.call_args[1]
        assert "parent123" in call_kwargs["q"]


class TestBatchUpdate:
    """Tests for batch_update."""

    def test_batch_update(self, mocker):
        """Test batch update."""
        mock_service = MagicMock()
        mock_service.documents().batchUpdate().execute.return_value = {
            "replies": [{"insertText": {}}]
        }

        mocker.patch("gdocs_cli.services.docs.get_docs_service", return_value=mock_service)

        requests = [{"insertText": {"text": "Hello", "location": {"index": 1}}}]
        result = batch_update("doc123", requests)

        assert "replies" in result
        mock_service.documents().batchUpdate.assert_called_with(
            documentId="doc123",
            body={"requests": requests},
        )


class TestSearchDocuments:
    """Tests for search_documents."""

    def test_search_documents(self, mocker):
        """Test searching documents."""
        from gdocs_cli.services.docs import search_documents

        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {"id": "doc1", "name": "Test Doc 1", "modifiedTime": "2024-01-01T00:00:00Z"},
                {"id": "doc2", "name": "Test Doc 2", "modifiedTime": "2024-01-02T00:00:00Z"},
            ]
        }

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = search_documents("Test")

        assert len(result) == 2
        assert result[0].id == "doc1"
        assert result[0].title == "Test Doc 1"

    def test_search_documents_empty(self, mocker):
        """Test searching with no results."""
        from gdocs_cli.services.docs import search_documents

        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {"files": []}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = search_documents("nonexistent")

        assert result == []


class TestListPermissions:
    """Tests for list_permissions."""

    def test_list_permissions(self, mocker):
        """Test listing permissions."""
        from gdocs_cli.services.docs import list_permissions

        mock_service = MagicMock()
        mock_service.permissions().list().execute.return_value = {
            "permissions": [
                {"id": "perm1", "type": "user", "role": "owner", "emailAddress": "owner@test.com"},
                {
                    "id": "perm2",
                    "type": "user",
                    "role": "reader",
                    "emailAddress": "reader@test.com",
                },
            ]
        }

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_permissions("doc123")

        assert len(result) == 2
        assert result[0]["role"] == "owner"

    def test_list_permissions_empty(self, mocker):
        """Test listing permissions when none exist."""
        from gdocs_cli.services.docs import list_permissions

        mock_service = MagicMock()
        mock_service.permissions().list().execute.return_value = {"permissions": []}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_permissions("doc123")

        assert result == []


class TestShareDocument:
    """Tests for share_document."""

    def test_share_document(self, mocker):
        """Test sharing a document."""
        from gdocs_cli.services.docs import share_document

        mock_service = MagicMock()
        mock_service.permissions().create().execute.return_value = {
            "id": "perm123",
            "type": "user",
            "role": "reader",
            "emailAddress": "user@test.com",
        }

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = share_document("doc123", "user@test.com", role="reader")

        assert result["id"] == "perm123"
        assert result["role"] == "reader"


class TestUnshareDocument:
    """Tests for unshare_document."""

    def test_unshare_document(self, mocker):
        """Test removing a permission."""
        from gdocs_cli.services.docs import unshare_document

        mock_service = MagicMock()
        mock_service.permissions().delete().execute.return_value = None

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        # Should not raise
        unshare_document("doc123", "perm123")

        mock_service.permissions().delete.assert_called()


class TestListRevisions:
    """Tests for list_revisions."""

    def test_list_revisions(self, mocker):
        """Test listing revisions."""
        from gdocs_cli.services.docs import list_revisions

        mock_service = MagicMock()
        mock_service.revisions().list().execute.return_value = {
            "revisions": [
                {"id": "1", "modifiedTime": "2024-01-01T12:00:00Z"},
                {"id": "2", "modifiedTime": "2024-01-02T12:00:00Z"},
            ]
        }

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_revisions("doc123")

        assert len(result) == 2
        assert result[0]["id"] == "1"

    def test_list_revisions_empty(self, mocker):
        """Test listing revisions when none exist."""
        from gdocs_cli.services.docs import list_revisions

        mock_service = MagicMock()
        mock_service.revisions().list().execute.return_value = {"revisions": []}

        mocker.patch("gdocs_cli.services.docs.get_drive_service", return_value=mock_service)

        result = list_revisions("doc123")

        assert result == []
