from threading import Lock

import faiss
import numpy as np

from app.models import Article, EMBED_DIM


class FaissIndex:
    _index = None
    _ids = []
    _lock = Lock()

    @classmethod
    def build_index(cls):
        with cls._lock:

            valid_articles = []
            embs_list = []
            for a in Article.objects.all():
                emb = a.embedding
                if emb and len(emb) == EMBED_DIM:
                    embs_list.append(np.array(emb, dtype='float32'))
                    valid_articles.append(a.id)
            if not embs_list:
                cls._index = None
                cls._ids = []
                return
            embs = np.stack(embs_list)
            faiss.normalize_L2(embs)
            idx = faiss.IndexFlatIP(EMBED_DIM)
            idx.add(embs)
            cls._index = idx
            cls._ids = valid_articles
        with cls._lock:
            embs = np.stack([a.embedding for a in Article.objects.all()]).astype('float32')
            faiss.normalize_L2(embs)
            idx = faiss.IndexFlatIP(EMBED_DIM)
            idx.add(embs)
            cls._index = idx
            cls._ids = list(Article.objects.values_list('id', flat=True))

    @classmethod
    def search(cls, vec, top_k=10):
        if cls._index is None:
            cls.build_index()
        if cls._index is None:
            return []

        v = np.array([vec], dtype='float32')
        faiss.normalize_L2(v)
        D, I = cls._index.search(v, top_k)
        return [(cls._ids[i], float(D[0][j])) for j, i in enumerate(I[0])]
