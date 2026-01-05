"""Tests for auth service."""

import os
from unittest.mock import MagicMock

import pytest

from gdocs_cli.services.auth import (
    AccountNotFoundError,
    NoAccountConfiguredError,
    get_credentials,
    get_token_expiry,
    get_user_email,
    is_authenticated,
    logout,
    refresh_credentials,
    resolve_account,
)


class TestResolveAccount:
    """Tests for resolve_account."""

    def test_resolve_explicit_account(self, mocker):
        """Test resolving explicit account."""
        mocker.patch(
            "gdocs_cli.services.auth.list_accounts",
            return_value=["user@example.com", "other@example.com"],
        )

        result = resolve_account(explicit_account="user@example.com")

        assert result == "user@example.com"

    def test_resolve_explicit_account_not_found(self, mocker):
        """Test resolving explicit account that doesn't exist."""
        mocker.patch(
            "gdocs_cli.services.auth.list_accounts",
            return_value=["other@example.com"],
        )

        with pytest.raises(AccountNotFoundError) as exc_info:
            resolve_account(explicit_account="notfound@example.com")

        assert exc_info.value.account == "notfound@example.com"
        assert "other@example.com" in exc_info.value.available

    def test_resolve_env_variable(self, mocker):
        """Test resolving account from environment variable."""
        mocker.patch(
            "gdocs_cli.services.auth.list_accounts",
            return_value=["env@example.com"],
        )
        mocker.patch.dict(os.environ, {"GDOCS_ACCOUNT": "env@example.com"})

        result = resolve_account()

        assert result == "env@example.com"

    def test_resolve_env_variable_not_found(self, mocker):
        """Test resolving env account that doesn't exist."""
        mocker.patch(
            "gdocs_cli.services.auth.list_accounts",
            return_value=["other@example.com"],
        )
        mocker.patch.dict(os.environ, {"GDOCS_ACCOUNT": "notfound@example.com"})

        with pytest.raises(AccountNotFoundError):
            resolve_account()

    def test_resolve_default_account(self, mocker):
        """Test resolving configured default account."""
        mocker.patch(
            "gdocs_cli.services.auth.list_accounts",
            return_value=["default@example.com", "other@example.com"],
        )
        mocker.patch(
            "gdocs_cli.services.auth.get_default_account",
            return_value="default@example.com",
        )
        mocker.patch.dict(os.environ, {}, clear=True)
        # Clear GDOCS_ACCOUNT if it exists
        os.environ.pop("GDOCS_ACCOUNT", None)

        result = resolve_account()

        assert result == "default@example.com"

    def test_resolve_first_available(self, mocker):
        """Test resolving first available account."""
        mocker.patch(
            "gdocs_cli.services.auth.list_accounts",
            return_value=["first@example.com", "second@example.com"],
        )
        mocker.patch("gdocs_cli.services.auth.get_default_account", return_value=None)
        os.environ.pop("GDOCS_ACCOUNT", None)

        result = resolve_account()

        assert result == "first@example.com"

    def test_resolve_no_accounts(self, mocker):
        """Test resolving when no accounts configured."""
        mocker.patch("gdocs_cli.services.auth.list_accounts", return_value=[])
        mocker.patch("gdocs_cli.services.auth.get_default_account", return_value=None)
        os.environ.pop("GDOCS_ACCOUNT", None)

        with pytest.raises(NoAccountConfiguredError):
            resolve_account()


class TestGetCredentials:
    """Tests for get_credentials."""

    def test_get_credentials_success(self, mocker):
        """Test getting valid credentials."""
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_creds.valid = True

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)

        result = get_credentials()

        assert result == mock_creds

    def test_get_credentials_not_found(self, mocker):
        """Test getting credentials when not found."""
        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=None)

        result = get_credentials()

        assert result is None

    def test_get_credentials_no_account(self, mocker):
        """Test getting credentials when no account configured."""
        mocker.patch(
            "gdocs_cli.services.auth.resolve_account",
            side_effect=NoAccountConfiguredError(),
        )

        result = get_credentials()

        assert result is None

    def test_get_credentials_refresh_success(self, mocker):
        """Test refreshing expired credentials."""
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds.valid = True

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)
        mocker.patch("gdocs_cli.services.auth.save_credentials")

        result = get_credentials()

        assert result == mock_creds
        mock_creds.refresh.assert_called_once()

    def test_get_credentials_refresh_failed(self, mocker):
        """Test refresh failure deletes credentials."""
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds.refresh.side_effect = Exception("Refresh failed")

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)
        mock_delete = mocker.patch("gdocs_cli.services.auth.delete_credentials")

        result = get_credentials()

        assert result is None
        mock_delete.assert_called_once()


