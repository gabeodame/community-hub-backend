import pytest
from django.contrib.auth import get_user_model

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

    response = api_client.post("/api/v1/auth/token/", payload, format="json")

    assert response.status_code == 200
    assert "access" in response.json()
    assert "refresh" in response.json()


@pytest.mark.django_db
def test_login_failure(api_client):
    User.objects.create_user(username="loginfail", password="S3curePassw0rd!")

    payload = {
        "username": "loginfail",
        "password": "wrongpassword",
    }

    response = api_client.post("/api/v1/auth/token/", payload, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_requires_auth(api_client):
    response = api_client.get("/api/v1/users/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_update_display_name(api_client):
    User.objects.create_user(username="meuser", password="S3curePassw0rd!")

    login_response = api_client.post(
        "/api/v1/auth/token/",
        {"username": "meuser", "password": "S3curePassw0rd!"},
        format="json",
    )
    token = login_response.json()["access"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.patch("/api/v1/users/me/", {"display_name": "Updated"}, format="json")

    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated"
