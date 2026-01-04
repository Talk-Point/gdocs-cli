"""Keyring storage service for OAuth credentials with multi-account support."""

import json
from datetime import datetime

import keyring
from google.oauth2.credentials import Credentials

SERVICE_NAME = "gdocs-cli"
LEGACY_ACCOUNT_NAME = "oauth_credentials"  # Legacy single-account key
ACCOUNTS_LIST_KEY = "accounts_list"
DEFAULT_ACCOUNT_KEY = "default_account"


def _get_account_key(email: str) -> str:
    """Get keyring key for account-specific credentials.

    Args:
        email: Account email address.

    Returns:
        Keyring key string for the account.
    """
    return f"oauth_{email}"


def list_accounts() -> list[str]:
    """List all authenticated accounts.

    Returns:
        List of account email addresses.
    """
    data = keyring.get_password(SERVICE_NAME, ACCOUNTS_LIST_KEY)
    if not data:
        return []
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return []


def get_default_account() -> str | None:
    """Get the default account email.

    Returns:
        Default account email or None if not set.
    """
    return keyring.get_password(SERVICE_NAME, DEFAULT_ACCOUNT_KEY)


def set_default_account(account: str) -> None:
    """Set the default account.

    Args:
        account: Email address to set as default.
    """
    keyring.set_password(SERVICE_NAME, DEFAULT_ACCOUNT_KEY, account)


def _add_to_accounts_list(account: str) -> None:
    """Add an account to the accounts list if not already present.

    Args:
        account: Email address to add.
    """
    accounts = list_accounts()
    if account not in accounts:
        accounts.append(account)
        keyring.set_password(SERVICE_NAME, ACCOUNTS_LIST_KEY, json.dumps(accounts))


def _remove_from_accounts_list(account: str) -> None:
    """Remove an account from the accounts list.

    Args:
        account: Email address to remove.
    """
    accounts = list_accounts()
    if account in accounts:
        accounts.remove(account)
        keyring.set_password(SERVICE_NAME, ACCOUNTS_LIST_KEY, json.dumps(accounts))


def save_credentials(credentials: Credentials, account: str | None = None) -> None:
    """Save OAuth credentials to system keyring.

    Args:
        credentials: Google OAuth credentials to store.
        account: Account email address. If None, uses legacy single-account format.
    """
    creds_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else [],
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }

    if account:
        # Multi-account format
        keyring.set_password(SERVICE_NAME, _get_account_key(account), json.dumps(creds_data))
        _add_to_accounts_list(account)

        # Set as default if first account
        if len(list_accounts()) == 1:
            set_default_account(account)
    else:
        # Legacy single-account format (for backward compatibility)
        keyring.set_password(SERVICE_NAME, LEGACY_ACCOUNT_NAME, json.dumps(creds_data))


def load_credentials(account: str | None = None) -> Credentials | None:
    """Load OAuth credentials from system keyring.

    Args:
        account: Account email to load. If None, tries legacy format.

    Returns:
        Credentials object if found, None otherwise.
    """
    if account:
        # Multi-account format
        creds_json = keyring.get_password(SERVICE_NAME, _get_account_key(account))
    else:
        # Legacy single-account format
        creds_json = keyring.get_password(SERVICE_NAME, LEGACY_ACCOUNT_NAME)

    if not creds_json:
        return None

    try:
        creds_data = json.loads(creds_json)
        expiry = None
        if creds_data.get("expiry"):
            expiry = datetime.fromisoformat(creds_data["expiry"])

        return Credentials(
            token=creds_data["token"],
            refresh_token=creds_data["refresh_token"],
            token_uri=creds_data["token_uri"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            scopes=creds_data.get("scopes", []),
            expiry=expiry,
        )
    except (json.JSONDecodeError, KeyError):
        return None


def delete_credentials(account: str | None = None) -> None:
    """Delete OAuth credentials from system keyring.

    Args:
        account: Account email to delete. If None, deletes legacy format.
    """
    try:
        if account:
            # Multi-account format
            keyring.delete_password(SERVICE_NAME, _get_account_key(account))
            _remove_from_accounts_list(account)

            # Update default if deleted account was default
            default = get_default_account()
            if default == account:
                accounts = list_accounts()
                if accounts:
                    set_default_account(accounts[0])
                else:
                    try:
                        keyring.delete_password(SERVICE_NAME, DEFAULT_ACCOUNT_KEY)
                    except keyring.errors.PasswordDeleteError:
                        pass
        else:
            # Legacy single-account format
            keyring.delete_password(SERVICE_NAME, LEGACY_ACCOUNT_NAME)
    except keyring.errors.PasswordDeleteError:
        pass


def has_credentials(account: str | None = None) -> bool:
    """Check if credentials exist in keyring.

    Args:
        account: Account email to check. If None, checks legacy format.

    Returns:
        True if credentials exist, False otherwise.
    """
    if account:
        return keyring.get_password(SERVICE_NAME, _get_account_key(account)) is not None
    return keyring.get_password(SERVICE_NAME, LEGACY_ACCOUNT_NAME) is not None


def get_raw_credentials_json(account: str) -> str | None:
    """Get raw credentials JSON for an account.

    This is useful for exporting credentials to transfer to another machine.

    Args:
        account: Account email to get credentials for.

    Returns:
        Raw JSON string of credentials or None if not found.
    """
    return keyring.get_password(SERVICE_NAME, _get_account_key(account))


def clear_all_accounts() -> None:
    """Clear all accounts and credentials from keyring.

    Used for logout --all functionality.
    """
    accounts = list_accounts()
    for account in accounts:
        try:
            keyring.delete_password(SERVICE_NAME, _get_account_key(account))
        except keyring.errors.PasswordDeleteError:
            pass

    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNTS_LIST_KEY)
    except keyring.errors.PasswordDeleteError:
        pass

    try:
        keyring.delete_password(SERVICE_NAME, DEFAULT_ACCOUNT_KEY)
    except keyring.errors.PasswordDeleteError:
        pass
