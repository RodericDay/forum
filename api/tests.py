import json

from django.conf import settings
from rest_framework import test

from api.models import Topic, Post, Record, User


settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
settings.REST_FRAMEWORK["PAGE_SIZE"] = 5


class TestAll(test.APITestCase):

    @classmethod
    def setUpTestData(cls):
        Topic.objects.create(author="user", title="Existing topic")
        Post.objects.create(author="user", text="Existing post", topic_id=1)
        cls.admin = User.objects.create_superuser(username="admin", password="admin", email="")
        cls.user = User.objects.create_user(username="user", password="user")
        cls.other = User.objects.create_user(username="other", password="other")

    def setUp(self):
        self.client.force_login(self.user)

    def test_topic_list(self):
        response = self.client.get("/api/topics/")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["page_size"], settings.REST_FRAMEWORK["PAGE_SIZE"])

        topic, = response.data["results"]
        self.assertEqual(topic["author"], "user")
        self.assertEqual(topic["title"], "Existing topic")
        self.assertEqual(topic["post_count"], 1)

    def test_post_list(self):
        response = self.client.get("/api/topics/1/posts/")
        self.assertEqual(response.data["topic"]["title"], "Existing topic")
        self.assertEqual(response.data["page_size"], settings.REST_FRAMEWORK["PAGE_SIZE"])

        post, = response.data["results"]
        self.assertEqual(post["text"], "Existing post")
        self.assertEqual(post["author"], "user")
        self.assertTrue("topic" not in post, msg=post.get("topic"))

    def test_post_detail(self):
        post = self.client.get("/api/topics/1/posts/1/")
        self.assertEqual(post.data["text"], "Existing post")
        self.assertEqual(post.data["author"], "user")
        self.assertEqual(post.data["topic"]["title"], "Existing topic")

    def test_topic_new(self):
        data = {"title": "New topic", "text": "New post"}

        topic = self.client.post("/api/topics/", data, format="json")
        self.assertEqual(topic.data["title"], "New topic")

        first, second = Topic.objects.all()
        self.assertEqual(first.title, "New topic")
        self.assertEqual(second.title, "Existing topic")

    def test_reply(self):
        self.client.force_login(self.other)
        data = {"text": "Second post"}

        self.client.post("/api/topics/1/posts/", data, format="json")

        topic = Topic.objects.last()
        self.assertEqual(topic.post_count, 2)

        first, second = topic.posts.all()
        self.assertEqual(second.text, "Second post")
        self.assertEqual(second.author, "other")

    def test_edit(self):
        data = {"text": "Edited post"}

        response = self.client.patch("/api/topics/1/posts/1/", data, format="json")
        self.assertEqual(response.data["text"], "Edited post")

    def test_edit_by_other(self):
        self.client.force_login(self.other)
        data = {"text": "Edited post"}

        response = self.client.put("/api/topics/1/posts/1/", data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_edit_by_admin(self):
        self.client.force_login(self.admin)
        data = {"text": "Edited post"}

        response = self.client.patch("/api/topics/1/posts/1/", data, format="json")
        self.assertEqual(response.data["text"], "Edited post")
        self.assertEqual(response.data["author"], "user")

    def test_record_cycle(self):
        Post.objects.bulk_create([Post(text=str(i), topic_id=1) for i in range(5)])

        record = Record.objects.create(topic_id=1, user_id=2)
        self.assertEqual(record.count, 0)

        self.client.get("/api/topics/1/posts/?page=1")
        record.refresh_from_db()
        self.assertEqual(record.count, 5)

        self.client.get("/api/topics/1/posts/?page=2")
        record.refresh_from_db()
        self.assertEqual(record.count, 6)

        self.client.get("/api/topics/1/posts/?page=1")
        record.refresh_from_db()
        self.assertEqual(record.count, 6)

    def test_no_np1q_on_post_list(self):
        Post.objects.bulk_create([Post(text=str(i), topic_id=1) for i in range(5)])

        with self.assertNumQueries(12):
            response = self.client.get("/api/topics/1/posts/")
        self.assertEqual(response.data["count"], 6)

    def test_no_np1q_on_topic_list(self):
        Topic.objects.bulk_create([Topic(title=str(i)) for i in range(5)])

        with self.assertNumQueries(5):
            response = self.client.get("/api/topics/")
        self.assertEqual(response.data["count"], 6)

    def test_throttle(self):
        self.client.force_login(self.admin)
        data = {"text": "Second post"}

        response = self.client.post("/api/topics/1/posts/", data, format="json")
        self.assertEqual(response.status_code, 201)

        response = self.client.post("/api/topics/1/posts/", data, format="json")
        self.assertEqual(response.status_code, 429)
        self.assertIn("15 seconds", response.data["detail"])

    def test_users(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 200)

    def test_delete_topic(self):
        response = self.client.delete("/api/topics/1/")
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.admin)
        response = self.client.delete("/api/topics/1/")
        self.assertEqual(response.status_code, 204)

        self.assertEqual(Topic.objects.count(), 0)

    def test_post_detail_uses_topic_for_prefilter(self):
        response = self.client.get("/api/topics/2/posts/1/")
        self.assertEqual(response.status_code, 404)

    def test_post_detail_context_info(self):
        topic = Topic.objects.create()
        Post.objects.bulk_create([Post(text=i, topic_id=1) for i in range(20)])
        Post.objects.bulk_create([Post(text=i, topic_id=2) for i in range(20)])

        with self.assertNumQueries(6):
            response = self.client.get("/api/topics/2/posts/28/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["context"]["index"], 7)
        self.assertEqual(response.data["context"]["page"], 2)


