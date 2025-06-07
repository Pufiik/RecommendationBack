from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.auth.models import User

EMBED_DIM = 2
MAX_LENGTH = 500


class ArticleInteractionManager(models.Manager):
    def liked(self):
        return self.filter(vote=ArticleInteraction.LIKE)

    def disliked(self):
        return self.filter(vote=ArticleInteraction.DISLIKE)

    def read_articles(self):
        return self.filter(read=True)

    def for_user(self, user_profile):
        return self.filter(user_profile=user_profile)


class Article(models.Model):
    RU = "ru"
    ENG = "eng"

    LANG_CHOICES = (
        (RU, "ru"),
        (ENG, "eng"),
    )

    title = models.CharField(max_length=MAX_LENGTH)
    annotation = models.TextField()
    content = models.TextField()
    language = models.CharField(
        max_length=3,
        choices=LANG_CHOICES,
        default=RU,
    )
    embedding = ArrayField(models.FloatField(), size=EMBED_DIM, default=list)
    created_at = models.DateTimeField(auto_now_add=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                related_name='profile')
    embedding = ArrayField(models.FloatField(), size=EMBED_DIM, default=list)
    update_date = models.DateTimeField(auto_now=True)



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

