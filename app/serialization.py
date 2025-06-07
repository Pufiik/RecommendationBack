from rest_framework import serializers
from .models import Article, ArticleInteraction


class ArticleSerializer(serializers.ModelSerializer):
    like_count = serializers.IntegerField(read_only=True)
    liked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'annotation', 'content', 'created_at', 'like_count', 'liked']

    def get_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        profile = request.user.profile
        return ArticleInteraction.objects.filter(
            user_profile=profile,
            article=obj,
            vote=ArticleInteraction.LIKE
        ).exists()


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
