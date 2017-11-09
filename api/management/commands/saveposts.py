import os, re, json, collections, sqlite3

from django.core.management import BaseCommand, CommandError

from api.models import Topic
from api.serializers import PostSerializer


class Command(BaseCommand):
    help = "Saves posts into standard JSON file."

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=os.path.abspath)

    def handle(self, filepath, **options):
        if os.path.exists(filepath):
            raise CommandError("Path %s already exists!" % filepath)

        forum = collections.defaultdict(list)
        for topic in Topic.objects.all():
            for post in topic.posts.all():
                data = PostSerializer(post).data
                forum[topic.title].append([data["timestamp"], data["author"], data["text"]])

        with open(filepath, "w") as fp:
            json.dump(forum, fp, indent=2)
