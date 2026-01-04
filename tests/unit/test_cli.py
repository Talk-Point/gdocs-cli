"""Tests for CLI commands."""

from typer.testing import CliRunner

from gdocs_cli.cli.main import app
from gdocs_cli.models.document import Document, DocumentSummary, Folder, SharedDrive

runner = CliRunner()


class TestMainCli:
    """Tests for main CLI."""

    def test_version(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "gdocs-cli version" in result.output

    def test_help(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "command-line interface for Google Docs" in result.output

    def test_no_args(self):
        """Test CLI with no args shows help."""
        result = runner.invoke(app, [])
        # Typer shows help and exits with 0 for no_args_is_help=True
        assert "Usage:" in result.output


class TestAuthCli:
    """Tests for auth CLI commands."""

    def test_auth_help(self):
        """Test auth --help."""
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output

    def test_auth_status_not_authenticated(self, mocker):
        """Test auth status when not authenticated."""
        mocker.patch("gdocs_cli.cli.auth.list_accounts", return_value=[])

        result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    def test_auth_status_authenticated(self, mocker):
        """Test auth status when authenticated."""
        mocker.patch(
            "gdocs_cli.cli.auth.list_accounts",
            return_value=["user@example.com"],
        )
        mocker.patch(
            "gdocs_cli.cli.auth.get_default_account",
            return_value="user@example.com",
        )
        mocker.patch("gdocs_cli.cli.auth.get_token_expiry", return_value="2024-01-15 12:00:00")

        result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "user@example.com" in result.output

    def test_auth_logout_success(self, mocker):
        """Test auth logout."""
        mocker.patch("gdocs_cli.cli.auth.logout", return_value=["user@example.com"])

        result = runner.invoke(app, ["auth", "logout", "--account", "user@example.com"])

        assert result.exit_code == 0
        assert "user@example.com" in result.output

    def test_auth_set_default(self, mocker):
        """Test auth set-default."""
        mocker.patch(
            "gdocs_cli.cli.auth.list_accounts",
            return_value=["user@example.com"],
        )
        mocker.patch("gdocs_cli.cli.auth.set_default_account")

        result = runner.invoke(app, ["auth", "set-default", "user@example.com"])

        assert result.exit_code == 0
        assert "Default account set" in result.output

    def test_auth_set_default_not_found(self, mocker):
        """Test auth set-default with non-existent account."""
        mocker.patch("gdocs_cli.cli.auth.list_accounts", return_value=[])

        result = runner.invoke(app, ["auth", "set-default", "notfound@example.com"])

        assert result.exit_code == 1
        assert "not found" in result.output


class TestDocumentCli:
    """Tests for document CLI commands."""

    def test_doc_help(self):
        """Test doc --help."""
        result = runner.invoke(app, ["doc", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output

    def test_doc_create_not_authenticated(self, mocker):
        """Test doc create when not authenticated."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=False)

        result = runner.invoke(app, ["doc", "create", "Test Doc"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    def test_doc_create_success(self, mocker):
        """Test doc create success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.create_document",
            return_value=Document(id="doc123", title="Test Doc"),
        )

        result = runner.invoke(app, ["doc", "create", "Test Doc"])

        assert result.exit_code == 0
        assert "Created" in result.output
        assert "doc123" in result.output

    def test_doc_get_success(self, mocker):
        """Test doc get success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.get_document",
            return_value=Document(id="doc123", title="Test Doc", revision_id="rev1"),
        )

        result = runner.invoke(app, ["doc", "get", "doc123"])

        assert result.exit_code == 0
        assert "Test Doc" in result.output

    def test_doc_list_success(self, mocker):
        """Test doc list success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.list_documents",
            return_value=[
                DocumentSummary(id="doc1", title="Doc 1"),
                DocumentSummary(id="doc2", title="Doc 2"),
            ],
        )

        result = runner.invoke(app, ["doc", "list"])

        assert result.exit_code == 0
        assert "Doc 1" in result.output or "Documents" in result.output

    def test_doc_list_empty(self, mocker):
        """Test doc list with no documents."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.document.list_documents", return_value=[])

        result = runner.invoke(app, ["doc", "list"])

        assert result.exit_code == 0
        assert "No documents found" in result.output

    def test_doc_delete_confirmed(self, mocker):
        """Test doc delete with confirmation."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.document.delete_document")

        result = runner.invoke(app, ["doc", "delete", "doc123", "--force"])

        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_doc_delete_aborted(self, mocker):
        """Test doc delete aborted."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)

        result = runner.invoke(app, ["doc", "delete", "doc123"], input="n\n")

        assert result.exit_code == 1

    def test_doc_move_success(self, mocker):
        """Test doc move success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.document.move_document")

        result = runner.invoke(app, ["doc", "move", "doc123", "--folder", "folder456"])

        assert result.exit_code == 0
        assert "Moved" in result.output


class TestContentCli:
    """Tests for content CLI commands."""

    def test_content_help(self):
        """Test content --help."""
        result = runner.invoke(app, ["content", "--help"])
        assert result.exit_code == 0
        assert "insert" in result.output
        assert "append" in result.output

    def test_content_insert_success(self, mocker):
        """Test content insert success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.content.batch_update", return_value={})

        result = runner.invoke(app, ["content", "insert", "doc123", "Hello World"])

        assert result.exit_code == 0
        assert "Inserted" in result.output

    def test_content_insert_with_heading(self, mocker):
        """Test content insert with heading."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.content.batch_update", return_value={})

        result = runner.invoke(
            app, ["content", "insert", "doc123", "Title", "--heading", "HEADING_1"]
        )

        assert result.exit_code == 0

    def test_content_insert_invalid_heading(self, mocker):
        """Test content insert with invalid heading."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)

        result = runner.invoke(
            app, ["content", "insert", "doc123", "Title", "--heading", "INVALID"]
        )

        assert result.exit_code == 1
        assert "Invalid heading" in result.output

    def test_content_append_success(self, mocker):
        """Test content append success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.content.batch_update", return_value={})

        result = runner.invoke(app, ["content", "append", "doc123", "More text"])

        assert result.exit_code == 0
        assert "Appended" in result.output

    def test_content_replace_success(self, mocker):
        """Test content replace success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.content.batch_update",
            return_value={"replies": [{"replaceAllText": {"occurrencesChanged": 3}}]},
        )

        result = runner.invoke(app, ["content", "replace", "doc123", "old", "new"])

        assert result.exit_code == 0
        assert "Replaced" in result.output


class TestTableCli:
    """Tests for table CLI commands."""

    def test_table_help(self):
        """Test table --help."""
        result = runner.invoke(app, ["table", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output

    def test_table_create_success(self, mocker):
        """Test table create success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.table.batch_update", return_value={})

        result = runner.invoke(app, ["table", "create", "doc123", "--rows", "3", "--columns", "4"])

        assert result.exit_code == 0
        assert "Created" in result.output
        assert "3x4" in result.output

    def test_table_list_success(self, mocker):
        """Test table list success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.table.get_document_content",
            return_value={
                "body": {
                    "content": [
                        {
                            "table": {"rows": 3, "columns": 4},
                            "startIndex": 10,
                            "endIndex": 100,
                        }
                    ]
                }
            },
        )

        result = runner.invoke(app, ["table", "list", "doc123"])

        assert result.exit_code == 0

    def test_table_list_empty(self, mocker):
        """Test table list with no tables."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.table.get_document_content",
            return_value={"body": {"content": []}},
        )

        result = runner.invoke(app, ["table", "list", "doc123"])

        assert result.exit_code == 0
        assert "No tables found" in result.output


