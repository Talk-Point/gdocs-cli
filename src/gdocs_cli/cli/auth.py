"""Authentication CLI commands."""

from collections.abc import Callable
from functools import wraps
from typing import Annotated, Any

import typer

from gdocs_cli.services.auth import (
    get_token_expiry,
    is_authenticated,
    logout,
    run_oauth_flow,
)
from gdocs_cli.services.credentials import (
    delete_credentials,
    get_default_account,
    get_raw_credentials_json,
    has_credentials,
    list_accounts,
    set_default_account,
)
from gdocs_cli.services.docs import TokenExpiredError
from gdocs_cli.utils.output import (
    is_json_mode,
    print_error,
    print_json,
    print_json_error,
    print_success,
)

auth_app = typer.Typer(
    name="auth",
    help="Manage Google Docs authentication.",
    no_args_is_help=True,
)


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require authentication for a command.

    Args:
        func: The command function to wrap.

    Returns:
        Wrapped function that checks authentication first.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_authenticated():
            if is_json_mode():
                print_json_error(
                    "NOT_AUTHENTICATED",
                    "Not authenticated",
                    "Run 'gdocs auth login' to authenticate.",
                )
            else:
                print_error(
                    "Not authenticated",
                    tip="Run 'gdocs auth login' to authenticate.",
                )
            raise typer.Exit(1)
        try:
            return func(*args, **kwargs)
        except TokenExpiredError as e:
            if e.account:
                delete_credentials(account=e.account)
            if is_json_mode():
                print_json_error(
                    "TOKEN_EXPIRED",
                    f"Token expired for {e.account or 'account'}",
                    "Run 'gdocs auth login' to re-authenticate.",
                )
            else:
                print_error(
                    f"Token expired for {e.account or 'account'}",
                    tip="Run 'gdocs auth login' to re-authenticate.",
                )
            raise typer.Exit(1)

    return wrapper


@auth_app.command("login")
def login(
    set_default: Annotated[
        bool,
        typer.Option("--set-default", help="Set this account as the default account."),
    ] = False,
) -> None:
    """Authenticate with Google using OAuth 2.0.

    Supports multiple accounts. The first account authenticated becomes the default.
    Use --set-default to make a new account the default.
    """
    accounts = list_accounts()
    if accounts and has_credentials(account=accounts[0]):
        if not typer.confirm("You already have authenticated accounts. Add another account?"):
            if is_json_mode():
                print_json({"status": "cancelled", "message": "Login cancelled"})
            else:
                print_success("Keeping existing authentication")
            return

    try:
        credentials, email = run_oauth_flow()

        was_first_account = len(accounts) == 0
        is_default = was_first_account or set_default

        if set_default and not was_first_account:
            set_default_account(email)

        if is_json_mode():
            print_json(
                {
                    "status": "authenticated",
                    "email": email,
                    "is_default": is_default,
                    "scopes": list(credentials.scopes) if credentials.scopes else [],
                }
            )
        else:
            if is_default:
                print_success(f"Successfully authenticated as {email} (default account)")
            else:
                print_success(f"Successfully authenticated as {email}")

    except FileNotFoundError as e:
        if is_json_mode():
            print_json_error("CREDENTIALS_NOT_FOUND", str(e))
        else:
            print_error(
                "credentials.json not found",
                details=str(e),
                tip="Ensure the OAuth credentials file exists in the current directory.",
            )
        raise typer.Exit(2)

    except Exception as e:
        if is_json_mode():
            print_json_error("AUTH_FAILED", "Authentication failed", str(e))
        else:
            print_error(
                "Authentication failed",
                details=str(e),
            )
        raise typer.Exit(1)


