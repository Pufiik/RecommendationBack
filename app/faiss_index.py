from threading import Lock
import faiss
import numpy as np
from app.models import Article, EMBED_DIM

NPROBE = 1
NLIST = 1


class FaissIndex:
    _index = None
    _ids = []
    _lock = Lock()

    @classmethod
    def build_index(cls, nlist=NLIST):
        with cls._lock:
            valid = [(a.id, np.array(a.embedding, dtype='float32'))
                     for a in Article.objects.all()
                     if a.embedding and len(a.embedding) == EMBED_DIM]
            if not valid:
                cls._index = None
                cls._ids = []
                return

            ids, embs = zip(*valid)
            embs = np.stack(embs)
            faiss.normalize_L2(embs)

            quantizer = faiss.IndexFlatIP(EMBED_DIM)
            index = faiss.IndexIVFFlat(quantizer, EMBED_DIM, nlist, faiss.METRIC_INNER_PRODUCT)
            index.train(embs)
            index.add(embs)

            cls._index = index
            cls._ids = list(ids)

    @classmethod
    def search(cls, vec, top_k=10, nprobe=NPROBE):
        if cls._index is None:
            cls.build_index()
        if cls._index is None:
            return []

        cls._index.nprobe = nprobe

        v = np.array([vec], dtype='float32')
        faiss.normalize_L2(v)
        D, I = cls._index.search(v, top_k)
        return [(cls._ids[i], float(D[0][j])) for j, i in enumerate(I[0])]