class TestDrivesCli:
    """Tests for drives CLI commands."""

    def test_drives_help(self):
        """Test drives --help."""
        result = runner.invoke(app, ["drives", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "folders" in result.output

    def test_drives_list_success(self, mocker):
        """Test drives list success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.drives.list_shared_drives",
            return_value=[
                SharedDrive(id="drive1", name="Team Drive 1"),
                SharedDrive(id="drive2", name="Team Drive 2"),
            ],
        )

        result = runner.invoke(app, ["drives", "list"])

        assert result.exit_code == 0
        assert "Team Drive" in result.output or "Shared Drives" in result.output

    def test_drives_list_empty(self, mocker):
        """Test drives list with no drives."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.drives.list_shared_drives", return_value=[])

        result = runner.invoke(app, ["drives", "list"])

        assert result.exit_code == 0
        assert "No Shared Drives found" in result.output

    def test_drives_folders_success(self, mocker):
        """Test drives folders success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.drives.list_folders",
            return_value=[
                Folder(id="folder1", name="Folder 1"),
                Folder(id="folder2", name="Folder 2"),
            ],
        )

        result = runner.invoke(app, ["drives", "folders", "drive123"])

        assert result.exit_code == 0

    def test_drives_folders_empty(self, mocker):
        """Test drives folders with no folders."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.drives.list_folders", return_value=[])

        result = runner.invoke(app, ["drives", "folders"])

        assert result.exit_code == 0
        assert "No folders found" in result.output


