from collections.abc import Sequence
import numpy as np
from .models import Article


def _unwrap(v):
    if isinstance(v, Sequence) and not isinstance(v, (str, bytes)) and len(v) == 1:
        return _unwrap(v[0])
    return v


def get_cosine_similar_ids(
        query_vec,
        exclude_ids=None,
        top_k=10,
        filter_ids=None,
):
    qs = Article.objects.all()

    if filter_ids is not None:
        qs = qs.filter(pk__in=filter_ids)

    if exclude_ids:
        qs = qs.exclude(pk__in=exclude_ids)

    def cosine(a, b):
        a_np = np.array(_unwrap(a), dtype='float32').ravel()
        b_np = np.array(_unwrap(b), dtype='float32').ravel()
        na, nb = np.linalg.norm(a_np), np.linalg.norm(b_np)
        if na == 0 or nb == 0 or a_np.shape != b_np.shape:
            return 0.0
        return float(np.dot(a_np, b_np) / (na * nb))

    scored = [(art.id, cosine(art.embedding, query_vec)) for art in qs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [pk for pk, _ in scored[:top_k]]
