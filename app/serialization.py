from rest_framework import serializers
from .models import Article, ArticleInteraction


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'annotation', 'content', 'created_at']


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleInteraction
        fields = ['article', 'read', 'vote']

    def create(self, validated_data):
        profile = self.context['request'].user.profile
        obj, _ = ArticleInteraction.objects.update_or_create(
            user_profile=profile,
            article=validated_data['article'],
            defaults={'read': validated_data.get('read', False),
                      'vote': validated_data.get('vote')}
        )
        return obj
