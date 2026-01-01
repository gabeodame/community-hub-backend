from rest_framework import generics, permissions, response, status, views
from rest_framework.pagination import CursorPagination, PageNumberPagination

from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-created_at"


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        unread = self.request.query_params.get("unread")
        if unread and unread.lower() in {"1", "true", "yes"}:
            queryset = queryset.filter(is_read=False)
        return queryset

    def get_pagination_class(self):
        pagination = self.request.query_params.get("pagination")
        if pagination and pagination.lower() in {"cursor", "c"}:
            return NotificationCursorPagination
        return super().get_pagination_class()


class NotificationReadView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.all()

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        if notification.recipient_id != request.user.id:
            return response.Response(
                {"detail": "You do not have access to this notification."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return response.Response(self.get_serializer(notification).data)


class NotificationReadAllView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return response.Response({"updated": updated}, status=status.HTTP_200_OK)


class NotificationUnreadCountView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return response.Response({"unread": count}, status=status.HTTP_200_OK)
