from signal import signal

import numpy as np
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ArticleInteraction, Article, UserProfile, EMBED_DIM
from .faiss_index import FaissIndex
from sklearn.preprocessing import normalize
from django.utils import timezone


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
@receiver(post_delete, sender=ArticleInteraction)
def get_start_user_embedding(sender, instance, **kwargs):
    flag = False
    if sender is ArticleInteraction and signal == post_delete:
        profile = instance.user_profile
        liked_interactions = profile.interactions.filter(vote=ArticleInteraction.LIKE)
        if liked_interactions.exists():
            flag = True
    if sender is UserProfile and signal == post_save:
        flag = True

    if flag:
        all_embs = [a.embedding for a in Article.objects.all() if a.embedding]
        if not all_embs:
            instance.embedding = [0.0] * EMBED_DIM
        else:
            mat = np.stack(all_embs)
            avg = mat.mean(axis=0).reshape(1, -1)
            instance.embedding = normalize(avg)[0].tolist()
        instance.save()
    else:
        pass


@receiver(post_save, sender=Article)
@receiver(post_delete, sender=Article)
def rebuild_faiss(sender, instance, **kwargs):
    FaissIndex.build_index()
