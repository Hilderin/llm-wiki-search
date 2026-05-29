import hashlib
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

    def index_file(self, filepath: Path) -> bool:
        rel = filepath.relative_to(self.config.wiki_root)
        path_str = str(rel)

        content = filepath.read_text(encoding="utf-8")
        mtime = filepath.stat().st_mtime
        size = len(content.encode("utf-8"))
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        existing = self.doc_repo.get_document_by_path(path_str)
        if existing and existing["hash"] == content_hash:
            return False

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

    def reindex_changed_only(self) -> int:
        wiki_root = self.config.wiki_root
        if not wiki_root.exists():
            return 0

        md_files = sorted(wiki_root.rglob("*.md"))
        count = 0
        for filepath in md_files:
            if self.index_file(filepath):
                count += 1

        indexed_paths = {str(f.relative_to(wiki_root)) for f in md_files}
        for doc in self.doc_repo.get_all_documents():
            if doc["path"] not in indexed_paths:
                self.doc_repo.delete_document(doc["path"])

        self.db.conn.commit()
        return count

    def rebuild(self) -> int:
        conn = self.db.conn
        conn.execute("DELETE FROM chunks_fts")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")
        conn.commit()
        return self.reindex_changed_only()


def _extract_title(content: str, fallback: str) -> str:
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            return stripped[1:].strip()
    return fallback
