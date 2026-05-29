import asyncio
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..config import WikiSearchConfig
from .indexer import Indexer


class WikiEventHandler(FileSystemEventHandler):
    def __init__(self, indexer: Indexer, config: WikiSearchConfig, debounce_seconds: float = 1.0):
        self.indexer = indexer
        self.config = config
        self.debounce_seconds = debounce_seconds
        self._last_event: dict[str, float] = {}

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        self._debounce(event.src_path, "created")

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        self._debounce(event.src_path, "modified")

    def on_deleted(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        rel = self._relative_path(event.src_path)
        if rel is not None:
            self.indexer.delete_file(self.config.wiki_root / rel)

    def on_moved(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        src_rel = self._relative_path(event.src_path)
        dest_rel = self._relative_path(event.dest_path)
        if src_rel is not None:
            self.indexer.delete_file(self.config.wiki_root / src_rel)
        if dest_rel is not None:
            time.sleep(0.1)
            dest_file = self.config.wiki_root / dest_rel
            if dest_file.exists():
                self.indexer.index_file(dest_file)

    def _debounce(self, src_path: str, _event_type: str) -> None:
        now = time.time()
        last = self._last_event.get(src_path, 0)
        if now - last < self.debounce_seconds:
            return
        self._last_event[src_path] = now

        rel = self._relative_path(src_path)
        if rel is None:
            return

        filepath = self.config.wiki_root / rel
        if filepath.exists():
            self.indexer.index_file(filepath)

    def _relative_path(self, src_path: str) -> Path | None:
        try:
            return Path(src_path).relative_to(self.config.wiki_root)
        except ValueError:
            return None


async def start_watcher(config: WikiSearchConfig, indexer: Indexer) -> Observer | None:
    if not config.wiki_root.exists():
        config.wiki_root.mkdir(parents=True, exist_ok=True)
    handler = WikiEventHandler(indexer, config)
    observer = Observer()
    observer.schedule(handler, str(config.wiki_root), recursive=True)
    observer.start()
    return observer
