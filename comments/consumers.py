from channels.generic.websocket import AsyncJsonWebsocketConsumer


class CommentsConsumer(AsyncJsonWebsocketConsumer):
    """Deliver new comment events to connected clients."""

    group_name = "comments"

    async def connect(self) -> None:
        """Join the shared comments group."""
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:  # ruff: ignore[unused-method-argument]
        """Leave the shared comments group."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def comment_created(self, event: dict) -> None:
        """Send a newly created comment to the client."""
        await self.send_json(event["comment"])