class TestJsonOutput:
    """Tests for JSON output mode."""

    def test_doc_list_json(self, mocker):
        """Test doc list with --json flag."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.list_documents",
            return_value=[DocumentSummary(id="doc1", title="Doc 1")],
        )

        result = runner.invoke(app, ["--json", "doc", "list"])

        assert result.exit_code == 0
        assert '"documents"' in result.output

    def test_doc_create_json(self, mocker):
        """Test doc create with --json flag."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.create_document",
            return_value=Document(id="doc123", title="Test Doc"),
        )

        result = runner.invoke(app, ["--json", "doc", "create", "Test Doc"])

        assert result.exit_code == 0
        assert '"id"' in result.output
        assert "doc123" in result.output


class TestSearchCli:
    """Tests for search CLI command."""

    def test_doc_search_success(self, mocker):
        """Test doc search success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.search_documents",
            return_value=[
                DocumentSummary(id="doc1", title="Test Doc 1"),
                DocumentSummary(id="doc2", title="Test Doc 2"),
            ],
        )

        result = runner.invoke(app, ["doc", "search", "Test"])

        assert result.exit_code == 0
        assert "Test Doc" in result.output or "Search" in result.output

    def test_doc_search_empty(self, mocker):
        """Test doc search with no results."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.document.search_documents", return_value=[])

        result = runner.invoke(app, ["doc", "search", "nonexistent"])

        assert result.exit_code == 0
        assert "No documents found" in result.output

    def test_doc_search_json(self, mocker):
        """Test doc search with --json flag."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.search_documents",
            return_value=[DocumentSummary(id="doc1", title="Test")],
        )

        result = runner.invoke(app, ["--json", "doc", "search", "Test"])

        assert result.exit_code == 0
        assert '"query"' in result.output
        assert '"documents"' in result.output


class TestSharingCli:
    """Tests for sharing CLI commands."""

    def test_doc_permissions_success(self, mocker):
        """Test doc permissions listing."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.list_permissions",
            return_value=[
                {"id": "perm1", "type": "user", "role": "owner", "emailAddress": "owner@test.com"},
                {
                    "id": "perm2",
                    "type": "user",
                    "role": "reader",
                    "emailAddress": "reader@test.com",
                },
            ],
        )

        result = runner.invoke(app, ["doc", "permissions", "doc123"])

        assert result.exit_code == 0
        assert "Permissions" in result.output or "owner" in result.output

    def test_doc_permissions_empty(self, mocker):
        """Test doc permissions with no permissions."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.document.list_permissions", return_value=[])

        result = runner.invoke(app, ["doc", "permissions", "doc123"])

        assert result.exit_code == 0
        assert "No permissions found" in result.output

    def test_doc_share_success(self, mocker):
        """Test doc share success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.share_document",
            return_value={"id": "perm123", "type": "user", "role": "reader"},
        )

        result = runner.invoke(
            app, ["doc", "share", "doc123", "--email", "user@test.com", "--role", "reader"]
        )

        assert result.exit_code == 0
        assert "Shared" in result.output

    def test_doc_share_invalid_role(self, mocker):
        """Test doc share with invalid role."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)

        result = runner.invoke(
            app, ["doc", "share", "doc123", "--email", "user@test.com", "--role", "invalid"]
        )

        assert result.exit_code == 1
        assert "Invalid role" in result.output

    def test_doc_unshare_success(self, mocker):
        """Test doc unshare success."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.document.unshare_document")

        result = runner.invoke(app, ["doc", "unshare", "doc123", "--permission", "perm123"])

        assert result.exit_code == 0
        assert "Removed" in result.output


