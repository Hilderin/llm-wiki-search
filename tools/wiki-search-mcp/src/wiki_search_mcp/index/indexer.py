import hashlib
from datetime import datetime
from pathlib import Path

from ..config import WikiSearchConfig
from ..db.repository import DocumentRepository, ChunkRepository
from . import markdown_chunker as chunker


class Indexer:
    def __init__(self, db, config: WikiSearchConfig):
        self.db = db
        self.config = config
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self._log_path = config.index_path.parent / "wiki.indexation.log"
        config.index_path.parent.mkdir(parents=True, exist_ok=True)
        self._log("STARTUP", f"Indexer initialized (wiki_root={config.wiki_root})")

    def _log(self, level: str, message: str) -> None:
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(f"{ts} | {level:7s} | {message}\n")
        except OSError:
            pass

    def index_file(self, filepath: Path) -> bool:
        rel = filepath.relative_to(self.config.wiki_root)
        path_str = str(rel)

        content = filepath.read_text(encoding="utf-8")
        mtime = filepath.stat().st_mtime
        size = len(content.encode("utf-8"))
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        existing = self.doc_repo.get_document_by_path(path_str)
        if existing and existing["hash"] == content_hash:
            self._log("UP-TO-DATE", str(rel))
            return False

        self._log("INDEXING", str(rel))

        title = _extract_title(content, path_str)

        conn = self.db.conn
        doc_id = self.doc_repo.upsert_document(path_str, title, content_hash, mtime, size)
        self.chunk_repo.delete_chunks_for_document(doc_id)

        chunks = chunker.chunk_file(filepath)
        for ch in chunks:
            ch["path"] = path_str
            if not ch["heading_path"]:
                ch["heading_path"] = title or path_str
                ch["heading_level"] = 0
            self.chunk_repo.insert_chunk(
                doc_id, ch["path"], ch["heading_path"],
                ch["heading_level"], ch["content"],
                ch["content_hash"], ch["start_line"], ch["end_line"],
            )

        conn.commit()
        self._log("INDEXED", str(rel))
        return True

    def delete_file(self, filepath: Path) -> None:
        try:
            rel = filepath.relative_to(self.config.wiki_root)
        except ValueError:
            return
        path_str = str(rel)
        conn = self.db.conn
        self.doc_repo.delete_document(path_str)
        conn.commit()
        self._log("DELETED", str(rel))

    def reindex_changed_only(self) -> int:
        wiki_root = self.config.wiki_root
        if not wiki_root.exists():
            self._log("STARTUP", "Wiki root does not exist, skipping reindex")
            return 0

        self._log("REINDEX", "Starting changed-only reindex")
        md_files = sorted(wiki_root.rglob("*.md"))
        count = 0
        for filepath in md_files:
            if self.index_file(filepath):
                count += 1

        indexed_paths = {str(f.relative_to(wiki_root)) for f in md_files}
        for doc in self.doc_repo.get_all_documents():
            if doc["path"] not in indexed_paths:
                self._log("STALE", f"Removing stale document: {doc['path']}")
                self.doc_repo.delete_document(doc["path"])

        self.db.conn.commit()
        self._log("REINDEX", f"Completed: {len(md_files)} files scanned, {count} reindexed")
        return count

    def rebuild(self) -> int:
        self._log("REBUILD", "Starting full rebuild")
        conn = self.db.conn
        conn.execute("DELETE FROM chunks_fts")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")
        conn.commit()
        result = self.reindex_changed_only()
        self._log("REBUILD", f"Full rebuild complete: {result} files indexed")
        return result


def _extract_title(content: str, fallback: str) -> str:
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            return stripped[1:].strip()
    return fallback
