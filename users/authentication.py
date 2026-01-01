from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
        if not raw_token:
            return None

        try:
            validated = AccessToken(raw_token)
        except Exception as exc:  # pragma: no cover - token parsing is library controlled
            raise AuthenticationFailed("Invalid token.") from exc

        user_id = validated.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Invalid token.")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("User not found.") from exc

        if not user.is_active:
            raise AuthenticationFailed("User inactive.")

        if request.method not in SAFE_METHODS:
            self._enforce_csrf(request)

        return (user, validated)

    def _enforce_csrf(self, request):
        request._request._dont_enforce_csrf_checks = False
        middleware = CsrfViewMiddleware(lambda req: None)
        reason = middleware.process_view(request._request, None, (), {})
        if reason:
            raise PermissionDenied(f"CSRF Failed: {reason}")

    def authenticate_header(self, request):
        return "Bearer"
