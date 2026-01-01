from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification


def create_notification(recipient, verb, actor=None, target=None, data=None):
    if recipient is None:
        return None
    content_type = None
    object_id = None
    if target is not None:
        content_type = ContentType.objects.get_for_model(target.__class__)
        object_id = target.pk
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        content_type=content_type,
        object_id=object_id,
        data=data or {},
    )
