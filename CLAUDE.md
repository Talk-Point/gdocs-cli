# gdocs-cli Development Guidelines

## Project Overview

A command-line interface for Google Docs, inspired by `gmail-cli` and GitHub's `gh` CLI.
Uses Domain-Driven Design architecture.

## Tech Stack

- Python 3.11+ with Typer (CLI), Rich (Output)
- Google Docs API v1 + Drive API v3
- Keyring for Credential Storage
- uv for package management

## Project Structure

```text
src/gdocs_cli/
├── cli/           # CLI Layer (Typer Commands)
│   ├── auth.py    # Authentication commands
│   ├── document.py # Document CRUD commands
│   ├── content.py  # Content manipulation
│   ├── table.py    # Table operations
│   ├── drives.py   # Shared Drives commands
│   └── main.py     # Typer app entry point
├── services/      # Business Logic Layer
│   ├── auth.py    # OAuth flow, token management
│   ├── credentials.py # Keyring storage
│   └── docs.py    # Google Docs/Drive API wrapper
├── models/        # Domain Models (Dataclasses)
│   ├── document.py # Document, DocumentSummary
│   └── element.py  # TextStyle, ParagraphStyle, Table
└── utils/         # Shared Utilities
    ├── output.py   # Rich formatting, JSON output
    └── request_builder.py # BatchUpdate request builders
```

## Commands

```bash
# Development
uv sync                          # Install dependencies
uv run pytest                    # Run tests
uv run ruff check .              # Lint code
uv run ruff format .             # Format code
uv run gdocs --help              # Run CLI

# Testing
uv run pytest tests/unit/        # Unit tests only
uv run pytest -v                 # Verbose output
```

## CLI Usage

```bash
# Authentication
gdocs auth login                 # Authenticate with Google
gdocs auth status                # Show auth status
gdocs auth logout                # Log out

# Document Management
gdocs doc create "My Document"   # Create new doc
gdocs doc list                   # List documents
gdocs doc get <id>               # Get document details
gdocs doc delete <id>            # Delete document
gdocs doc move <id> --folder <folder-id>

# Content Manipulation
gdocs content insert <id> "Text" --heading HEADING_1
gdocs content append <id> "More text"
gdocs content from-file <id> content.md
gdocs content replace <id> "old" "new"

# Tables
gdocs table create <id> --rows 3 --columns 4
gdocs table list <id>
gdocs table add-row <id> <table-index>
gdocs table delete-row <id> <table-index> --row 2

# Shared Drives
gdocs drives list
gdocs drives folders <drive-id>
```

## Key Patterns

### Authentication Decorator
```python
from gdocs_cli.cli.auth import require_auth

@command_app.command("my-command")
@require_auth
def my_command(...):
    ...
```

### JSON Output Mode
```python
from gdocs_cli.utils.output import is_json_mode, print_json, print_success

if is_json_mode():
    print_json({"key": "value"})
else:
    print_success("Human readable message")
```

### Request Builders
```python
from gdocs_cli.utils.request_builder import insert_text_request
from gdocs_cli.services.docs import batch_update

requests = [insert_text_request("Hello", index=1)]
batch_update(document_id, requests, account=account)
```

## OAuth Scopes

```python
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
]
```

## Environment Variables

- `GDOCS_ACCOUNT`: Default account to use (overrides configured default)

## Code Style

- Python 3.11+ syntax (type hints, `|` unions)
- Ruff for linting and formatting
- Follow existing patterns from gmail-cli
