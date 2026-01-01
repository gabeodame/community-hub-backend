import pytest
from django.contrib.auth import get_user_model

from groups.models import Group, Membership
from notifications.models import Notification
from posts.models import Comment, Post
from tests.utils import authenticate_client

User = get_user_model()


@pytest.mark.django_db
def test_follow_creates_notification(api_client):
    follower = User.objects.create_user(username="follower", password="S3curePassw0rd!")
    target = User.objects.create_user(username="target", password="S3curePassw0rd!")
    authenticate_client(api_client, follower)
    response = api_client.post(f"/api/v1/users/{target.id}/follow/")
    assert response.status_code == 201

    assert Notification.objects.filter(
        recipient=target, verb=Notification.Verb.FOLLOWED
    ).exists()


@pytest.mark.django_db
def test_group_approval_notification(api_client):
    owner = User.objects.create_user(username="owner", password="S3curePassw0rd!")
    pending = User.objects.create_user(username="pending", password="S3curePassw0rd!")
    group = Group.objects.create(
        name="Notify Group",
        slug="notify-group",
        created_by=owner,
        join_policy=Group.JoinPolicy.REQUEST,
    )
    Membership.objects.create(user=owner, group=group, role=Membership.Role.OWNER)

    authenticate_client(api_client, pending)
    response = api_client.post(f"/api/v1/groups/{group.id}/join/")
    assert response.status_code == 201

    authenticate_client(api_client, owner)
    response = api_client.post(f"/api/v1/groups/{group.id}/members/{pending.id}/approve/")
    assert response.status_code == 200

    assert Notification.objects.filter(
        recipient=pending, verb=Notification.Verb.GROUP_APPROVED
    ).exists()


@pytest.mark.django_db
def test_comment_and_reply_notifications(api_client):
    author = User.objects.create_user(username="author", password="S3curePassw0rd!")
    commenter = User.objects.create_user(username="commenter", password="S3curePassw0rd!")
    replier = User.objects.create_user(username="replier", password="S3curePassw0rd!")

    post = Post.objects.create(author=author, content="A post")

    authenticate_client(api_client, commenter)
    response = api_client.post(
        f"/api/v1/posts/{post.id}/comments/",
        {"content": "First"},
        format="json",
    )
    assert response.status_code == 201
    parent_id = response.json()["id"]

    assert Notification.objects.filter(
        recipient=author, verb=Notification.Verb.COMMENTED
    ).exists()

    authenticate_client(api_client, replier)
    response = api_client.post(
        f"/api/v1/posts/{post.id}/comments/",
        {"content": "Reply", "parent": parent_id},
        format="json",
    )
    assert response.status_code == 201

    parent_comment = Comment.objects.get(pk=parent_id)
    assert Notification.objects.filter(
        recipient=parent_comment.author, verb=Notification.Verb.REPLIED
    ).exists()


@pytest.mark.django_db
def test_notifications_list_and_mark_read(api_client):
    actor = User.objects.create_user(username="actor", password="S3curePassw0rd!")
    recipient = User.objects.create_user(username="recipient", password="S3curePassw0rd!")
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=Notification.Verb.FOLLOWED,
    )

    authenticate_client(api_client, recipient)

    response = api_client.get("/api/v1/notifications/")
    assert response.status_code == 200
    notification_id = response.json()["results"][0]["id"]

    response = api_client.patch(f"/api/v1/notifications/{notification_id}/read/")
    assert response.status_code == 200
    assert response.json()["is_read"] is True


@pytest.mark.django_db
def test_notifications_unread_filter_and_read_all(api_client):
    actor = User.objects.create_user(username="actor2", password="S3curePassw0rd!")
    recipient = User.objects.create_user(username="recipient2", password="S3curePassw0rd!")
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=Notification.Verb.FOLLOWED,
        is_read=True,
    )
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=Notification.Verb.FOLLOWED,
        is_read=False,
    )

    authenticate_client(api_client, recipient)

    response = api_client.get("/api/v1/notifications/?unread=1")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1

    response = api_client.post("/api/v1/notifications/read-all/")
    assert response.status_code == 200
    assert response.json()["updated"] == 1

    response = api_client.get("/api/v1/notifications/unread-count/")
    assert response.status_code == 200
    assert response.json()["unread"] == 0


@pytest.mark.django_db
def test_notifications_cursor_pagination(api_client):
    actor = User.objects.create_user(username="actor3", password="S3curePassw0rd!")
    recipient = User.objects.create_user(username="recipient3", password="S3curePassw0rd!")
    for _ in range(3):
        Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb=Notification.Verb.FOLLOWED,
        )

    authenticate_client(api_client, recipient)

    response = api_client.get("/api/v1/notifications/?pagination=cursor")
    assert response.status_code == 200
    assert "results" in response.json()
