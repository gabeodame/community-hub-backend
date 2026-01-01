import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from groups.models import Group, Membership
from posts.models import Comment, Post, Report
from tests.utils import authenticate_client

User = get_user_model()


@pytest.mark.django_db
def test_create_post_and_comment(api_client):
    user = User.objects.create_user(username="author", password="S3curePassw0rd!")
    authenticate_client(api_client, user)

    response = api_client.post("/api/v1/posts/", {"content": "Hello world"}, format="json")
    assert response.status_code == 201
    post_id = response.json()["id"]

    response = api_client.post(
        f"/api/v1/posts/{post_id}/comments/",
        {"content": "Nice post"},
        format="json",
    )
    assert response.status_code == 201
    assert Comment.objects.filter(post_id=post_id, author=user).exists()

    response = api_client.get(f"/api/v1/posts/{post_id}/comments/")
    assert response.status_code == 200
    assert response.json()[0]["content"] == "Nice post"


@pytest.mark.django_db
def test_group_post_requires_membership(api_client):
    owner = User.objects.create_user(username="owner", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Private Group",
        slug="private-group",
        created_by=owner,
        visibility=Group.Visibility.PRIVATE,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)

    outsider = User.objects.create_user(username="outsider", password="S3curePassw0rd!")
    authenticate_client(api_client, outsider)
    response = api_client.post(
        "/api/v1/posts/",
        {"content": "Sneaky post", "group": group.id},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_private_group_posts_require_membership(api_client):
    owner = User.objects.create_user(username="owner2", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Private Feed",
        slug="private-feed",
        created_by=owner,
        visibility=Group.Visibility.PRIVATE,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)
    Post.objects.create(author=owner, group=group, content="Group post")

    response = api_client.get(f"/api/v1/groups/{group.id}/posts/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_private_group_comments_require_membership(api_client):
    owner = User.objects.create_user(username="owner3", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Private Comments",
        slug="private-comments",
        created_by=owner,
        visibility=Group.Visibility.PRIVATE,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)
    post = Post.objects.create(author=owner, group=group, content="Private post")

    response = api_client.get(f"/api/v1/posts/{post.id}/comments/")
    assert response.status_code == 403

    outsider = User.objects.create_user(username="outsider2", password="S3curePassw0rd!")
    authed_client = APIClient()
    authenticate_client(authed_client, outsider)
    response = authed_client.post(
        f"/api/v1/posts/{post.id}/comments/",
        {"content": "Nope"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_soft_delete_post_hides_from_lists(api_client):
    user = User.objects.create_user(username="deleter", password="S3curePassw0rd!")
    authenticate_client(api_client, user)
    response = api_client.post("/api/v1/posts/", {"content": "Temporary"}, format="json")
    post_id = response.json()["id"]

    response = api_client.delete(f"/api/v1/posts/{post_id}/")
    assert response.status_code == 204

    response = api_client.get("/api/v1/posts/")
    assert response.status_code == 200
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_report_post_and_comment(api_client):
    user = User.objects.create_user(username="reporter", password="S3curePassw0rd!")
    authenticate_client(api_client, user)
    post = Post.objects.create(author=user, content="Reportable")
    comment = Comment.objects.create(author=user, post=post, content="Also reportable")

    response = api_client.post(
        "/api/v1/reports/",
        {"target_type": "post", "target_id": post.id, "reason": "spam"},
        format="json",
    )
    assert response.status_code == 201
    assert Report.objects.filter(reporter=user).count() == 1

    response = api_client.post(
        "/api/v1/reports/",
        {"target_type": "comment", "target_id": comment.id, "reason": "other"},
        format="json",
    )
    assert response.status_code == 201
    assert Report.objects.filter(reporter=user).count() == 2


@pytest.mark.django_db
def test_posts_cursor_pagination(api_client):
    user = User.objects.create_user(username="pager", password="S3curePassw0rd!")
    for i in range(3):
        Post.objects.create(author=user, content=f"Post {i}")

    response = api_client.get("/api/v1/posts/?pagination=cursor")
    assert response.status_code == 200
    assert "results" in response.json()
