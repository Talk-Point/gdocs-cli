"""Pytest configuration and fixtures."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_credentials(mocker):
    """Mock credentials for testing."""
    mock_creds = mocker.MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.token = "test_token"
    mock_creds.refresh_token = "test_refresh_token"
    return mock_creds


@pytest.fixture
def mock_docs_service(mocker):
    """Mock Google Docs service."""
    return mocker.patch("gdocs_cli.services.docs.get_docs_service")


@pytest.fixture
def mock_drive_service(mocker):
    """Mock Google Drive service."""
    return mocker.patch("gdocs_cli.services.docs.get_drive_service")


@pytest.fixture
def mock_auth(mocker, mock_credentials):
    """Mock authentication for testing."""
    mocker.patch(
        "gdocs_cli.services.auth.get_credentials",
        return_value=mock_credentials,
    )
    mocker.patch(
        "gdocs_cli.services.auth.is_authenticated",
        return_value=True,
    )
    mocker.patch(
        "gdocs_cli.services.credentials.list_accounts",
        return_value=["test@example.com"],
    )
    return mock_credentials
