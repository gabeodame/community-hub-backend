from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def access_token_for_user(user):
    """Return a short-lived access token for the given user without API calls."""
    return str(RefreshToken.for_user(user).access_token)


def authenticate_client(api_client, user):
    """Attach auth + CSRF cookies for cookie-based JWT authentication."""
    token = access_token_for_user(user)
    api_client.cookies[settings.JWT_ACCESS_COOKIE_NAME] = token
    csrf_token = set_csrf_cookie(api_client)
    return token


def set_csrf_cookie(api_client):
    """Fetch and attach a CSRF cookie + header for unsafe requests."""
    csrf_response = api_client.get("/api/v1/auth/csrf/")
    csrf_token = csrf_response.cookies.get(settings.CSRF_COOKIE_NAME).value
    api_client.credentials(HTTP_X_CSRFTOKEN=csrf_token)
    return csrf_token
