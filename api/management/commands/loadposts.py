import os, re, json, collections, sqlite3

from django.core.management import BaseCommand, CommandError

from api.models import Topic, Post


class Command(BaseCommand):
    help = "Merges posts from standard JSON file into the database."

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=os.path.abspath)

    def handle(self, filepath, **options):
        with open(filepath) as fp:
            for title, post_list in  json.load(fp).items():
                author = post_list[0][1]
                topic, _ = Topic.objects.get_or_create(title=title, author=author)
                for timestamp, author, text in post_list:
                    post, new = Post.objects.get_or_create(
                        timestamp=timestamp,
                        author=author,
                        text=text,
                        topic=topic
                    )
                post.save()
