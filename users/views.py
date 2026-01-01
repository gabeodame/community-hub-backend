from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import generics, permissions, response, status, views
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from users.serializers import RegisterSerializer, UserMeSerializer
from users.throttles import LoginThrottle, RegisterThrottle, UserWriteThrottle


def _set_auth_cookies(resp, access, refresh=None):
    resp.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        access,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_COOKIE_PATH,
    )
    if refresh:
        resp.set_cookie(
            settings.JWT_REFRESH_COOKIE_NAME,
            refresh,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            path=settings.JWT_COOKIE_PATH,
        )


def _clear_auth_cookies(resp):
    resp.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME, path=settings.JWT_COOKIE_PATH)
    resp.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path=settings.JWT_COOKIE_PATH)
 

def _enforce_csrf(request):
    middleware = CsrfViewMiddleware(lambda req: None)
    reason = middleware.process_view(request._request, None, (), {})
    if reason:
        return response.Response(
            {"detail": f"CSRF Failed: {reason}"},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


class LoginView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        csrf_response = _enforce_csrf(request)
        if csrf_response:
            return csrf_response
        response_obj = super().post(request, *args, **kwargs)
        access = response_obj.data.get("access")
        refresh = response_obj.data.get("refresh")
        if access and refresh:
            _set_auth_cookies(response_obj, access, refresh)
            get_token(request)
            response_obj.data = {"detail": "Login successful."}
        return response_obj


class TokenRefreshCookieView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        csrf_response = _enforce_csrf(request)
        if csrf_response:
            return csrf_response
        refresh = request.data.get("refresh") or request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE_NAME
        )
        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)
        access = serializer.validated_data.get("access")
        new_refresh = serializer.validated_data.get("refresh")
        resp = response.Response({"detail": "Token refreshed."}, status=status.HTTP_200_OK)
        _set_auth_cookies(resp, access, new_refresh)
        get_token(request)
        return resp


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        resp = response.Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
        _clear_auth_cookies(resp)
        return resp


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            if "username" in serializer.errors or "email" in serializer.errors:
                return response.Response(
                    {"detail": "Unable to register with provided credentials."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            error_key = None
            if "detail" in serializer.errors:
                error_key = "detail"
            elif "non_field_errors" in serializer.errors:
                error_key = "non_field_errors"

            if error_key:
                detail = serializer.errors[error_key]
                if isinstance(detail, list) and detail:
                    detail = detail[0]
                return response.Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserWriteThrottle]

    def get_object(self):
        return self.request.user
