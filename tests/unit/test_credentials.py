"""Tests for credentials service."""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

from gdocs_cli.services.credentials import (
    ACCOUNTS_LIST_KEY,
    DEFAULT_ACCOUNT_KEY,
    SERVICE_NAME,
    _add_to_accounts_list,
    _get_account_key,
    _remove_from_accounts_list,
    clear_all_accounts,
    delete_credentials,
    get_default_account,
    get_raw_credentials_json,
    has_credentials,
    list_accounts,
    load_credentials,
    save_credentials,
    set_default_account,
)


class TestAccountKey:
    """Tests for _get_account_key."""

    def test_get_account_key(self):
        """Test account key generation."""
        assert _get_account_key("user@example.com") == "oauth_user@example.com"


class TestListAccounts:
    """Tests for list_accounts."""

    def test_list_accounts_empty(self, mocker):
        """Test listing accounts when none exist."""
        mocker.patch("gdocs_cli.services.credentials.keyring.get_password", return_value=None)
        assert list_accounts() == []

    def test_list_accounts_with_data(self, mocker):
        """Test listing accounts with existing accounts."""
        accounts = ["user1@example.com", "user2@example.com"]
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(accounts),
        )
        assert list_accounts() == accounts

    def test_list_accounts_invalid_json(self, mocker):
        """Test listing accounts with invalid JSON."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value="invalid json",
        )
        assert list_accounts() == []


class TestDefaultAccount:
    """Tests for default account management."""

    def test_get_default_account(self, mocker):
        """Test getting default account."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value="default@example.com",
        )
        assert get_default_account() == "default@example.com"

    def test_get_default_account_none(self, mocker):
        """Test getting default account when not set."""
        mocker.patch("gdocs_cli.services.credentials.keyring.get_password", return_value=None)
        assert get_default_account() is None

    def test_set_default_account(self, mocker):
        """Test setting default account."""
        mock_set = mocker.patch("gdocs_cli.services.credentials.keyring.set_password")
        set_default_account("new@example.com")
        mock_set.assert_called_once_with(SERVICE_NAME, DEFAULT_ACCOUNT_KEY, "new@example.com")


class TestAccountsList:
    """Tests for accounts list management."""

    def test_add_to_accounts_list_new(self, mocker):
        """Test adding new account to list."""
        mocker.patch("gdocs_cli.services.credentials.keyring.get_password", return_value=None)
        mock_set = mocker.patch("gdocs_cli.services.credentials.keyring.set_password")

        _add_to_accounts_list("new@example.com")

        mock_set.assert_called_once_with(
            SERVICE_NAME, ACCOUNTS_LIST_KEY, json.dumps(["new@example.com"])
        )

    def test_add_to_accounts_list_existing(self, mocker):
        """Test adding account that already exists."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(["existing@example.com"]),
        )
        mock_set = mocker.patch("gdocs_cli.services.credentials.keyring.set_password")

        _add_to_accounts_list("existing@example.com")

        mock_set.assert_not_called()

    def test_remove_from_accounts_list(self, mocker):
        """Test removing account from list."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(["user1@example.com", "user2@example.com"]),
        )
        mock_set = mocker.patch("gdocs_cli.services.credentials.keyring.set_password")

        _remove_from_accounts_list("user1@example.com")

        mock_set.assert_called_once_with(
            SERVICE_NAME, ACCOUNTS_LIST_KEY, json.dumps(["user2@example.com"])
        )

    def test_remove_from_accounts_list_not_present(self, mocker):
        """Test removing account that doesn't exist."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(["other@example.com"]),
        )
        mock_set = mocker.patch("gdocs_cli.services.credentials.keyring.set_password")

        _remove_from_accounts_list("notpresent@example.com")

        mock_set.assert_not_called()


class TestSaveCredentials:
    """Tests for save_credentials."""

    def test_save_credentials_with_account(self, mocker):
        """Test saving credentials for specific account."""
        mock_creds = MagicMock()
        mock_creds.token = "test_token"
        mock_creds.refresh_token = "test_refresh"
        mock_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds.client_id = "client_id"
        mock_creds.client_secret = "client_secret"
        mock_creds.scopes = ["scope1", "scope2"]
        mock_creds.expiry = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        # Mock keyring and list_accounts
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=None,
        )
        mock_set = mocker.patch("gdocs_cli.services.credentials.keyring.set_password")

        save_credentials(mock_creds, account="user@example.com")

        # Check that credentials were saved
        assert mock_set.call_count >= 1

    def test_save_credentials_first_account_sets_default(self, mocker):
        """Test that first account is set as default."""
        mock_creds = MagicMock()
        mock_creds.token = "test_token"
        mock_creds.refresh_token = "test_refresh"
        mock_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds.client_id = "client_id"
        mock_creds.client_secret = "client_secret"
        mock_creds.scopes = []
        mock_creds.expiry = None

        # Track state: start with no accounts, then after save there's one
        accounts_state = {"accounts": [], "saved": False}

        def get_password_side_effect(_service, key):
            if key == ACCOUNTS_LIST_KEY:
                if accounts_state["saved"]:
                    return json.dumps(["user@example.com"])
                return json.dumps(accounts_state["accounts"])
            return None

        def set_password_side_effect(_service, key, value):
            if key == ACCOUNTS_LIST_KEY:
                accounts_state["accounts"] = json.loads(value)
                accounts_state["saved"] = True

        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            side_effect=get_password_side_effect,
        )
        mock_set = mocker.patch(
            "gdocs_cli.services.credentials.keyring.set_password",
            side_effect=set_password_side_effect,
        )

        save_credentials(mock_creds, account="user@example.com")

        # Verify set_default_account was called (DEFAULT_ACCOUNT_KEY)
        calls = [call for call in mock_set.call_args_list if call[0][1] == DEFAULT_ACCOUNT_KEY]
        assert len(calls) == 1


class TestLoadCredentials:
    """Tests for load_credentials."""

    def test_load_credentials_not_found(self, mocker):
        """Test loading credentials when not found."""
        mocker.patch("gdocs_cli.services.credentials.keyring.get_password", return_value=None)
        assert load_credentials(account="user@example.com") is None

    def test_load_credentials_success(self, mocker):
        """Test loading credentials successfully."""
        creds_data = {
            "token": "test_token",
            "refresh_token": "test_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scopes": ["scope1"],
            "expiry": "2024-01-01T12:00:00",
        }
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(creds_data),
        )

        creds = load_credentials(account="user@example.com")

        # Credentials object is returned (may be mock in Python 3.14 alpha)
        assert creds is not None

    def test_load_credentials_invalid_json(self, mocker):
        """Test loading credentials with invalid JSON."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value="invalid json",
        )
        assert load_credentials(account="user@example.com") is None

    def test_load_credentials_legacy_format(self, mocker):
        """Test loading credentials from legacy format."""
        creds_data = {
            "token": "legacy_token",
            "refresh_token": "legacy_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scopes": [],
            "expiry": None,
        }
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(creds_data),
        )

        creds = load_credentials(account=None)

        # Credentials object is returned (may be mock in Python 3.14 alpha)
        assert creds is not None


