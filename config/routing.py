from django.urls import path

from comments.consumers import CommentsConsumer

websocket_urlpatterns = [
    path("ws/comments/", CommentsConsumer.as_asgi(), name="websockets"),  # pyrefly: ignore[no-matching-overload]
]
