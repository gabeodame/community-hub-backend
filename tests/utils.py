from rest_framework_simplejwt.tokens import RefreshToken


def access_token_for_user(user):
    """Return a short-lived access token for the given user without API calls."""
    return str(RefreshToken.for_user(user).access_token)
