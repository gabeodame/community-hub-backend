import pytest
from django.contrib.auth import get_user_model

from tests.utils import access_token_for_user

from profiles.models import Profile
from social.models import Block, Follow

User = get_user_model()


def _login(api_client, username, password):
    user = User.objects.get(username=username)
    return access_token_for_user(user)


@pytest.mark.django_db
def test_profile_auto_created(api_client):
    user = User.objects.create_user(username="puser", password="S3curePassw0rd!")
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_profile_update(api_client):
    User.objects.create_user(username="puser2", password="S3curePassw0rd!")
    token = _login(api_client, "puser2", "S3curePassw0rd!")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.patch(
        "/api/v1/profiles/me/",
        {"bio": "Hello", "is_private": True},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["bio"] == "Hello"
    assert response.json()["is_private"] is True


@pytest.mark.django_db
def test_follow_unfollow(api_client):
    User.objects.create_user(username="follower", password="S3curePassw0rd!")
    target = User.objects.create_user(username="target", password="S3curePassw0rd!")
    token = _login(api_client, "follower", "S3curePassw0rd!")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.post(f"/api/v1/users/{target.id}/follow/")
    assert response.status_code == 201
    assert Follow.objects.filter(follower__username="follower", following=target).exists()

    response = api_client.post(f"/api/v1/users/{target.id}/follow/")
    assert response.status_code == 200

    response = api_client.delete(f"/api/v1/users/{target.id}/follow/")
    assert response.status_code == 204
    assert not Follow.objects.filter(follower__username="follower", following=target).exists()


@pytest.mark.django_db
def test_cannot_follow_self(api_client):
    user = User.objects.create_user(username="selfie", password="S3curePassw0rd!")
    token = _login(api_client, "selfie", "S3curePassw0rd!")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.post(f"/api/v1/users/{user.id}/follow/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_block_prevents_follow(api_client):
    blocker = User.objects.create_user(username="blocker", password="S3curePassw0rd!")
    blocked = User.objects.create_user(username="blocked", password="S3curePassw0rd!")

    token_blocker = _login(api_client, "blocker", "S3curePassw0rd!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_blocker}")
    response = api_client.post(f"/api/v1/users/{blocked.id}/block/")
    assert response.status_code == 201
    assert Block.objects.filter(blocker=blocker, blocked=blocked).exists()

    token_blocked = _login(api_client, "blocked", "S3curePassw0rd!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_blocked}")
    response = api_client.post(f"/api/v1/users/{blocker.id}/follow/")
    assert response.status_code == 403
