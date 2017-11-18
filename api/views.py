import math

from django.db.models import Count
from django.utils import timezone
from rest_framework import generics, permissions

from api import models, serializers


class TopicList(generics.ListCreateAPIView):
    queryset = models.Topic.objects.all()

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_scope = "slow"
        return super().get_throttles()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.FirstPostSerializer
        return serializers.TopicSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.username)

    def list(self, request):
        response = super().list(request)
        self._append_seen_count_to_response(request, response)
        response.data["page_size"] = self.paginator.page_size
        return response

    def _append_seen_count_to_response(self, request, response):
        ids = {topic["id"] for topic in response.data["results"]}
        records = dict(request.user.record_set.filter(topic__in=ids).values_list("topic", "count"))
        for topic in response.data["results"]:
            topic["seen_count"] = records.get(topic["id"], 0)
            topic["page_size"] = self.paginator.page_size


class TopicDetail(generics.RetrieveDestroyAPIView):
    queryset = models.Topic.objects.all()
    serializer_class = serializers.TopicSerializer
    permission_classes = [permissions.IsAdminUser]


class PostList(generics.ListCreateAPIView):

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_scope = "slow"
        return super().get_throttles()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.ReplySerializer
        return serializers.PostListSerializer

    def get_queryset(self):
        topic_id = int(self.kwargs["topic_id"])
        return (models.Post.objects
            .filter(topic=topic_id)
            .select_related("topic")
            .order_by("timestamp")
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.username, timestamp=timezone.now(), topic_id=self.kwargs["topic_id"])

    def list(self, request, topic_id):
        response = super().list(request, topic_id)
        self._maybe_update_record(request, topic_id, response)
        self._add_topic_to_response(topic_id, response)
        self._enumerate_results(request, response)
        response.data["page_size"] = self.paginator.page_size
        return response

    def _maybe_update_record(self, request, topic_id, response):
        page = request.query_params.get("page", "1")
        count = min(self.paginator.page_size * int(page), response.data["count"])
        record = request.user.record_set.filter(topic_id=topic_id).first()
        if not record or count > record.count:
            request.user.record_set.update_or_create(topic_id=topic_id, defaults={"count": count})

    def _add_topic_to_response(self, topic_id, response):
        topic = models.Topic.objects.get(id=topic_id)
        response.data["topic"] = serializers.TopicSerializer(topic).data

    def _enumerate_results(self, request, response):
        for i, post in enumerate(response.data["results"], 1):
            post["index"] = (int(request.query_params.get("page", "1"))-1) * self.paginator.page_size + i


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.PostDetailSerializer

    def get_queryset(self):
        return models.Post.objects.filter(topic_id=self.kwargs["topic_id"])

    def get(self, request, topic_id, pk):
        response = super().get(request, topic_id, pk)
        obj = self.get_object()
        qs = self.get_queryset()
        index = list(qs).index(obj) + 1
        page = math.ceil(index/self.paginator.page_size)
        response.data["context"] = {"index": index, "page": page}
        return response


class UserList(generics.ListAPIView):
    queryset = models.User.objects.order_by("id")
    serializer_class = serializers.UserSerializer

    def list(self, request):
        response = super().list(request)
        for user in response.data["results"]:
            qs = models.Post.objects.filter(author=user["username"])
            user["post_count"] = len(qs)
        return response
