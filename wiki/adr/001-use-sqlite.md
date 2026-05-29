# ADR-001: Use SQLite for local storage

## Status

Accepted

## Context

We need a local storage solution that is reliable, requires no external services, and supports full-text search.

## Decision

Use SQLite with FTS5 extension for full-text search capabilities.

## Consequences

- Zero external dependencies for data storage.
- FTS5 provides fast, ranked full-text search.
- Easy backup: just copy the `.sqlite` file.
- WAL mode allows concurrent reads during writes.
