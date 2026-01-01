from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, response, status, views

from social.models import Block, Follow
from notifications.models import Notification
from notifications.utils import create_notification

User = get_user_model()


class FollowView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        target = get_object_or_404(User, pk=user_id)
        if target == request.user:
            return response.Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Block.objects.filter(blocker=target, blocked=request.user).exists():
            return response.Response(
                {"detail": "Unable to follow this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if Block.objects.filter(blocker=request.user, blocked=target).exists():
            return response.Response(
                {"detail": "Unable to follow this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if created and target != request.user:
            create_notification(
                recipient=target,
                actor=request.user,
                verb=Notification.Verb.FOLLOWED,
                target=request.user,
            )
        return response.Response(
            {"detail": "Followed."},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, user_id):
        target = get_object_or_404(User, pk=user_id)
        Follow.objects.filter(follower=request.user, following=target).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class BlockView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        target = get_object_or_404(User, pk=user_id)
        if target == request.user:
            return response.Response(
                {"detail": "You cannot block yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Block.objects.get_or_create(blocker=request.user, blocked=target)
        Follow.objects.filter(follower=request.user, following=target).delete()
        Follow.objects.filter(follower=target, following=request.user).delete()
        return response.Response({"detail": "Blocked."}, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        target = get_object_or_404(User, pk=user_id)
        Block.objects.filter(blocker=request.user, blocked=target).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
