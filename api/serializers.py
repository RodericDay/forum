from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from api import models


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username"]


class TopicSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Topic
        exclude = []
        read_only_fields = ["author"]


class PostListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Post
        exclude = ["topic"]


class PostDetailSerializer(serializers.ModelSerializer):
    topic = TopicSerializer()

    class Meta:
        model = models.Post
        exclude = []
        read_only_fields = ["id", "author", "timestamp", "topic"]


class ReplySerializer(serializers.ModelSerializer):
    text = serializers.CharField(default="")

    class Meta:
        model = models.Post
        exclude = []
        read_only_fields = ["id", "author", "timestamp", "text", "topic"]


class FirstPostSerializer(serializers.ModelSerializer):
    text = serializers.CharField(default="")

    class Meta:
        model = models.Topic
        exclude = []
        read_only_fields = ["id", "author", "last_post", "text"]

    def create(self, validated_data):
        extra = set(self.initial_data) - set(self.fields) - {'csrfmiddlewaretoken'}
        if extra:
            msg = "Provided invalid data: {extra}".format(extra=extra)
            raise serializers.ValidationError(msg)

        text = validated_data.pop("text")
        author = validated_data.pop("author")
        now = timezone.now()
        if not text:
            raise serializers.ValidationError("Topic must have at least one post.")

        topic = models.Topic.objects.create(author=author, last_post=now, **validated_data)
        topic.posts.create(author=author, timestamp=now, text=text)
        return topic
