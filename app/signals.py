import numpy as np
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ArticleInteraction, Article, UserProfile, EMBED_DIM
from .faiss_index import FaissIndex
from sklearn.preprocessing import normalize


@receiver(post_save, sender=ArticleInteraction)
def update_user_embedding(sender, instance, **kwargs):
    profile = instance.user_profile
    liked = profile.interactions.filter(vote=ArticleInteraction.LIKE)
    if not liked.exists():
        profile.embedding = None
    else:
        mat = np.stack([i.article.embedding for i in liked])
        avg = mat.mean(axis=0).reshape(1, -1)
        profile.embedding = normalize(avg)[0].tolist()
    profile.save()


@receiver(post_save, sender=Article)
def rebuild_faiss(sender, instance, **kwargs):
    FaissIndex.build_index()
