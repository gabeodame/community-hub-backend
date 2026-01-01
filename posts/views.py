from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, response, status
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.exceptions import PermissionDenied

from groups.models import Group, Membership
from notifications.models import Notification
from notifications.utils import create_notification
from posts.models import Comment, Post, Report
from posts.serializers import CommentSerializer, PostSerializer, ReportSerializer


def _is_group_member(user, group):
    if not user.is_authenticated:
        return False
    return Membership.objects.filter(
        group=group, user=user, status=Membership.Status.ACTIVE
    ).exists()


class PostPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class PostCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-created_at"


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    pagination_class = PostPageNumberPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = (
            Post.objects.select_related("author", "group")
            .filter(is_deleted=False)
            .order_by("-created_at")
        )
        user = self.request.user
        if user.is_authenticated:
            member_group_ids = Membership.objects.filter(
                user=user, status=Membership.Status.ACTIVE
            ).values_list("group_id", flat=True)
            return queryset.filter(
                Q(group__isnull=True)
                | Q(group__visibility=Group.Visibility.PUBLIC)
                | Q(group_id__in=member_group_ids)
            )
        return queryset.filter(Q(group__isnull=True) | Q(group__visibility=Group.Visibility.PUBLIC))

    def perform_create(self, serializer):
        group = serializer.validated_data.get("group")
        if group and not _is_group_member(self.request.user, group):
            raise PermissionDenied("You must be a group member to post.")
        serializer.save(author=self.request.user)

    def get_pagination_class(self):
        pagination = self.request.query_params.get("pagination")
        if pagination and pagination.lower() in {"cursor", "c"}:
            return PostCursorPagination
        return super().get_pagination_class()


class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PostPageNumberPagination

    def get_queryset(self):
        queryset = (
            Post.objects.select_related("author", "group")
            .filter(is_deleted=False)
            .order_by("-created_at")
        )
        user = self.request.user
        member_group_ids = []
        if user.is_authenticated:
            member_group_ids = Membership.objects.filter(
                user=user, status=Membership.Status.ACTIVE
            ).values_list("group_id", flat=True)
        return queryset.filter(
            author_id=self.kwargs["user_id"]
        ).filter(
            Q(group__isnull=True)
            | Q(group__visibility=Group.Visibility.PUBLIC)
            | Q(group_id__in=member_group_ids)
        )

    def get_pagination_class(self):
        pagination = self.request.query_params.get("pagination")
        if pagination and pagination.lower() in {"cursor", "c"}:
            return PostCursorPagination
        return super().get_pagination_class()


class GroupPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PostPageNumberPagination

    def list(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=self.kwargs["group_id"])
        if group.visibility == Group.Visibility.PRIVATE and not _is_group_member(
            request.user, group
        ):
            return response.Response(
                {"detail": "You do not have access to this group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Post.objects.filter(group_id=self.kwargs["group_id"], is_deleted=False)
            .select_related("author", "group")
            .order_by("-created_at")
        )

    def get_pagination_class(self):
        pagination = self.request.query_params.get("pagination")
        if pagination and pagination.lower() in {"cursor", "c"}:
            return PostCursorPagination
        return super().get_pagination_class()


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def _get_post(self):
        return get_object_or_404(Post, pk=self.kwargs["post_id"], is_deleted=False)

    def _ensure_can_view_post(self, request, post):
        if post.group and post.group.visibility == Group.Visibility.PRIVATE:
            if not _is_group_member(request.user, post.group):
                return response.Response(
                    {"detail": "You do not have access to this post."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return None

    def list(self, request, *args, **kwargs):
        post = self._get_post()
        denied = self._ensure_can_view_post(request, post)
        if denied:
            return denied
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Comment.objects.filter(post_id=self.kwargs["post_id"], is_deleted=False)
            .select_related("author", "post")
            .order_by("created_at")
        )

    def create(self, request, *args, **kwargs):
        post = self._get_post()
        denied = self._ensure_can_view_post(request, post)
        if denied:
            return denied
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        post = self._get_post()
        parent = serializer.validated_data.get("parent")
        if parent and parent.post_id != post.id:
            raise PermissionDenied("Parent comment must belong to the same post.")
        comment = serializer.save(author=self.request.user, post=post)
        if parent and parent.author_id != self.request.user.id:
            create_notification(
                recipient=parent.author,
                actor=self.request.user,
                verb=Notification.Verb.REPLIED,
                target=comment,
                data={"post_id": post.id},
            )
        elif post.author_id != self.request.user.id:
            create_notification(
                recipient=post.author,
                actor=self.request.user,
                verb=Notification.Verb.COMMENTED,
                target=comment,
                data={"post_id": post.id},
            )


class PostDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Post.objects.select_related("author", "group").filter(is_deleted=False)
    lookup_field = "id"
    lookup_url_kwarg = "post_id"

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id and not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to delete this post.")
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["is_deleted", "deleted_at"])


class CommentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.select_related("author", "post").filter(is_deleted=False)

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id and not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to delete this comment.")
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["is_deleted", "deleted_at"])


class ReportCreateView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
