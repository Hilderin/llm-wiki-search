from .exact_search import ExactSearcher


class HybridSearcher:
    """
    V1: delegates to FTS5 exact search.
    TODO V2: add VectorSearchProvider (sqlite-vec) and combine results
             using reciprocal rank fusion (RRF).
    """

    def __init__(self, db):
        self.db = db
        self.exact = ExactSearcher(db)
        # TODO V2: self.vector = VectorSearchProvider(db)

    def search(self, query: str, limit: int = 10) -> list[dict]:
        return self.exact.search(query, limit)
