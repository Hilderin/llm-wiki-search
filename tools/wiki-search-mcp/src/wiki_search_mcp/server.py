import asyncio
import sys

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from .config import WikiSearchConfig
from .db.connection import DatabaseManager
from .db.schema import initialize_database
from .index.indexer import Indexer
from .index.watcher import start_watcher
from .search.hybrid_search import HybridSearcher
from .search.exact_search import ExactSearcher
from .mcp_tools.search_wiki import (
    SEARCH_WIKI_TOOL,
    SEARCH_EXACT_TOOL,
    handle_search,
    handle_search_exact,
)
from .mcp_tools.read_section import READ_SECTION_TOOL, handle_read_section
from .mcp_tools.reindex import REINDEX_TOOL, handle_reindex
from .mcp_tools.status import STATUS_TOOL, handle_status


async def main() -> None:
    config = WikiSearchConfig.from_env()
    config.index_path.parent.mkdir(parents=True, exist_ok=True)

    db = DatabaseManager(config.index_path)
    initialize_database(db)

    indexer = Indexer(db, config)

    if config.reindex_on_start:
        count = indexer.reindex_changed_only()
        print(f"[wiki-search] Indexed {count} files on startup", file=sys.stderr)

    if config.watch:
        observer = await start_watcher(config, indexer)
        _ = asyncio.create_task(_keep_watcher_alive(observer))
        print(f"[wiki-search] File watcher started on {config.wiki_root}", file=sys.stderr)

    hybrid = HybridSearcher(db)
    exact = ExactSearcher(db)
    server = Server("wiki-search")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            SEARCH_WIKI_TOOL,
            SEARCH_EXACT_TOOL,
            READ_SECTION_TOOL,
            REINDEX_TOOL,
            STATUS_TOOL,
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "wiki_search":
            return await handle_search(hybrid, arguments)
        if name == "wiki_search_exact":
            return await handle_search_exact(exact, arguments)
        if name == "wiki_read_section":
            return await handle_read_section(db, arguments)
        if name == "wiki_reindex":
            return await handle_reindex(indexer, arguments)
        if name == "wiki_status":
            return await handle_status(config, db)
        raise ValueError(f"Unknown tool: {name}")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="wiki-search",
                server_version="0.1.0",
                capabilities=types.ServerCapabilities(),
            ),
        )


async def _keep_watcher_alive(observer) -> None:
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    asyncio.run(main())
