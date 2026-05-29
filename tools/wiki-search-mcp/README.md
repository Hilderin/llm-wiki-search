# wiki-search-mcp

Local MCP server for searching markdown wikis using SQLite FTS5 full-text search.

Designed for OpenCode agents: index your `wiki/` folder, then search via MCP tools.

## Features

- **Automatic indexing** – scans `wiki/**/*.md` on startup
- **File watching** – updates the index when files are created, modified, deleted, or renamed (via watchdog)
- **FTS5 full-text search** – fast, ranked results with BM25 scoring
- **Section-aware chunking** – splits markdown files by headings; results include heading path and line ranges
- **Architecture ready for vector search** – `sqlite-vec` can be added later
- **100 % local** – no external API calls, no data leaves your machine

## Project structure

```
tools/wiki-search-mcp/
├── pyproject.toml
├── README.md
├── wiki-search-agent-rules.md
├── src/wiki_search_mcp/
│   ├── server.py          # MCP server entry point
│   ├── config.py          # Environment-based configuration
│   ├── db/                # SQLite schema, connection, repository
│   ├── index/             # Markdown chunker, indexer, file watcher
│   ├── search/            # FTS5 exact search, hybrid search, ranking
│   └── mcp_tools/         # MCP tool definitions and handlers
└── tests/
    ├── test_markdown_chunker.py
    ├── test_indexer.py
    └── test_search.py
```

## Requirements

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (package manager)

## Installation

### Option A: Workspace-wide install (recommended for OpenCode)

```bash
# From the repo root
uv venv                     # create a virtual environment (one-time)
uv pip install -e tools/wiki-search-mcp
```

The server can then be run from any directory:

```bash
WIKI_ROOT=./wiki uv run python -m wiki_search_mcp.server
```

### Option B: Isolated project install

```bash
cd tools/wiki-search-mcp
uv sync
```

Paths must be adjusted when running (see below).

## Usage

### Environment variables

| Variable                | Default                  | Description                              |
|-------------------------|--------------------------|------------------------------------------|
| `WIKI_ROOT`             | `./wiki`                 | Path to the wiki markdown folder         |
| `WIKI_INDEX`            | `./.wiki-index/wiki.sqlite` | Path for the SQLite index file        |
| `WIKI_WATCH`            | `true`                   | Enable file watching                     |
| `WIKI_REINDEX_ON_START` | `true`                   | Reindex changed files on startup         |

### Run the server manually

```bash
# With workspace-wide install (from repo root):
WIKI_ROOT=./wiki uv run python -m wiki_search_mcp.server

# With isolated install:
cd tools/wiki-search-mcp
WIKI_ROOT=../../wiki uv run python -m wiki_search_mcp.server
```

### Run tests

```bash
cd tools/wiki-search-mcp
uv run pytest -v
```

## MCP Tools

| Tool                 | Description                                          |
|----------------------|------------------------------------------------------|
| `wiki_search`        | Hybrid search (FTS + future vector). Use for fuzzy/project questions. |
| `wiki_search_exact`  | Exact lexical search. Use for specific terms, ADR numbers, file names. |
| `wiki_read_section`  | Read a specific section by path and heading path.    |
| `wiki_reindex`       | Force reindexing (`changed-only` or `rebuild`).      |
| `wiki_status`        | Index state: doc count, chunk count, watcher status. |

## OpenCode integration

### Prerequisite

Install the package so `uv run` can find it:

```bash
uv venv && uv pip install -e tools/wiki-search-mcp
```

### Configuration

Add to your `opencode.json` or `opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "wiki": {
      "type": "local",
      "command": ["uv", "run", "python", "-m", "wiki_search_mcp.server"],
      "enabled": true,
      "environment": {
        "WIKI_ROOT": "./wiki",
        "WIKI_INDEX": "./.wiki-index/wiki.sqlite",
        "WIKI_WATCH": "true",
        "WIKI_REINDEX_ON_START": "true"
      }
    }
  }
}
```

Paths are relative to the workspace root (where OpenCode runs).

## Architecture overview

```
Startup → read config → create/verify DB schema
       → reindex changed files
       → start file watcher (watchdog)
       → expose MCP tools via stdio

Indexing flow:
  Markdown file → chunker (split by headings)
               → SQLite documents + chunks + chunks_fts (FTS5)

Search flow:
  Agent query → FTS5 MATCH → BM25 ranking
             → heading boost → formatted excerpt
```

## V2 roadmap

- `sqlite-vec` extension for vector embeddings
- `VectorSearchProvider` interface
- Reciprocal rank fusion (RRF) for hybrid result merging
- Configurable embedding model (local, via Ollama etc.)
