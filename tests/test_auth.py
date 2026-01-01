import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from tests.utils import authenticate_client, set_csrf_cookie

User = get_user_model()


@pytest.mark.django_db
def test_register_success(api_client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "S3curePassw0rd!",
        "display_name": "New User",
    }

    response = api_client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 201
    assert response.json()["username"] == "newuser"
    assert User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_register_duplicate_username_returns_generic_error(api_client):
    User.objects.create_user(username="dupuser", password="S3curePassw0rd!")

    payload = {
        "username": "dupuser",
        "password": "S3curePassw0rd!",
        "display_name": "Dup User",
    }

    response = api_client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unable to register with provided credentials."


@pytest.mark.django_db
def test_register_password_too_short(api_client):
    payload = {
        "username": "shortpass",
        "password": "short",
    }

    response = api_client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 400
    assert "password" in response.json()


@pytest.mark.django_db
def test_login_success(api_client):
    User.objects.create_user(username="loginuser", password="S3curePassw0rd!")

    payload = {
        "username": "loginuser",
        "password": "S3curePassw0rd!",
    }

    set_csrf_cookie(api_client)
    response = api_client.post("/api/v1/auth/token/", payload, format="json")

    assert response.status_code == 200
    assert response.json()["detail"] == "Login successful."
    assert settings.JWT_ACCESS_COOKIE_NAME in response.cookies
    assert settings.JWT_REFRESH_COOKIE_NAME in response.cookies


@pytest.mark.django_db
def test_login_failure(api_client):
    User.objects.create_user(username="loginfail", password="S3curePassw0rd!")

    payload = {
        "username": "loginfail",
        "password": "wrongpassword",
    }

    set_csrf_cookie(api_client)
    response = api_client.post("/api/v1/auth/token/", payload, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_refresh_requires_csrf(api_client):
    User.objects.create_user(username="refreshuser", password="S3curePassw0rd!")
    set_csrf_cookie(api_client)
    api_client.post(
        "/api/v1/auth/token/",
        {"username": "refreshuser", "password": "S3curePassw0rd!"},
        format="json",
    )

    api_client.credentials()
    response = api_client.post("/api/v1/auth/token/refresh/", {}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_logout_requires_csrf(api_client):
    User.objects.create_user(username="logoutuser", password="S3curePassw0rd!")
    set_csrf_cookie(api_client)
    api_client.post(
        "/api/v1/auth/token/",
        {"username": "logoutuser", "password": "S3curePassw0rd!"},
        format="json",
    )

    api_client.credentials()
    response = api_client.post("/api/v1/auth/logout/", {}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_me_requires_auth(api_client):
    response = api_client.get("/api/v1/users/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_update_display_name(api_client):
    User.objects.create_user(username="meuser", password="S3curePassw0rd!")
    user = User.objects.get(username="meuser")
    authenticate_client(api_client, user)
    response = api_client.patch("/api/v1/users/me/", {"display_name": "Updated"}, format="json")

    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated"