class TestIsAuthenticated:
    """Tests for is_authenticated."""

    def test_is_authenticated_true(self, mocker):
        """Test is_authenticated returns True."""
        mock_creds = MagicMock()
        mock_creds.valid = True

        mocker.patch("gdocs_cli.services.auth.get_credentials", return_value=mock_creds)

        assert is_authenticated(account="user@example.com") is True

    def test_is_authenticated_false_no_creds(self, mocker):
        """Test is_authenticated returns False when no credentials."""
        mocker.patch("gdocs_cli.services.auth.get_credentials", return_value=None)

        assert is_authenticated(account="user@example.com") is False

    def test_is_authenticated_false_invalid(self, mocker):
        """Test is_authenticated returns False when credentials invalid."""
        mock_creds = MagicMock()
        mock_creds.valid = False

        mocker.patch("gdocs_cli.services.auth.get_credentials", return_value=mock_creds)

        assert is_authenticated(account="user@example.com") is False

    def test_is_authenticated_any_account(self, mocker):
        """Test is_authenticated checks any account."""
        mock_creds = MagicMock()
        mock_creds.valid = True

        mocker.patch("gdocs_cli.services.auth.list_accounts", return_value=["first@example.com"])
        mocker.patch("gdocs_cli.services.auth.get_credentials", return_value=mock_creds)

        assert is_authenticated() is True

    def test_is_authenticated_no_accounts(self, mocker):
        """Test is_authenticated with no accounts."""
        mocker.patch("gdocs_cli.services.auth.list_accounts", return_value=[])

        assert is_authenticated() is False


class TestRefreshCredentials:
    """Tests for refresh_credentials."""

    def test_refresh_success(self, mocker):
        """Test successful refresh."""
        mock_creds = MagicMock()
        mock_creds.refresh_token = "refresh_token"

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)
        mocker.patch("gdocs_cli.services.auth.save_credentials")

        result = refresh_credentials()

        assert result is True
        mock_creds.refresh.assert_called_once()

    def test_refresh_no_account(self, mocker):
        """Test refresh with no account."""
        mocker.patch(
            "gdocs_cli.services.auth.resolve_account",
            side_effect=NoAccountConfiguredError(),
        )

        result = refresh_credentials()

        assert result is False

    def test_refresh_no_credentials(self, mocker):
        """Test refresh with no credentials."""
        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=None)

        result = refresh_credentials()

        assert result is False

    def test_refresh_no_refresh_token(self, mocker):
        """Test refresh with no refresh token."""
        mock_creds = MagicMock()
        mock_creds.refresh_token = None

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)

        result = refresh_credentials()

        assert result is False

    def test_refresh_failed(self, mocker):
        """Test refresh failure."""
        mock_creds = MagicMock()
        mock_creds.refresh_token = "refresh_token"
        mock_creds.refresh.side_effect = Exception("Refresh failed")

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)

        result = refresh_credentials()

        assert result is False


class TestGetUserEmail:
    """Tests for get_user_email."""

    def test_get_user_email_with_account(self):
        """Test get_user_email with explicit account."""
        result = get_user_email(account="user@example.com")

        assert result == "user@example.com"

    def test_get_user_email_resolved(self, mocker):
        """Test get_user_email resolves account."""
        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="resolved@example.com")

        result = get_user_email()

        assert result == "resolved@example.com"

    def test_get_user_email_no_account(self, mocker):
        """Test get_user_email with no account."""
        mocker.patch(
            "gdocs_cli.services.auth.resolve_account",
            side_effect=NoAccountConfiguredError(),
        )

        result = get_user_email()

        assert result is None


class TestGetTokenExpiry:
    """Tests for get_token_expiry."""

    def test_get_token_expiry_success(self, mocker):
        """Test getting token expiry."""
        from datetime import datetime

        mock_creds = MagicMock()
        mock_creds.expiry = datetime(2024, 1, 15, 12, 30, 45)

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)

        result = get_token_expiry()

        assert result == "2024-01-15 12:30:45"

    def test_get_token_expiry_no_expiry(self, mocker):
        """Test getting token expiry when not set."""
        mock_creds = MagicMock()
        mock_creds.expiry = None

        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="user@example.com")
        mocker.patch("gdocs_cli.services.auth.load_credentials", return_value=mock_creds)

        result = get_token_expiry()

        assert result is None

    def test_get_token_expiry_no_account(self, mocker):
        """Test getting token expiry with no account."""
        mocker.patch(
            "gdocs_cli.services.auth.resolve_account",
            side_effect=NoAccountConfiguredError(),
        )

        result = get_token_expiry()

        assert result is None


class TestLogout:
    """Tests for logout."""

    def test_logout_single_account(self, mocker):
        """Test logging out single account."""
        mock_delete = mocker.patch("gdocs_cli.services.auth.delete_credentials")

        result = logout(account="user@example.com")

        assert result == ["user@example.com"]
        mock_delete.assert_called_once_with(account="user@example.com")

    def test_logout_all_accounts(self, mocker):
        """Test logging out all accounts."""
        mocker.patch(
            "gdocs_cli.services.auth.list_accounts",
            return_value=["user1@example.com", "user2@example.com"],
        )
        mock_clear = mocker.patch("gdocs_cli.services.auth.clear_all_accounts")

        result = logout(all_accounts=True)

        assert result == ["user1@example.com", "user2@example.com"]
        mock_clear.assert_called_once()

    def test_logout_default_account(self, mocker):
        """Test logging out default account."""
        mocker.patch("gdocs_cli.services.auth.resolve_account", return_value="default@example.com")
        mock_delete = mocker.patch("gdocs_cli.services.auth.delete_credentials")

        result = logout()

        assert result == ["default@example.com"]
        mock_delete.assert_called_once()

    def test_logout_no_account_configured(self, mocker):
        """Test logging out with no account configured."""
        mocker.patch(
            "gdocs_cli.services.auth.resolve_account",
            side_effect=NoAccountConfiguredError(),
        )

        result = logout()

        assert result == []
