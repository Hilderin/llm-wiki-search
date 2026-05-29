# Wiki Search Rules

When you need project knowledge, use the wiki MCP before making assumptions.

Use `wiki_search` for conceptual or fuzzy project questions.

Use `wiki_search_exact` for exact terms, IDs, ADR numbers, file names, class names or specific phrases.

Use `wiki_read_section` when a search result is relevant but the excerpt is insufficient.

Always cite:
- file path
- heading
- line range

Do not modify specs, ADRs, implementation contracts or constitution documents without first searching the wiki for existing decisions.

Prefer small, targeted searches over broad searches.

If the index seems stale, call `wiki_status`, then `wiki_reindex` with `changed-only`.
