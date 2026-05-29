# llm-wiki-search

Local MCP server for full-text search over markdown wikis. Designed for OpenCode agents to query project knowledge during development.

## What it does

The server indexes `wiki/**/*.md` files, watches for changes, and exposes MCP tools so agents can search, read sections, and inspect the index — all locally, no external services.

## How it works

```
Markdown files → chunk by headings → SQLite (documents + chunks + FTS5 index)
                                                          ↓
Agent query → FTS5 MATCH → BM25 ranking → heading boost → formatted excerpt
```

Files are chunked per heading section (e.g. `Architecture > Agents > Handoff`). Each chunk stores content, heading path, and line range. Search uses SQLite FTS5 with BM25 scoring and heading-match boosting.

A file watcher (watchdog) keeps the index in sync when files are created, modified, deleted, or renamed.

## MCP tools

| Tool | What it does |
|------|-------------|
| `wiki_search` | Hybrid search for fuzzy / conceptual questions |
| `wiki_search_exact` | Exact FTS search for specific terms, file names, class names |
| `wiki_read_section` | Read a full section by file path + heading path |
| `wiki_reindex` | Force reindex (`changed-only` or `rebuild`) |
| `wiki_status` | Show index state (doc count, chunk count, last indexed) |

## Quick start

```bash
uv venv
uv pip install -e tools/wiki-search-mcp
WIKI_ROOT=./wiki uv run python -m wiki_search_mcp.server
```

## OpenCode config example

Add to your `opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "wiki": {
      "type": "local",
      "command": ["uv", "run", "python", "-m", "wiki_search_mcp.server"],
      "enabled": true,
      "environment": {
        "WIKI_ROOT": "./docs/wiki",
        "WIKI_INDEX": "./.wiki-index/wiki.sqlite",
        "WIKI_WATCH": "true",
        "WIKI_REINDEX_ON_START": "true"
      }
    }
  }
}
```

> Requires `uv pip install -e tools/wiki-search-mcp` to be run first so `uv run` can find the package.

Make sure to add `.wiki-index/` to your project's `.gitignore` so the SQLite index is not committed.

## Documentation

Full docs: [tools/wiki-search-mcp/README.md](tools/wiki-search-mcp/README.md)
