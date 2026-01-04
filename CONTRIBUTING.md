# Contributing to gdocs-cli

Thank you for your interest in contributing to gdocs-cli!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Talk-Point/gdocs-cli.git
   cd gdocs-cli
   ```

2. Install dependencies with uv:
   ```bash
   uv sync --all-extras --dev
   ```

3. Set up Google API credentials:
   - Create OAuth 2.0 credentials in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Enable the Google Docs API and Google Drive API
   - Download credentials as `credentials.json` and place in the project root

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=gdocs_cli --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_docs.py
```

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check linting
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure tests pass and code is formatted
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Project Structure

```
gdocs-cli/
├── src/gdocs_cli/
│   ├── cli/           # CLI commands (Typer)
│   ├── services/      # Business logic and API interactions
│   ├── models/        # Domain models (dataclasses)
│   └── utils/         # Shared utilities
├── tests/
│   └── unit/          # Unit tests
└── pyproject.toml     # Project configuration
```

## Reporting Issues

Please report bugs and feature requests via [GitHub Issues](https://github.com/Talk-Point/gdocs-cli/issues).