class TestRevisionsCli:
    """Tests for revisions CLI command."""

    def test_doc_revisions_success(self, mocker):
        """Test doc revisions listing."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.list_revisions",
            return_value=[
                {
                    "id": "1",
                    "modifiedTime": "2024-01-01T12:00:00Z",
                    "lastModifyingUser": {"displayName": "User"},
                },
                {
                    "id": "2",
                    "modifiedTime": "2024-01-02T12:00:00Z",
                    "lastModifyingUser": {"displayName": "User"},
                },
            ],
        )

        result = runner.invoke(app, ["doc", "revisions", "doc123"])

        assert result.exit_code == 0
        assert "Revisions" in result.output

    def test_doc_revisions_empty(self, mocker):
        """Test doc revisions with no revisions."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch("gdocs_cli.cli.document.list_revisions", return_value=[])

        result = runner.invoke(app, ["doc", "revisions", "doc123"])

        assert result.exit_code == 0
        assert "No revisions found" in result.output

    def test_doc_revisions_json(self, mocker):
        """Test doc revisions with --json flag."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.document.list_revisions",
            return_value=[{"id": "1", "modifiedTime": "2024-01-01T12:00:00Z"}],
        )

        result = runner.invoke(app, ["--json", "doc", "revisions", "doc123"])

        assert result.exit_code == 0
        assert '"revisions"' in result.output


class TestContentReadCli:
    """Tests for content read CLI command."""

    def test_content_read_markdown(self, mocker):
        """Test content read as markdown."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.content.get_document_content",
            return_value={
                "title": "Test Doc",
                "body": {
                    "content": [
                        {
                            "paragraph": {
                                "elements": [{"textRun": {"content": "Hello World\n"}}],
                                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            }
                        }
                    ]
                },
            },
        )

        result = runner.invoke(app, ["content", "read", "doc123"])

        assert result.exit_code == 0
        assert "Test Doc" in result.output
        assert "Hello World" in result.output

    def test_content_read_plain(self, mocker):
        """Test content read as plain text."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.content.get_document_content",
            return_value={
                "title": "Test Doc",
                "body": {
                    "content": [
                        {
                            "paragraph": {
                                "elements": [{"textRun": {"content": "Plain text\n"}}],
                            }
                        }
                    ]
                },
            },
        )

        result = runner.invoke(app, ["content", "read", "doc123", "--plain"])

        assert result.exit_code == 0
        assert "Plain text" in result.output

    def test_content_read_raw_json(self, mocker):
        """Test content read as raw JSON."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.content.get_document_content",
            return_value={"title": "Test", "body": {"content": []}},
        )

        result = runner.invoke(app, ["content", "read", "doc123", "--raw"])

        assert result.exit_code == 0
        assert '"title"' in result.output

    def test_content_read_with_table(self, mocker):
        """Test content read with table in document."""
        mocker.patch("gdocs_cli.cli.auth.is_authenticated", return_value=True)
        mocker.patch(
            "gdocs_cli.cli.content.get_document_content",
            return_value={
                "title": "Test Doc",
                "body": {
                    "content": [
                        {
                            "table": {
                                "tableRows": [
                                    {
                                        "tableCells": [
                                            {
                                                "content": [
                                                    {
                                                        "paragraph": {
                                                            "elements": [
                                                                {"textRun": {"content": "A\n"}}
                                                            ]
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                "content": [
                                                    {
                                                        "paragraph": {
                                                            "elements": [
                                                                {"textRun": {"content": "B\n"}}
                                                            ]
                                                        }
                                                    }
                                                ]
                                            },
                                        ]
                                    },
                                    {
                                        "tableCells": [
                                            {
                                                "content": [
                                                    {
                                                        "paragraph": {
                                                            "elements": [
                                                                {"textRun": {"content": "1\n"}}
                                                            ]
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                "content": [
                                                    {
                                                        "paragraph": {
                                                            "elements": [
                                                                {"textRun": {"content": "2\n"}}
                                                            ]
                                                        }
                                                    }
                                                ]
                                            },
                                        ]
                                    },
                                ]
                            }
                        }
                    ]
                },
            },
        )

        result = runner.invoke(app, ["content", "read", "doc123"])

        assert result.exit_code == 0
        assert "| A | B |" in result.output
        assert "| 1 | 2 |" in result.output
