import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class WikiSearchConfig:
    wiki_root: Path
    index_path: Path
    watch: bool
    reindex_on_start: bool

    @classmethod
    def from_env(cls) -> "WikiSearchConfig":
        return cls(
            wiki_root=Path(os.environ.get("WIKI_ROOT", "./wiki")).resolve(),
            index_path=Path(os.environ.get("WIKI_INDEX", "./.wiki-index/wiki.sqlite")).resolve(),
            watch=os.environ.get("WIKI_WATCH", "true").lower() in ("true", "1", "yes"),
            reindex_on_start=os.environ.get("WIKI_REINDEX_ON_START", "true").lower() in ("true", "1", "yes"),
        )
