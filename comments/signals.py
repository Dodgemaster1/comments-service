from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from comments.models import CommentModel
from comments.services.text import TextService


@receiver(post_save, sender=CommentModel, weak=False)
def notify_comment_created(
    sender: type[CommentModel],
    instance: CommentModel,
    *,
    created: bool,
    **_kwargs: object,
) -> None:
    """Broadcast a newly committed comment to connected clients."""
    del sender
    if not created:
        return

    event = {
        "type": "comment.created",
        "comment": {
            "id": instance.id,
            "username": instance.user.username,
            "email": instance.user.email,
            "text": TextService.sanitize(instance.text),
            "homepage": instance.homepage,
        },
    }

    def send_event() -> None:
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)("comments", event)

    transaction.on_commit(send_event)
