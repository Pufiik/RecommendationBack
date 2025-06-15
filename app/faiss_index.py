import faiss
import json
import os
import numpy as np
from threading import Lock
from django.conf import settings

from .constants import UMAP_DIM, IVF_NLIST


class FaissIndex:
    _index = None
    _ids = []
    _lock = Lock()

    INDEX_PATH = os.path.join(settings.BASE_DIR, 'faiss_index_ivf.bin')
    IDS_PATH = INDEX_PATH + '.ids.json'

    @classmethod
    def _ensure_index(cls):
        if cls._index is None:
            cls.load_index()

    @classmethod
    def build_index(cls, vectors_with_ids):
        ids, vecs = zip(*vectors_with_ids)
        mat = np.stack(vecs).astype('float32')
        faiss.normalize_L2(mat)
        quantizer = faiss.IndexFlatIP(UMAP_DIM)

        index = faiss.IndexIVFFlat(
            quantizer,
            UMAP_DIM,  # размерность векторов
            IVF_NLIST,  # количество кластеров
            faiss.METRIC_INNER_PRODUCT  # тип метрики
        )
        index.train(mat)  # выделение центроид
        index.add(mat)

        with cls._lock:
            cls._index = index
            cls._ids = list(ids)

        cls.save_index()

    @classmethod
    def search(cls, query_vec, top_k=10, nprobe=10):
        cls._ensure_index()
        if cls._index is None:
            return []

        cls._index.nprobe = nprobe
        v = np.array([query_vec], dtype='float32')
        faiss.normalize_L2(v)
        D, I = cls._index.search(v, top_k)
        return [(cls._ids[i], float(D[0][j])) for j, i in enumerate(I[0])]

    @classmethod
    def save_index(cls):
        with cls._lock:
            if cls._index is not None:
                faiss.write_index(cls._index, cls.INDEX_PATH)
                with open(cls.IDS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cls._ids, f)

    @classmethod
    def load_index(cls):
        try:
            idx = faiss.read_index(cls.INDEX_PATH)
            with open(cls.IDS_PATH, 'r', encoding='utf-8') as f:
                ids = json.load(f)
            with cls._lock:
                cls._index = idx
                cls._ids = ids
        except Exception:
            cls._index = None
            cls._ids = []
