import pytest
from django.contrib.auth import get_user_model

from tests.utils import access_token_for_user

from groups.models import Group, Membership

User = get_user_model()


def _login(api_client, username, password):
    user = User.objects.get(username=username)
    return access_token_for_user(user)


@pytest.mark.django_db
def test_create_group_creates_owner_membership(api_client):
    User.objects.create_user(username="owner", password="S3curePassw0rd!")
    token = _login(api_client, "owner", "S3curePassw0rd!")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.post(
        "/api/v1/groups/",
        {"name": "My Group", "description": "Test", "visibility": "public"},
        format="json",
    )

    assert response.status_code == 201
    group_id = response.json()["id"]
    assert Membership.objects.filter(
        group_id=group_id, user__username="owner", role=Membership.Role.OWNER
    ).exists()


@pytest.mark.django_db
def test_join_open_group_active(api_client):
    owner = User.objects.create_user(username="owner2", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Open Group",
        slug="open-group",
        created_by=owner,
        join_policy=Group.JoinPolicy.OPEN,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)

    User.objects.create_user(username="member", password="S3curePassw0rd!")
    token = _login(api_client, "member", "S3curePassw0rd!")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.post(f"/api/v1/groups/{group.id}/join/")

    assert response.status_code == 201
    assert response.json()["status"] == Membership.Status.ACTIVE


@pytest.mark.django_db
def test_join_request_group_pending_and_approve(api_client):
    owner = User.objects.create_user(username="owner3", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Request Group",
        slug="request-group",
        created_by=owner,
        join_policy=Group.JoinPolicy.REQUEST,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)

    pending_user = User.objects.create_user(username="pending", password="S3curePassw0rd!")
    token_pending = _login(api_client, "pending", "S3curePassw0rd!")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pending}")
    response = api_client.post(f"/api/v1/groups/{group.id}/join/")
    assert response.status_code == 201
    assert response.json()["status"] == Membership.Status.PENDING

    token_owner = _login(api_client, "owner3", "S3curePassw0rd!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_owner}")
    response = api_client.post(
        f"/api/v1/groups/{group.id}/members/{pending_user.id}/approve/"
    )
    assert response.status_code == 200
    assert Membership.objects.filter(
        group=group, user__username="pending", status=Membership.Status.ACTIVE
    ).exists()


@pytest.mark.django_db
def test_join_invite_group_forbidden(api_client):
    owner = User.objects.create_user(username="owner4", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Invite Group",
        slug="invite-group",
        created_by=owner,
        join_policy=Group.JoinPolicy.INVITE,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)

    User.objects.create_user(username="invited", password="S3curePassw0rd!")
    token = _login(api_client, "invited", "S3curePassw0rd!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.post(f"/api/v1/groups/{group.id}/join/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_private_group_members_requires_membership(api_client):
    owner = User.objects.create_user(username="owner5", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Private Group",
        slug="private-group",
        created_by=owner,
        visibility=Group.Visibility.PRIVATE,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)

    User.objects.create_user(username="outsider", password="S3curePassw0rd!")
    token = _login(api_client, "outsider", "S3curePassw0rd!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.get(f"/api/v1/groups/{group.id}/members/")

    assert response.status_code == 403
