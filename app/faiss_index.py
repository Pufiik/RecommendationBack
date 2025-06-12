
from threading import Lock
import faiss
import numpy as np
from app.models import Article
from .constants import UMAP_DIM, HNSW_EF_SEARCH, HNSW_EF_CONSTRUCTION, HNSW_M


class FaissIndex:
    _index = None
    _ids = []
    _lock = Lock()

    @classmethod
    def build_index(cls):

        with cls._lock:
            valid = [
                (a.id, np.array(a.embedding, dtype='float32'))
                for a in Article.objects.all()
                if a.embedding and len(a.embedding) == UMAP_DIM
            ]
            if not valid:
                cls._index = None
                cls._ids = []
                return

            ids, embs = zip(*valid)
            embs = np.stack(embs)
            faiss.normalize_L2(embs)

            index = faiss.IndexHNSWFlat(UMAP_DIM, HNSW_M, faiss.METRIC_INNER_PRODUCT)

            index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION

            index.add(embs)

            cls._index = index
            cls._ids = list(ids)

    @classmethod
    def search(cls, vec, top_k=10, ef_search=HNSW_EF_SEARCH):

        if cls._index is None:
            cls.build_index()
        if cls._index is None:
            return []

        cls._index.hnsw.efSearch = ef_search

        v = np.array([vec], dtype='float32')
        faiss.normalize_L2(v)
        D, I = cls._index.search(v, top_k)
        return [(cls._ids[i], float(D[0][j])) for j, i in enumerate(I[0])]
