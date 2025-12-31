from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import HealthView
from profiles.views import MeProfileView
from social.views import BlockView, FollowView
from users.views import LoginView, MeView, RegisterView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/token/", LoginView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/me/", MeView.as_view(), name="users_me"),
    path("profiles/me/", MeProfileView.as_view(), name="profiles_me"),
    path("users/<int:user_id>/follow/", FollowView.as_view(), name="user_follow"),
    path("users/<int:user_id>/block/", BlockView.as_view(), name="user_block"),
]