@auth_app.command("logout")
def logout_command(
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Specific account to log out."),
    ] = None,
    all_accounts: Annotated[
        bool,
        typer.Option("--all", help="Log out all accounts."),
    ] = False,
) -> None:
    """Log out and delete stored credentials.

    Without options, logs out the default account.
    Use --account to log out a specific account.
    Use --all to log out all accounts.
    """
    logged_out = logout(account=account, all_accounts=all_accounts)

    if is_json_mode():
        print_json({"status": "logged_out", "accounts": logged_out})
    else:
        if not logged_out:
            print_success("No accounts logged out")
        elif len(logged_out) == 1:
            print_success(f"Successfully logged out: {logged_out[0]}")
        else:
            print_success(f"Successfully logged out: {', '.join(logged_out)}")


@auth_app.command("status")
def status() -> None:
    """Show current authentication status.

    Lists all configured accounts with their status.
    The default account is marked with an asterisk (*).
    """
    accounts = list_accounts()
    default = get_default_account()

    if not accounts:
        if is_json_mode():
            print_json({"authenticated": False, "accounts": []})
        else:
            print_error(
                "Not authenticated",
                tip="Run 'gdocs auth login' to authenticate.",
            )
        raise typer.Exit(1)

    if is_json_mode():
        accounts_info = []
        for acc in accounts:
            expiry = get_token_expiry(account=acc)
            accounts_info.append(
                {
                    "email": acc,
                    "is_default": acc == default,
                    "token_expiry": expiry,
                }
            )
        print_json(
            {
                "authenticated": True,
                "default_account": default,
                "accounts": accounts_info,
            }
        )
    else:
        print_success(f"Authenticated with {len(accounts)} account(s):")
        for acc in accounts:
            marker = " *" if acc == default else ""
            expiry = get_token_expiry(account=acc)
            expiry_info = f" (token expires: {expiry})" if expiry else ""
            typer.echo(f"  {acc}{marker}{expiry_info}")


@auth_app.command("set-default")
def set_default_command(
    email: Annotated[
        str,
        typer.Argument(help="Email address of the account to set as default."),
    ],
) -> None:
    """Set the default account for commands.

    The default account is used when no --account option is specified.
    """
    accounts = list_accounts()

    if email not in accounts:
        if is_json_mode():
            print_json_error(
                "ACCOUNT_NOT_FOUND",
                f"Account '{email}' not found",
                f"Available accounts: {', '.join(accounts)}",
            )
        else:
            print_error(
                f"Account '{email}' not found",
                tip=f"Available accounts: {', '.join(accounts)}",
            )
        raise typer.Exit(1)

    set_default_account(email)

    if is_json_mode():
        print_json({"status": "default_set", "account": email})
    else:
        print_success(f"Default account set: {email}")


@auth_app.command("token")
def token_command(
    account: Annotated[
        str | None,
        typer.Option("--account", "-A", help="Account to show token for."),
    ] = None,
) -> None:
    """Show credentials JSON for server deployment.

    Outputs the raw OAuth credentials as JSON, which can be used to
    transfer authentication to a headless server.

    WARNING: This contains sensitive data. Handle with care!
    """
    accounts = list_accounts()

    if not accounts:
        if is_json_mode():
            print_json_error("NOT_AUTHENTICATED", "No accounts configured")
        else:
            print_error(
                "No accounts configured",
                tip="Run 'gdocs auth login' to authenticate.",
            )
        raise typer.Exit(1)

    target_account = account or get_default_account() or accounts[0]

    if target_account not in accounts:
        if is_json_mode():
            print_json_error(
                "ACCOUNT_NOT_FOUND",
                f"Account '{target_account}' not found",
                f"Available accounts: {', '.join(accounts)}",
            )
        else:
            print_error(
                f"Account '{target_account}' not found",
                tip=f"Available accounts: {', '.join(accounts)}",
            )
        raise typer.Exit(1)

    creds_json = get_raw_credentials_json(target_account)

    if not creds_json:
        if is_json_mode():
            print_json_error("NO_CREDENTIALS", f"No credentials for {target_account}")
        else:
            print_error(f"No credentials for {target_account}")
        raise typer.Exit(1)

    typer.echo(creds_json)
