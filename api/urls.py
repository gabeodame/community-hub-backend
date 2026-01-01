from django.urls import path
from users.views import CsrfView, LoginView, LogoutView, MeView, RegisterView, TokenRefreshCookieView
from core.views import HealthView, ReadinessView
from groups.views import GroupApproveView, GroupCreateView, GroupJoinView, GroupMembersView
from posts.views import (
    CommentDetailView,
    CommentListCreateView,
    GroupPostsView,
    PostDetailView,
    PostListCreateView,
    ReportCreateView,
    UserPostsView,
)
from notifications.views import (
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationUnreadCountView,
)
from profiles.views import MeProfileView
from social.views import BlockView, FollowView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("ready/", ReadinessView.as_view(), name="ready"),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/token/", LoginView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshCookieView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path("auth/csrf/", CsrfView.as_view(), name="auth_csrf"),
    path("users/me/", MeView.as_view(), name="users_me"),
    path("profiles/me/", MeProfileView.as_view(), name="profiles_me"),
    path("users/<int:user_id>/follow/", FollowView.as_view(), name="user_follow"),
    path("users/<int:user_id>/block/", BlockView.as_view(), name="user_block"),
    path("groups/", GroupCreateView.as_view(), name="group_create"),
    path("groups/<int:group_id>/join/", GroupJoinView.as_view(), name="group_join"),
    path("groups/<int:group_id>/members/", GroupMembersView.as_view(), name="group_members"),
    path(
        "groups/<int:group_id>/members/<int:user_id>/approve/",
        GroupApproveView.as_view(),
        name="group_member_approve",
    ),
    path("posts/", PostListCreateView.as_view(), name="post_list_create"),
    path("posts/<int:post_id>/", PostDetailView.as_view(), name="post_detail"),
    path("posts/<int:post_id>/comments/", CommentListCreateView.as_view(), name="comment_list"),
    path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment_detail"),
    path("reports/", ReportCreateView.as_view(), name="report_create"),
    path("notifications/", NotificationListView.as_view(), name="notifications_list"),
    path(
        "notifications/<int:pk>/read/",
        NotificationReadView.as_view(),
        name="notifications_read",
    ),
    path(
        "notifications/read-all/",
        NotificationReadAllView.as_view(),
        name="notifications_read_all",
    ),
    path(
        "notifications/unread-count/",
        NotificationUnreadCountView.as_view(),
        name="notifications_unread_count",
    ),
    path("groups/<int:group_id>/posts/", GroupPostsView.as_view(), name="group_posts"),
    path("users/<int:user_id>/posts/", UserPostsView.as_view(), name="user_posts"),
]
