# gdocs-cli

A command-line interface for Google Docs, inspired by [gmail-cli](https://github.com/Talk-Point/gmail-cli) and GitHub's `gh`.

## Features

- **Document Management**: Create, list, get, delete, and move Google Docs
- **Content Manipulation**: Insert text with formatting, append content, replace text
- **Table Operations**: Create tables, add/delete rows and columns
- **Shared Drives Support**: List and browse Shared Drives (Team Drives)
- **Multi-Account Support**: Manage multiple Google accounts
- **JSON Output**: Machine-readable output for scripting (`--json`)

## Installation

```bash
# Using uv (recommended)
uv pip install gdocs-cli

# Or install from source
git clone https://github.com/Talk-Point/gdocs-cli.git
cd gdocs-cli
uv sync
```

## Setup

1. Create OAuth 2.0 credentials in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Enable the Google Docs API and Google Drive API
3. Download the credentials as `credentials.json`
4. Place `credentials.json` in your working directory
5. Run `gdocs auth login` to authenticate

## Usage

### Authentication

```bash
# Authenticate with Google
gdocs auth login

# Show authentication status
gdocs auth status

# Log out
gdocs auth logout
gdocs auth logout --all  # Log out all accounts
```

### Document Management

```bash
# Create a new document
gdocs doc create "My Document"
gdocs doc create "My Document" --folder <folder-id>

# List documents
gdocs doc list
gdocs doc list --limit 50
gdocs doc list --shared-drive <drive-id>

# Search documents by title
gdocs doc search "quarterly report"
gdocs doc search "meeting" --limit 10

# Get document details
gdocs doc get <document-id>

# Delete document
gdocs doc delete <document-id>
gdocs doc delete <document-id> --force  # Skip confirmation

# Move document
gdocs doc move <document-id> --folder <folder-id>
```

### Sharing & Permissions

```bash
# Share a document
gdocs doc share <id> --email user@example.com --role reader
gdocs doc share <id> --email user@example.com --role writer
gdocs doc share <id> --email user@example.com --role commenter

# Share without email notification
gdocs doc share <id> --email user@example.com --no-notify

# List permissions
gdocs doc permissions <id>

# Remove permission
gdocs doc unshare <id> --permission <permission-id>
```

### Revision History

```bash
# List document revisions
gdocs doc revisions <id>
```

### Content Manipulation

```bash
# Read document content (as Markdown)
gdocs content read <id>
gdocs content read <id> --plain    # Plain text
gdocs content read <id> --raw      # Raw JSON structure

# Insert text at position
gdocs content insert <id> "Hello World"
gdocs content insert <id> "Title" --heading TITLE
gdocs content insert <id> "Bold text" --bold

# Append text
gdocs content append <id> "More content"

# Import from file
gdocs content from-file <id> content.txt

# Replace text
gdocs content replace <id> "old text" "new text"
```

### Tables

```bash
# Create a table
gdocs table create <id> --rows 3 --columns 4

# List tables in document
gdocs table list <id>

# Add row
gdocs table add-row <id> <table-index>
gdocs table add-row <id> 0 --row 2 --above

# Delete row
gdocs table delete-row <id> <table-index> --row 1
```

### Shared Drives

```bash
# List all Shared Drives
gdocs drives list

# List folders in a Shared Drive
gdocs drives folders <drive-id>
gdocs drives folders <drive-id> --parent <folder-id>
```

### Global Options

```bash
# JSON output for scripting
gdocs --json doc list

# Use specific account
gdocs doc list --account user@example.com

# Show version
gdocs --version
```

## Environment Variables

- `GDOCS_ACCOUNT`: Default account to use (overrides configured default)

## Development

```bash
# Install development dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint code
uv run ruff check .

# Format code
uv run ruff format .
```

## License

MIT License - see [LICENSE](LICENSE) for details.
