import numpy as np
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .constants import UMAP_DIM
from .models import ArticleInteraction, Article, UserProfile
from .faiss_index import FaissIndex
from sklearn.preprocessing import normalize
from django.utils import timezone
from .embeddings import init_embedding_model, embed_bert_cls
from .summarization import init_summarizer, create_annotation
import umap

UMAP_PARAMS = dict(n_neighbors=15, n_components=360, metric='cosine')
_umap_reducers = {}


def _get_reducer(lang: str):
    if lang not in _umap_reducers:
        _umap_reducers[lang] = umap.UMAP(**UMAP_PARAMS)
    return _umap_reducers[lang]


@receiver(post_save, sender=ArticleInteraction)
@receiver(post_delete, sender=ArticleInteraction)
def update_user_embedding(sender, instance, **kwargs):
    profile = instance.user_profile
    liked = profile.interactions.liked()
    if not liked.exists():
        pass
    else:
        mat = np.stack([i.article.embedding for i in liked])
        avg = mat.mean(axis=0).reshape(1, -1)
        profile.embedding = normalize(avg)[0].tolist()
        profile.update_date = timezone.now()
    profile.save()


@receiver(post_save, sender=UserProfile)
def get_start_user_embedding(sender, instance, created, **kwargs):
    recalc_embedding_for_profile(instance)
    print(instance.embedding)


@receiver(post_delete, sender=ArticleInteraction)
def get_start_user_embedding(sender, instance, **kwargs):
    profile = instance.user_profile
    liked_interactions = profile.interactions.filter(vote=ArticleInteraction.LIKE)
    if liked_interactions.exists():
        all_embs = [a.embedding for a in Article.objects.all() if a.embedding]
        if not all_embs:
            instance.embedding = [0.0] * UMAP_DIM
        else:
            mat = np.stack(all_embs)
            avg = mat.mean(axis=0).reshape(1, -1)
            instance.embedding = normalize(avg)[0].tolist()
        instance.save()
    else:
        pass


def recalc_embedding_for_profile(profile):
    liked = profile.interactions.filter(vote=ArticleInteraction.LIKE)
    if liked.exists():
        embeddings = [a.embedding for a in Article.objects.exclude(embedding=[])]
        mat = np.stack(embeddings)
        avg = mat.mean(axis=0).reshape(1, -1)
        profile.embedding = normalize(avg)[0].tolist()
    else:
        profile.embedding = [0.0] * UMAP_DIM
    profile.save()


@receiver(post_save, sender=Article)
def vectorize_and_rebuild(sender, instance: Article, created, **kwargs):
    if not instance.annotation and instance.language == Article.RU:
        init_summarizer()
        annotation = create_annotation(instance.content)
    else:
        annotation = instance.annotation or instance.content
        should_rebuild = False

        if not instance.embedding:
            init_embedding_model()
            raw_emb = embed_bert_cls(annotation)

            same = Article.objects.filter(language=instance.language)
            all_embs = [np.array(a.embedding) for a in same if a.embedding]
            all_embs.append(raw_emb.astype('float32'))
            reducer = _get_reducer(instance.language)
            reduced = reducer.fit_transform(np.stack(all_embs))
            new_emb = reduced[-1]

            Article.objects.filter(pk=instance.pk).update(embedding=new_emb.tolist())
            should_rebuild = True

        if should_rebuild:
            FaissIndex.build_index()


@receiver(post_delete, sender=Article)
def rebuild_after_delete(sender, instance: Article, **kwargs):
    FaissIndex.build_index()
