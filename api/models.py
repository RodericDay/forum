from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Topic(models.Model):
    title = models.CharField(max_length=140, unique=True)
    author = models.CharField(max_length=100)
    last_post = models.DateTimeField(default=timezone.now)
    post_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-last_post"]

class Post(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    author = models.CharField(max_length=100)
    text = models.TextField()
    topic = models.ForeignKey(Topic, related_name="posts", on_delete=models.CASCADE)

    class Meta:
        ordering = ["timestamp"]
        unique_together = ["timestamp", "author", "topic"]

    def save(self, **kw):
        super().save(**kw)
        self.topic.post_count = self.topic.posts.count()
        self.topic.last_post = self.timestamp
        self.topic.save()

class Record(models.Model):
    user = models.ForeignKey(User)
    topic = models.ForeignKey(Topic)
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = ["user", "topic"]

    def __str__(self):
        return "topic={0.topic.id} for {0.user}".format(self)
