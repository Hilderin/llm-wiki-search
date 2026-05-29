# Getting Started

## Prerequisites

- Python 3.11 or later
- uv package manager
- Git

## Setup

1. Clone the repository.
2. Run `uv sync` to install dependencies.
3. Copy `.env.example` to `.env` and adjust settings.
4. Run the setup script to initialize the database.

## Running the server

```bash
uv run python -m wiki_search_mcp.server
```

## Verifying

Check that the server starts without errors and that the wiki index is created at `.wiki-index/wiki.sqlite`.
