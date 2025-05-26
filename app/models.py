from django.contrib.postgres.fields import ArrayField
from django.db import models, migrations
from django.contrib.auth.models import User
from pgvector.django import HnswIndex
from pgvector.django import VectorField
from pgvector.django import VectorExtension

EMBED_DIM = 2


class ArticleInteractionManager(models.Manager):
    def liked(self):
        return self.filter(vote=ArticleInteraction.LIKE)

    def disliked(self):
        return self.filter(vote=ArticleInteraction.DISLIKE)

    def read_articles(self):
        return self.filter(read=True)


class Article(models.Model):
    title = models.CharField(max_length=500)
    annotation = models.TextField()
    content = models.TextField()
    embedding = ArrayField(models.FloatField(), size=EMBED_DIM, default=list)
    # embedding = VectorField(dimensions=768)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.title}"

    # class Meta:
    #     indexes = [
    #         HnswIndex(
    #             name="article_embedding_hnsw_idx",
    #             fields=["embedding"],
    #             m=16,
    #             ef_construction=64,
    #             opclasses=["vector_cosine_ops"],
    #         )]


class UserProfile(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                related_name='profile')
    # embedding = VectorField(dimensions=768)
    embedding = ArrayField(models.FloatField(), size=EMBED_DIM, default=list)
    update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    #
    # class Meta:
    #     indexes = [
    #         HnswIndex(
    #             name="user_embedding",
    #             fields=["embedding"],
    #             m=16,
    #             ef_construction=64,
    #             opclasses=["vector_cosine_ops"],
    #         )]


class ArticleInteraction(models.Model):
    LIKE = 1
    DISLIKE = -1
    VOTE_CHOICES = (
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    )

    user_profile = models.ForeignKey(UserProfile,
                                     on_delete=models.CASCADE,
                                     related_name='interactions')
    article = models.ForeignKey(Article,
                                on_delete=models.CASCADE,
                                related_name='interactions')
    read = models.BooleanField(default=False)
    vote = models.SmallIntegerField(choices=VOTE_CHOICES,
                                    null=True, blank=True)
    date = models.DateTimeField(auto_now=True)

    objects = ArticleInteractionManager()

    class Meta:
        unique_together = ('user_profile', 'article')
        ordering = ('-date',)

    def __str__(self):
        vote_display = dict(self.VOTE_CHOICES).get(self.vote, 'No vote')
        return f"{self.user_profile.user.username} → '{self.article.title[:50]}' | Vote: {vote_display} | Read: {self.read}"





