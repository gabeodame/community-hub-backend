from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, response, status, views

from groups.models import Group, Membership
from groups.serializers import GroupSerializer, MembershipSerializer
from notifications.models import Notification
from notifications.utils import create_notification

User = get_user_model()


class GroupCreateView(generics.CreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        group = serializer.save(created_by=self.request.user)
        Membership.objects.create(
            user=self.request.user,
            group=group,
            role=Membership.Role.OWNER,
            status=Membership.Status.ACTIVE,
        )


class GroupJoinView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)

        if Membership.objects.filter(
            group=group, user=request.user, status=Membership.Status.ACTIVE
        ).exists():
            return response.Response({"detail": "Already a member."}, status=status.HTTP_200_OK)

        if group.join_policy == Group.JoinPolicy.INVITE:
            return response.Response(
                {"detail": "Invite required."}, status=status.HTTP_403_FORBIDDEN
            )

        status_value = (
            Membership.Status.ACTIVE
            if group.join_policy == Group.JoinPolicy.OPEN
            else Membership.Status.PENDING
        )
        membership, created = Membership.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={"status": status_value},
        )
        if not created:
            membership.status = status_value
            membership.save(update_fields=["status"])

        return response.Response(
            {"status": membership.status},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class GroupApproveView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id, user_id):
        group = get_object_or_404(Group, pk=group_id)
        is_moderator = Membership.objects.filter(
            group=group,
            user=request.user,
            role__in=[Membership.Role.OWNER, Membership.Role.MODERATOR],
            status=Membership.Status.ACTIVE,
        ).exists()
        if not is_moderator:
            return response.Response(
                {"detail": "You do not have permission to approve."},
                status=status.HTTP_403_FORBIDDEN,
            )
        member = get_object_or_404(Membership, group=group, user_id=user_id)

        if member.status == Membership.Status.ACTIVE:
            return response.Response({"detail": "Already active."}, status=status.HTTP_200_OK)

        member.status = Membership.Status.ACTIVE
        member.save(update_fields=["status"])
        if member.user_id != request.user.id:
            create_notification(
                recipient=member.user,
                actor=request.user,
                verb=Notification.Verb.GROUP_APPROVED,
                target=group,
                data={"group_id": group.id, "group_name": group.name},
            )
        return response.Response({"detail": "Approved."}, status=status.HTTP_200_OK)


class GroupMembersView(generics.ListAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=self.kwargs["group_id"])
        is_member = Membership.objects.filter(
            group=group, user=self.request.user, status=Membership.Status.ACTIVE
        ).exists()
        if group.visibility == Group.Visibility.PRIVATE and not is_member:
            return response.Response(
                {"detail": "You do not have access to members."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        group = get_object_or_404(Group, pk=self.kwargs["group_id"])
        return Membership.objects.filter(group=group, status=Membership.Status.ACTIVE).select_related(
            "user", "group"
        )