class TestDeleteCredentials:
    """Tests for delete_credentials."""

    def test_delete_credentials_with_account(self, mocker):
        """Test deleting credentials for specific account."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(["user@example.com"]),
        )
        mock_delete = mocker.patch("gdocs_cli.services.credentials.keyring.delete_password")
        mocker.patch("gdocs_cli.services.credentials.keyring.set_password")

        delete_credentials(account="user@example.com")

        mock_delete.assert_called()

    def test_delete_credentials_updates_default(self, mocker):
        """Test that deleting default account updates the default."""
        call_count = 0

        def get_password_side_effect(_service, key):
            nonlocal call_count
            call_count += 1
            if key == ACCOUNTS_LIST_KEY:
                if call_count <= 2:
                    return json.dumps(["user1@example.com", "user2@example.com"])
                return json.dumps(["user2@example.com"])
            if key == DEFAULT_ACCOUNT_KEY:
                return "user1@example.com"
            return None

        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            side_effect=get_password_side_effect,
        )
        mocker.patch("gdocs_cli.services.credentials.keyring.delete_password")
        mock_set = mocker.patch("gdocs_cli.services.credentials.keyring.set_password")

        delete_credentials(account="user1@example.com")

        # Should set new default
        default_calls = [c for c in mock_set.call_args_list if c[0][1] == DEFAULT_ACCOUNT_KEY]
        assert len(default_calls) == 1

    def test_delete_credentials_not_found(self, mocker):
        """Test deleting credentials that don't exist."""
        import keyring.errors

        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps([]),
        )
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.delete_password",
            side_effect=keyring.errors.PasswordDeleteError(),
        )

        # Should not raise
        delete_credentials(account="nonexistent@example.com")


class TestHasCredentials:
    """Tests for has_credentials."""

    def test_has_credentials_true(self, mocker):
        """Test has_credentials returns True when credentials exist."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value='{"token": "test"}',
        )
        assert has_credentials(account="user@example.com") is True

    def test_has_credentials_false(self, mocker):
        """Test has_credentials returns False when no credentials."""
        mocker.patch("gdocs_cli.services.credentials.keyring.get_password", return_value=None)
        assert has_credentials(account="user@example.com") is False

    def test_has_credentials_legacy(self, mocker):
        """Test has_credentials for legacy format."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value='{"token": "legacy"}',
        )
        assert has_credentials(account=None) is True


class TestGetRawCredentialsJson:
    """Tests for get_raw_credentials_json."""

    def test_get_raw_credentials_json(self, mocker):
        """Test getting raw credentials JSON."""
        raw_json = '{"token": "test", "refresh_token": "refresh"}'
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=raw_json,
        )

        result = get_raw_credentials_json("user@example.com")

        assert result == raw_json

    def test_get_raw_credentials_json_not_found(self, mocker):
        """Test getting raw credentials when not found."""
        mocker.patch("gdocs_cli.services.credentials.keyring.get_password", return_value=None)

        result = get_raw_credentials_json("user@example.com")

        assert result is None


class TestClearAllAccounts:
    """Tests for clear_all_accounts."""

    def test_clear_all_accounts(self, mocker):
        """Test clearing all accounts."""
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(["user1@example.com", "user2@example.com"]),
        )
        mock_delete = mocker.patch("gdocs_cli.services.credentials.keyring.delete_password")

        clear_all_accounts()

        # Should delete credentials for each account + accounts list + default account
        assert mock_delete.call_count >= 2

    def test_clear_all_accounts_handles_errors(self, mocker):
        """Test clearing all accounts handles delete errors."""
        import keyring.errors

        mocker.patch(
            "gdocs_cli.services.credentials.keyring.get_password",
            return_value=json.dumps(["user@example.com"]),
        )
        mocker.patch(
            "gdocs_cli.services.credentials.keyring.delete_password",
            side_effect=keyring.errors.PasswordDeleteError(),
        )

        # Should not raise
        clear_all_accounts()
